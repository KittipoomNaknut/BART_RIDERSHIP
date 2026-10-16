#!/usr/bin/env bash
# Run every notebook in order (00 -> 12), save each one, and show a live status board.
# Same as Restart + Run All + Save for each notebook, one after another.
#
#   ./scripts/run_all.sh            run 00-12
#   ./scripts/run_all.sh 08 09      run only the notebooks whose names start with these numbers
#
# Cached results are kept: the Optuna study (outputs/models/m1_optuna.db) and the M3 quarters
# (outputs/models/m3_backtest/). Delete them first if you want the GPU work redone from scratch.
#
# Files written to outputs/logs/:
#   run_all_<time>_kernel.log   messages from the notebook kernels (kept off the screen)
#   run_all_times.json          how long each notebook took, used for the ETA next time
#   failed_<notebook>.ipynb     only when a notebook fails: the partly executed copy

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.venv/bin/python"

notebooks=()
if [ "$#" -eq 0 ]; then
    for path in "$ROOT"/notebooks/[0-9][0-9]_*.ipynb; do
        notebooks+=("$path")
    done
else
    for number in "$@"; do
        for path in "$ROOT"/notebooks/"$number"_*.ipynb; do
            if [ -e "$path" ]; then
                notebooks+=("$path")
            fi
        done
    done
fi

if [ "${#notebooks[@]}" -eq 0 ]; then
    echo "no notebooks matched: $*"
    exit 1
fi

cd "$ROOT"
exec "$PYTHON" scripts/run_notebooks.py "${notebooks[@]}"
