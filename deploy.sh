#!/usr/bin/env bash
# deploy.sh — 一键部署 ra2sounds 到 docker.home
# 用法: bash deploy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTE="root@docker.home"
REMOTE_DIR="/opt/ra2sounds"
ARCHIVE="/tmp/ra2sounds-deploy.tar.gz"

echo "🚀 开始部署 ra2sounds 到 docker.home ..."

# 1. 打包（排除大目录）
echo "📦 打包项目..."
tar czf "$ARCHIVE" \
  --exclude=sounds \
  --exclude=node_modules \
  --exclude=__pycache__ \
  --exclude='*.pyc' \
  --exclude=.git \
  --exclude=.workbuddy \
  --exclude=notes.db \
  --exclude=extracted \
  --exclude=extracted_units \
  --exclude='*.log' \
  -C "$SCRIPT_DIR" \
  server.py index.html badges.js sounds.json README.md \
  Dockerfile docker-compose.yml nginx.conf

# 2. 上传
echo "📡 上传到 docker.home..."
scp "$ARCHIVE" "${REMOTE}:${REMOTE_DIR}/"

# 3. 远程部署
echo "🐳 远程构建并启动..."
ssh -o BatchMode=yes -o ConnectTimeout=5 "$REMOTE" "
  cd '$REMOTE_DIR' && \
  mkdir -p notes_db && \
  tar xzf ra2sounds-deploy.tar.gz && \
  rm -f ra2sounds-deploy.tar.gz && \
  docker compose down || true && \
  docker compose up -d --build && \
  docker compose ps
"

echo "✅ 部署完成！"
echo "   访问地址: http://rasounds.docker.home"
echo "   或:      http://docker.home:40402"
