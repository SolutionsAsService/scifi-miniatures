#!/usr/bin/env bash
# Sculpt the named parts (each in its own capped process), then run the local gap/thin twin (lantern diag.py) on them.
# Usage: tools/capped_diag.sh <pkg dir> <log> part [part ...]
set -u
PKG="$1"; LOG="$2"; shift 2
PY=~/projects/venvs/scifi-sculpt/bin/python
DIAG=~/projects/scifi-miniatures/lantern-drones/source/diag.py
cd "$PKG" || exit 2
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
gate() { while [ "$(awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo)" -lt 2000 ]; do echo "waiting for memory" >> "$LOG"; sleep 60; done; }
run() { gate; systemd-run --user --scope -q -p MemoryMax=1500M -p MemorySwapMax=0 nice -n 10 "$PY" -u "$@" >> "$LOG" 2>&1; echo "EXIT $? $*" >> "$LOG"; }
: > "$LOG"
files=()
for p in "$@"; do run source/build.py "$p"; files+=("build/upright/$p.stl"); done
run "$DIAG" "${files[@]}"
echo "ALL DONE $(date)" >> "$LOG"
