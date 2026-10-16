"""Run notebooks in order, save each one in place, and draw a live status board in the terminal.

Usage: python scripts/run_notebooks.py notebooks/00_setup_and_machine.ipynb notebooks/01_ingest.ipynb ...

- every notebook starts with a fresh kernel (same as Restart + Run All)
- a notebook is saved in place only when every cell ran without an error
- on the first error (or a kernel that dies, e.g. out of memory) the run stops and the partly
  executed copy goes to outputs/logs/failed_<name>.ipynb
- kernel messages go to outputs/logs/run_all_<time>_kernel.log so they do not break the board
- the time each notebook took is kept in outputs/logs/run_all_times.json and used for the ETA next time
"""

import json
import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError, DeadKernelError

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "outputs" / "logs"
TIMES_FILE = LOGS / "run_all_times.json"

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
GREEN = "\x1b[32m"
RED = "\x1b[31m"
CYAN = "\x1b[36m"
YELLOW = "\x1b[33m"
CLEAR_LINE = "\x1b[2K"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"

FULL = "█"
EMPTY = "░"


def clock(seconds):
    if seconds is None:
        return "--:--"
    seconds = int(round(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    rest = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{rest:02d}"
    return f"{minutes:02d}:{rest:02d}"


def short_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f} s"
    return f"{int(seconds // 60)} min {int(seconds % 60):02d} s"


def bar(done, total, width):
    if total == 0:
        filled = width
    else:
        filled = int(width * done / total)
    return FULL * filled + EMPTY * (width - filled)


def visible_length(text):
    length = 0
    inside_escape = False
    for character in text:
        if character == "\x1b":
            inside_escape = True
        elif inside_escape:
            if character.isalpha():
                inside_escape = False
        else:
            length += 1
    return length


def fit(text, width):
    # cut a line to the terminal width without cutting an escape code, so lines never wrap
    if visible_length(text) <= width:
        return text
    result = ""
    length = 0
    inside_escape = False
    for character in text:
        if character == "\x1b":
            inside_escape = True
            result += character
        elif inside_escape:
            result += character
            if character.isalpha():
                inside_escape = False
        else:
            if length >= width - 1:
                break
            result += character
            length += 1
    return result + "…" + RESET


def cell_labels(notebook):
    # what to show while a code cell runs: its stage("...") name, otherwise the last markdown heading
    labels = []
    heading = ""
    for cell in notebook.cells:
        if cell.cell_type == "markdown":
            for line in cell.source.splitlines():
                if line.startswith("#"):
                    heading = line.lstrip("#").strip()
                    break
            continue
        label = heading
        marker = 'stage("'
        position = cell.source.find(marker)
        if position < 0:
            marker = 'stage(f"'
            position = cell.source.find(marker)
        if position >= 0:
            start = position + len(marker)
            end = cell.source.find('"', start)
            label = cell.source[start:end]
        labels.append(label)
    return labels


def load_times():
    if not TIMES_FILE.exists():
        return {}
    with open(TIMES_FILE) as handle:
        return json.load(handle)


def save_time(name, seconds):
    times = load_times()
    times[name] = round(seconds, 1)
    with open(TIMES_FILE, "w") as handle:
        json.dump(times, handle, indent=2, sort_keys=True)


class Board:
    def __init__(self, paths, started_label):
        self.lock = threading.Lock()
        self.started = time.perf_counter()
        self.started_label = started_label
        self.expected = load_times()
        self.rows = []
        for path in paths:
            notebook = nbformat.read(path, as_version=4)
            labels = cell_labels(notebook)
            self.rows.append({
                "path": path,
                "name": path.stem,
                "cells": len(labels),
                "labels": labels,
                "done": 0,
                "status": "waiting",
                "seconds": None,
                "began": None,
            })
        self.total_cells = 0
        for row in self.rows:
            self.total_cells += row["cells"]
        self.lines_drawn = 0
        self.interactive = sys.stdout.isatty()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.loop, daemon=True)

    # ---------- state changes ----------
    def begin(self, index):
        with self.lock:
            self.rows[index]["status"] = "running"
            self.rows[index]["began"] = time.perf_counter()
        if not self.interactive:
            print(f"start   {self.rows[index]['name']}", flush=True)

    def cell_done(self, index):
        with self.lock:
            self.rows[index]["done"] += 1

    def finish(self, index, ok):
        with self.lock:
            row = self.rows[index]
            row["seconds"] = time.perf_counter() - row["began"]
            if ok:
                row["status"] = "ok"
            else:
                row["status"] = "failed"
        if not self.interactive:
            print(f"{row['status']:<7} {row['name']:<30} {row['done']}/{row['cells']} cells  "
                  f"{short_time(row['seconds'])}", flush=True)

    # ---------- drawing ----------
    def remaining_estimate(self):
        remaining = 0.0
        known = True
        for row in self.rows:
            expected = self.expected.get(row["name"])
            if row["status"] == "waiting":
                if expected is None:
                    known = False
                else:
                    remaining += expected
            elif row["status"] == "running":
                elapsed = time.perf_counter() - row["began"]
                if expected is None:
                    known = False
                else:
                    remaining += max(expected - elapsed, 0.0)
        if known:
            return remaining
        # no history yet: scale elapsed time by the share of cells still to run
        done = 0
        for row in self.rows:
            done += row["done"]
        if done == 0:
            return None
        elapsed = time.perf_counter() - self.started
        return elapsed * (self.total_cells - done) / done

    def render(self):
        width = shutil.get_terminal_size((100, 24)).columns
        elapsed = time.perf_counter() - self.started
        rule = DIM + "─" * min(width, 96) + RESET
        name_width = 30

        lines = []
        lines.append(f"{BOLD} BART ridership · run all notebooks{RESET}   "
                     f"{DIM}started {self.started_label}   elapsed {clock(elapsed)}{RESET}")
        lines.append(rule)

        done_cells = 0
        current_label = ""
        for index, row in enumerate(self.rows):
            done_cells += row["done"]
            name = row["name"][:name_width].ljust(name_width)
            count = f"{row['done']:>3}/{row['cells']:<3} cells"
            expected = self.expected.get(row["name"])
            if row["status"] == "ok":
                lines.append(f"  {GREEN}✔{RESET} {name} {count}   {GREEN}{short_time(row['seconds'])}{RESET}")
            elif row["status"] == "failed":
                lines.append(f"  {RED}✘ {name} {count}   failed after {short_time(row['seconds'])}{RESET}")
            elif row["status"] == "running":
                running_for = time.perf_counter() - row["began"]
                label = ""
                if row["done"] < len(row["labels"]):
                    label = row["labels"][row["done"]]
                current_label = label
                lines.append(f"  {CYAN}▶ {name}{RESET} {CYAN}{bar(row['done'], row['cells'], 20)}{RESET} "
                             f"{row['done']:>3}/{row['cells']:<3}  {clock(running_for)}  {DIM}{label}{RESET}")
            else:
                hint = ""
                if expected is not None:
                    hint = f"~{short_time(expected)}"
                lines.append(f"  {DIM}· {name} {count}   {hint}{RESET}")

        lines.append(rule)
        percent = 0
        if self.total_cells > 0:
            percent = int(100 * done_cells / self.total_cells)
        left = self.remaining_estimate()
        left_text = "--:--"
        if left is not None:
            left_text = "~" + clock(left)
        lines.append(f"  {BOLD}overall{RESET} {YELLOW}{bar(done_cells, self.total_cells, 30)}{RESET} "
                     f"{done_cells:>3}/{self.total_cells} cells {percent:>3}%   "
                     f"elapsed {clock(elapsed)}   left {left_text}")
        if current_label != "":
            lines.append(f"  {DIM}now: {current_label}{RESET}")
        else:
            lines.append("")

        output = ""
        if self.lines_drawn > 0:
            output += f"\x1b[{self.lines_drawn}A"
        for line in lines:
            output += "\r" + CLEAR_LINE + fit(line, width) + "\n"
        sys.stdout.write(output)
        sys.stdout.flush()
        self.lines_drawn = len(lines)

    def loop(self):
        while not self.stop_event.wait(0.25):
            with self.lock:
                self.render()

    def start(self):
        if self.interactive:
            sys.stdout.write(HIDE_CURSOR)
            self.render()
            self.thread.start()

    def stop(self):
        if self.interactive:
            self.stop_event.set()
            self.thread.join()
            with self.lock:
                self.render()
            sys.stdout.write(SHOW_CURSOR)
            sys.stdout.flush()


