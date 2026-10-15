#!/bin/bash
cd /home/openclaw/projects/scifi-miniatures/vigil-aerial-drones
# wait for the running reuse build to end
while ps aux | grep 'source/build.py --reuse' | grep -v grep > /dev/null; do sleep 10; done
for i in $(seq 1 360); do
  avail=$(free -m | awk '/Mem:/{print $7}')
  if [ "$avail" -gt 1700 ]; then break; fi
  sleep 15
done
echo "start $(date) avail=$avail" > build/build.log
timeout 3600 ~/projects/venvs/scifi-sculpt/bin/python -u source/build.py --reuse base-50-tether launcher-roof-pad >> build/build.log 2>&1
echo "EXIT $? $(date)" >> build/build.log
bash build/run-check.sh
