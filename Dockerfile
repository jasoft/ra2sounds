FROM python:3.14-slim AS builder

# ---------- builder ----------
COPY server.py .

# ---------- runtime ----------
FROM python:3.14-slim
WORKDIR /opt/ra2sounds

# nginx（反向代理 + 静态托管）
RUN apt-get update && \
    apt-get install -y --no-install-recommends nginx && \
    rm -rf /var/lib/apt/lists/*

# 后端
COPY server.py .

# nginx 配置
COPY nginx.conf /etc/nginx/sites-available/default

# 静态文件（index.html / sounds.json / badges.js / sounds/）
COPY index.html .
COPY badges.js .
COPY sounds.json .
COPY sounds/ sounds/

# 数据目录
RUN mkdir -p /opt/ra2sounds/data

EXPOSE 80

# 启动 nginx + python 后端（双进程）
# DB_PATH 环境变量传入 SQLite 路径
CMD ["sh", "-c", "mkdir -p /opt/ra2sounds/data && nginx -g 'daemon off;' & python3 server.py --port 8000 --trust-proxy --db ${DB_PATH:-/opt/ra2sounds/data/notes.db}"]