def run_one(board, index, kernel_log):
    row = board.rows[index]
    path = row["path"]
    notebook = nbformat.read(path, as_version=4)

    def after_cell(cell, cell_index, execute_reply):
        if cell.cell_type == "code":
            board.cell_done(index)

    client = NotebookClient(
        notebook,
        kernel_name="python3",
        timeout=None,
        resources={"metadata": {"path": str(path.parent)}},
        on_cell_executed=after_cell,
    )

    board.begin(index)
    kernel_log.write(f"\n===== {path.name} {datetime.now():%H:%M:%S}\n")
    kernel_log.flush()
    try:
        # kernel stdout/stderr go to the log file instead of the terminal
        client.execute(stdout=kernel_log, stderr=kernel_log)
    except (CellExecutionError, DeadKernelError) as error:
        board.finish(index, False)
        failed_path = LOGS / f"failed_{path.name}"
        nbformat.write(notebook, failed_path)
        return False, failed_path, str(error)

    nbformat.write(notebook, path)
    board.finish(index, True)
    save_time(row["name"], row["seconds"])
    return True, None, ""


def main():
    paths = []
    for argument in sys.argv[1:]:
        paths.append(Path(argument).resolve())
    if len(paths) == 0:
        raise SystemExit("give the notebooks to run")

    stamp = datetime.now()
    kernel_log_path = LOGS / f"run_all_{stamp:%Y%m%d_%H%M%S}_kernel.log"
    board = Board(paths, f"{stamp:%H:%M:%S}")

    failure = None
    with open(kernel_log_path, "w") as kernel_log:
        board.start()
        try:
            for index in range(len(paths)):
                ok, failed_path, message = run_one(board, index, kernel_log)
                if not ok:
                    failure = (paths[index], failed_path, message)
                    break
        finally:
            board.stop()

    total = time.perf_counter() - board.started
    print()
    if failure is None:
        print(f"{GREEN}{BOLD}all {len(paths)} notebooks ran and were saved in {short_time(total)}{RESET}")
        print(f"{DIM}kernel log: {kernel_log_path.relative_to(ROOT)}{RESET}")
        return

    path, failed_path, message = failure
    print(f"{RED}{BOLD}stopped: {path.name} failed{RESET}  (notebooks after it were not run, {path.name} was not saved)")
    print(f"partly executed copy: {failed_path.relative_to(ROOT)}")
    print(f"kernel log          : {kernel_log_path.relative_to(ROOT)}")
    print()
    print(message[-2500:])
    sys.exit(1)


if __name__ == "__main__":
    main()
