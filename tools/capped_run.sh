#!/bin/bash
# Usage: tools/capped_run.sh <workdir> <logfile> <mcp|sculpt> <script> [args...]
# Starts ONE heavy python job as a detached transient systemd user service: MemoryMax=1500M, no swap, nice 10,
# 2 BLAS/OMP threads. Survives the calling shell. Appends "EXIT <code>" to the log. Unit name printed on stdout.
wd=$1; log=$2; kind=$3; shift 3
if [ "$kind" = mcp ]; then PY=$HOME/projects/unified-CAD-MCP/.venv/bin/python; PP=$HOME/projects/unified-CAD-MCP/src; else PY=$HOME/projects/venvs/scifi-sculpt/bin/python; PP=; fi
unit=capjob-$(date +%H%M%S)-$$
systemd-run --user --unit="$unit" --collect -q -p MemoryMax=1500M -p MemorySwapMax=0 --nice=10 \
  --working-directory="$wd" -E OMP_NUM_THREADS=2 -E OPENBLAS_NUM_THREADS=2 -E MKL_NUM_THREADS=2 -E PYTHONPATH="$PP" -E HOME="$HOME" \
  /bin/bash -c "$PY $* > '$log' 2>&1; echo EXIT \$? >> '$log'"
echo "$unit"
