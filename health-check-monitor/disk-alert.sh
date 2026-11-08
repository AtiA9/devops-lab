#!/bin/bash
# Stage 1 - disk-alert.sh: warn when the root disk is fuller than THRESHOLD percent.
set -euo pipefail

THRESHOLD=${THRESHOLD:-80}
USAGE=$(df --output=pcent / | tail -1 | tr -d ' %')
NOW=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$USAGE" -gt "$THRESHOLD" ]; then
  echo "[$NOW] WARNING: disk usage is ${USAGE}%"
  exit 1
fi
echo "[$NOW] OK: disk usage is ${USAGE}%"
