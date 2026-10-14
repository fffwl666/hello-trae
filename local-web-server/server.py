"""本地 HTTP 服务器 —— 基于标准库 http.server，无需第三方依赖。

用法：
    python server.py            # 默认端口 8000
    python server.py --port 9000

路由一览：
    GET  /             首页，读取同级目录的 index.html 返回（HTML）
    GET  /api/hello    返回 JSON：{"message": "Hello from API!", "time": "当前时间"}
    POST /api/echo     接收 JSON body，原样返回并追加 received 字段
    GET  /其他路径      若为存在的文件则返回文件内容，否则返回 404 JSON
"""

import argparse
import json
import mimetypes
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

# 以脚本所在目录为根目录，读取 index.html 和静态文件都基于此，避免硬编码绝对路径
BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"


class Handler(BaseHTTPRequestHandler):
    server_version = "LocalServer/1.0"

    # ------------------------------------------------------------------
    # 响应辅助方法
    # ------------------------------------------------------------------
    def _send(self, body: bytes, content_type: str, status: int = 200):
        """统一的响应发送：写入状态行、头部与正文。"""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, obj, status: int = 200):
        """返回 JSON 响应（UTF-8 编码，中文不转义）。"""
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(body, "application/json; charset=utf-8", status)

    def _send_html(self, html: str, status: int = 200):
        """返回 HTML 响应。"""
        self._send(html.encode("utf-8"), "text/html; charset=utf-8", status)

    # ------------------------------------------------------------------
    # GET 路由
    # ------------------------------------------------------------------
    def do_GET(self):
        path = urlparse(self.path).path

        # 路由 1：根路径 —— 读取同级目录的 index.html 作为首页返回
        if path in ("/", "/index.html"):
            if INDEX_FILE.is_file():
                self._send_html(INDEX_FILE.read_text(encoding="utf-8"))
            else:
                # index.html 缺失时的兜底页面，保证根路径仍可用
                self._send_html(
                    "<h1>我的第一个 Web 服务器</h1>"
                    "<p>未找到 index.html，请在同级目录创建该文件。</p>"
                )
            return

        # 路由 2：/api/hello —— 返回欢迎 JSON，含服务器当前时间
        if path == "/api/hello":
            self._send_json(
                {
                    "message": "Hello from API!",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            return

        # 路由 3：其他路径 —— 命中真实文件则返回内容，否则返回 404 JSON
        self._serve_static(path)

    # ------------------------------------------------------------------
    # POST 路由
    # ------------------------------------------------------------------
    def do_POST(self):
        path = urlparse(self.path).path

        # 路由 4：/api/echo —— 读取 JSON body，原样返回并追加 received 字段
        if path == "/api/echo":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""
                data = json.loads(raw.decode("utf-8")) if raw else {}
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
                self._send_json({"error": "请求体不是合法的 JSON"}, 400)
                return

            # body 是对象时直接合并；否则包一层，保证响应始终是 JSON 对象
            if isinstance(data, dict):
                result = {**data, "received": True}
            else:
                result = {"data": data, "received": True}
            self._send_json(result)
            return

        # 未定义的 POST 路径统一返回 404 JSON
        self._send_json({"error": "Not Found", "path": path, "method": "POST"}, 404)

    # ------------------------------------------------------------------
    # 静态文件
    # ------------------------------------------------------------------
    def _serve_static(self, path: str):
        """按路径返回文件内容；不存在或越界时返回 404 JSON。"""
        rel = unquote(path).lstrip("/")
        target = (BASE_DIR / rel).resolve()

        # 安全校验：只允许 BASE_DIR 及其子目录内的文件，防止路径穿越
        if (BASE_DIR == target or BASE_DIR in target.parents) and target.is_file():
            content_type, _ = mimetypes.guess_type(str(target))
            self._send(
                target.read_bytes(),
                content_type or "application/octet-stream",
            )
            return

        self._send_json({"error": "Not Found", "path": path}, 404)

    # ------------------------------------------------------------------
    # 日志：屏蔽默认格式，改为简洁输出
    # ------------------------------------------------------------------
    def log_message(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.address_string()} "
              f"{fmt % args}")

    def log_error(self, fmt, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 错误：{fmt % args}")


def main():
    parser = argparse.ArgumentParser(description="本地 HTTP 服务器")
    parser.add_argument(
        "--port", type=int, default=8000, help="监听端口（默认 8000）"
    )
    args = parser.parse_args()

    if not (1 <= args.port <= 65535):
        parser.error("端口需在 1-65535 之间")

    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    url = f"http://localhost:{args.port}"
    print(f"服务器运行在 {url}")
    print("按 Ctrl+C 停止服务器")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        # 路由：捕获 Ctrl+C，优雅关闭套接字并退出
        print("\n服务器已关闭")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
