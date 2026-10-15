#!/usr/bin/env bash
# Sculpt each part of a package in its own memory-capped process, then run the --reuse assembly (8 GB host rules:
# MemoryMax 1500M, no swap, nice 10, OMP 2 threads, one heavy process at a time; wait while MemAvailable < 2000 MB).
# Usage: tools/capped_parts.sh <pkg dir> <log> part [part ...]   (no parts: assembly only)
set -u
PKG="$1"; LOG="$2"; shift 2
PY=~/projects/venvs/scifi-sculpt/bin/python
cd "$PKG" || exit 2
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
gate() { while [ "$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)" -lt 2000 ]; do echo "waiting for memory" >> "$LOG"; sleep 60; done; }
run() { gate; systemd-run --user --scope -q -p MemoryMax=1500M -p MemorySwapMax=0 nice -n 10 "$PY" -u "$@" >> "$LOG" 2>&1; echo "EXIT $? $*" >> "$LOG"; }
: > "$LOG"
for p in "$@"; do run source/build.py "$p"; done
run source/build.py --reuse
grep -q -- '--images' source/build.py && run source/build.py --images
echo "ALL DONE $(date)" >> "$LOG"
