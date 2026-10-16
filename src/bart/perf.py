import json
import subprocess
import threading
import time
from contextlib import contextmanager
from datetime import datetime

import psutil

from .config import LOGS

LOG = LOGS / "perf.jsonl"


def gpu_memory_mb():
    command = ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=2)
        first_line = result.stdout.strip().splitlines()[0]
        return float(first_line)
    except (OSError, IndexError, ValueError, subprocess.TimeoutExpired):
        return None


class Sampler:
    def __init__(self, process, every, gpu):
        self.process = process
        self.every = every
        self.gpu = gpu
        self.peak_rss = process.memory_info().rss
        self.peak_gpu_mb = 0.0
        self.cpu_samples = []
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def run(self):
        psutil.cpu_percent(None)
        while not self.stop_event.wait(self.every):
            self.sample_once()

    def sample_once(self):
        try:
            rss = self.process.memory_info().rss
            if rss > self.peak_rss:
                self.peak_rss = rss
        except psutil.Error:
            pass

        self.cpu_samples.append(psutil.cpu_percent(None))

        if self.gpu:
            used_mb = gpu_memory_mb()
            if used_mb is not None and used_mb > self.peak_gpu_mb:
                self.peak_gpu_mb = used_mb

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.thread.join()

    def average_cpu(self):
        if len(self.cpu_samples) == 0:
            return None
        return round(sum(self.cpu_samples) / len(self.cpu_samples), 1)


def build_record(name, wall_s, cpu_s, sampler, meta):
    if wall_s > 0:
        effective_cores = round(cpu_s / wall_s, 2)
    else:
        effective_cores = None

    record = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "stage": name,
        "wall_s": round(wall_s, 3),
        "cpu_s": round(cpu_s, 3),
        "effective_cores": effective_cores,
        "peak_rss_gb": round(sampler.peak_rss / 1e9, 3),
        "avg_cpu_pct": sampler.average_cpu(),
    }
    if sampler.gpu:
        record["peak_gpu_mem_mb"] = sampler.peak_gpu_mb
    record.update(meta)
    return record


def print_record(record):
    parts = [
        f"[perf] {record['stage']}: {record['wall_s']:.2f}s",
        f"{record['effective_cores']} cores",
        f"peak RAM {record['peak_rss_gb']} GB",
    ]
    if record["avg_cpu_pct"] is not None:
        parts.append(f"CPU {record['avg_cpu_pct']}%")
    if "peak_gpu_mem_mb" in record:
        parts.append(f"GPU mem {record['peak_gpu_mem_mb']:.0f} MB")
    print(" | ".join(parts))


@contextmanager
def stage(name, sample_every=0.2, gpu=False, **meta):
    process = psutil.Process()
    sampler = Sampler(process, sample_every, gpu)

    cpu_before = process.cpu_times()
    wall_before = time.perf_counter()
    sampler.start()
    try:
        yield
    finally:
        sampler.stop()
        wall_s = time.perf_counter() - wall_before
        cpu_after = process.cpu_times()
        user_s = cpu_after.user - cpu_before.user
        system_s = cpu_after.system - cpu_before.system
        cpu_s = user_s + system_s

        record = build_record(name, wall_s, cpu_s, sampler, meta)
        with open(LOG, "a") as log_file:
            log_file.write(json.dumps(record) + "\n")
        print_record(record)
