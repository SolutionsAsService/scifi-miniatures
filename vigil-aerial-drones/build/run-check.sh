#!/bin/bash
cd /home/openclaw/projects/scifi-miniatures/vigil-aerial-drones
for i in $(seq 1 360); do
  avail=$(free -m | awk '/Mem:/{print $7}')
  busy=$(ps aux | grep -E 'vigil-aerial-drones.*build.py|source/build.py --reuse' | grep -v grep | wc -l)
  if [ "$avail" -gt 1500 ] && [ "$busy" -eq 0 ]; then break; fi
  sleep 15
done
echo "start $(date) avail=$avail" > build/check.log
PYTHONPATH=$HOME/projects/unified-CAD-MCP/src timeout 7200 $HOME/projects/unified-CAD-MCP/.venv/bin/python -u source/check.py >> build/check.log 2>&1
echo "EXIT $? $(date)" >> build/check.log
