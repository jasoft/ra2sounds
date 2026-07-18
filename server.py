#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RA2 音效库浏览器 · 轻量后端

功能：
  - 托管静态资源（index.html / sounds.json / badges.js / sounds/*.wav）
  - 提供「音效备注」的读写 API，备注持久化在本地 SQLite 数据库中
  - 仅允许局域网 / 本机（私有网段）客户端编辑备注；公网访问为只读

设计目标：零第三方依赖，仅使用 Python 标准库（http.server + sqlite3）。
与项目已有的离线 Python 工具链（build_sounds_json.py 等）保持一致。

运行：
    python3 server.py [--host HOST] [--port PORT] [--db PATH] [--trust-proxy]

默认监听 0.0.0.0:8000，绑定到所有网卡，便于同一局域网下的手机 / 其他电脑访问。
"""

import argparse
import datetime
import ipaddress
import json
import os
import re
import socket
import sqlite3
import urllib.parse
from typing import cast
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))

# 备注长度上限，避免单条备注无限膨胀
NOTE_MAX_LEN = 2000
# 请求体大小上限（字节），防御性限制
MAX_BODY = 64 * 1024
# file 键的合法字符集：音效文件名（如 bclovata.wav）
FILE_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,200}$")

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS notes (
    file        TEXT PRIMARY KEY,
    note        TEXT NOT NULL DEFAULT '',
    updated_at  TEXT NOT NULL
)
"""


def is_private_ip(ip):
    """判断是否为本机 / 局域网（私有网段）地址。

    覆盖：127.0.0.0/8、10.0.0.0/8、172.16.0.0/12、192.168.0.0/16、
    169.254.0.0/16（链路本地）、IPv6 ULA(fc00::/7) 与回环(::1) 等。
    这正是「仅局域网可编辑」所期望的放行范围。
    """
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


class Handler(SimpleHTTPRequestHandler):
    """静态资源 + /api/notes 备注接口。

    非 /api/ 开头的请求直接交给 SimpleHTTPRequestHandler 处理静态文件。
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    # ---------- 工具 ----------
    def _send_json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _db(self):
        conn = sqlite3.connect(cast("Server", self.server).db_path)
        conn.execute(CREATE_TABLE)
        return conn

    def client_ip(self):
        """获取客户端真实 IP。

        默认取 TCP 对端地址；当通过反向代理部署且开启 --trust-proxy 时，
        优先采用 X-Forwarded-For / X-Real-IP 头中的首个地址。
        """
        if getattr(cast("Server", self.server), "trust_proxy", False):
            xff = self.headers.get("X-Forwarded-For")
            if xff:
                return xff.split(",")[0].strip()
            xri = self.headers.get("X-Real-IP")
            if xri:
                return xri.strip()
        return self.client_address[0]

    # ---------- HTTP 方法路由 ----------
    def do_GET(self):
        if self.path.startswith("/api/"):
            return self._handle_get()
        return super().do_GET()

    def do_POST(self):
        if not self.path.startswith("/api/"):
            self.send_error(405)
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > MAX_BODY:
            return self._send_json(413, {"error": "请求体过大"})
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return self._send_json(400, {"error": "JSON 解析失败"})
        return self._handle_post(data)

    # ---------- API 实现 ----------
    def _handle_get(self):
        if not self.path.startswith("/api/notes"):
            return self._send_json(404, {"error": "未知接口"})
        editable = is_private_ip(self.client_ip())
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        files = qs.get("file")
        if not files:
            # 无 file 参数：返回所有「有内容」的备注文件清单，
            # 供前端在音效列表上标记哪些是已备注的。
            with self._db() as conn:
                rows = conn.execute(
                    "SELECT file FROM notes WHERE note IS NOT NULL AND note != ''"
                ).fetchall()
            return self._send_json(200, {
                "editable": editable,
                "files": [r[0] for r in rows],
            })
        file = files[0]
        with self._db() as conn:
            row = conn.execute(
                "SELECT note, updated_at FROM notes WHERE file=?", (file,)
            ).fetchone()
        payload = {
            "file": file,
            "note": row[0] if row else "",
            "updated_at": row[1] if row else None,
            "editable": editable,
        }
        return self._send_json(200, payload)

    def _handle_post(self, data):
        if not self.path.startswith("/api/notes"):
            return self._send_json(404, {"error": "未知接口"})
        if not is_private_ip(self.client_ip()):
            return self._send_json(
                403,
                {"editable": False,
                 "error": "只读模式：仅局域网（私有网段）客户端可编辑备注"},
            )
        file = data.get("file")
        note = data.get("note", "")
        if not isinstance(file, str) or not FILE_RE.match(file):
            return self._send_json(400, {"error": "file 非法（应为音效文件名）"})
        if not isinstance(note, str):
            return self._send_json(400, {"error": "note 必须为字符串"})
        note = note[:NOTE_MAX_LEN]
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        with self._db() as conn:
            conn.execute(
                "INSERT INTO notes(file, note, updated_at) VALUES(?,?,?) "
                "ON CONFLICT(file) DO UPDATE SET "
                "note=excluded.note, updated_at=excluded.updated_at",
                (file, note, ts),
            )
        return self._send_json(200, {"file": file, "note": note,
                                     "updated_at": ts, "editable": True})


class Server(ThreadingHTTPServer):
    """持有后端配置的 HTTPServer（db_path / trust_proxy）。"""

    db_path: str = "notes.db"
    trust_proxy: bool = False


def main():
    p = argparse.ArgumentParser(
        description="RA2 音效库浏览器后端（静态托管 + 备注 API）")
    p.add_argument("--host", default="0.0.0.0",
                   help="监听地址，默认 0.0.0.0（允许局域网访问）")
    p.add_argument("--port", type=int, default=8000, help="监听端口，默认 8000")
    p.add_argument("--db", default="notes.db", help="SQLite 数据库路径")
    p.add_argument("--trust-proxy", action="store_true",
                   help="信任 X-Forwarded-For / X-Real-IP 以获取真实客户端 IP")
    args = p.parse_args()

    httpd = Server((args.host, args.port), Handler)
    httpd.db_path = args.db
    httpd.trust_proxy = args.trust_proxy
    # 启动前确保表存在
    sqlite3.connect(args.db).execute(CREATE_TABLE).close()

    print("RA2 音效库后端已启动")
    print(f"  本机:   http://127.0.0.1:{args.port}/")
    try:
        lan = socket.gethostbyname(socket.gethostname())
        if lan != "127.0.0.1":
            print(f"  局域网: http://{lan}:{args.port}/")
    except Exception:
        pass
    print(f"  备注库: {os.path.abspath(args.db)}")
    print("  仅局域网 / 本机客户端可编辑备注；公网访问为只读。Ctrl+C 退出。")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
