#!/bin/bash
# runs once when the instance boots: install Docker and start TaskBoard
set -euo pipefail
dnf install -y docker
systemctl enable --now docker
docker volume create taskboard-data
docker run -d --name taskboard --restart unless-stopped \
  -p 5000:5000 -e DB_PATH=/data/taskboard.db -v taskboard-data:/data \
  ${image}
