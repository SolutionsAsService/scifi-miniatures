#!/bin/bash
# wait until other heavy jobs leave enough memory, then run the reuse build
cd /home/openclaw/projects/scifi-miniatures/vigil-aerial-drones
for i in $(seq 1 360); do
  avail=$(free -m | awk '/Mem:/{print $7}')
  if [ "$avail" -gt 2600 ]; then break; fi
  sleep 15
done
echo "start $(date) avail=$avail" > build/build.log
timeout 3600 ~/projects/venvs/scifi-sculpt/bin/python -u source/build.py --reuse vl-02-sar-pod vl-04-cargo-pod >> build/build.log 2>&1
echo "EXIT $? $(date)" >> build/build.log
