#!/bin/bash
# Stage 1 - health-check.sh URL: is the service answering?
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: $0 URL" >&2
  exit 64
fi

URL=$1
NOW=$(date '+%Y-%m-%d %H:%M:%S')

# -f: an HTTP error (4xx/5xx) counts as a failure, --max-time: never hang
if curl -fsS --max-time 5 -o /dev/null "$URL" 2>/dev/null; then
  echo "[$NOW] UP $URL"
else
  echo "[$NOW] DOWN $URL"
  exit 2
fi
