"""待办事项 Web 应用 —— Flask + SQLite 实现。

项目结构（Flask 标准结构）：
    todo-web/
    ├── app.py              # 应用入口：Flask 路由 + SQLite 操作
    ├── todo.db             # SQLite 数据库（首次运行自动创建）
    ├── templates/
    │   ├── index.html      # 首页模板（展示待办列表 + 添加表单）
    │   ├── 404.html        # 404 错误页
    │   └── 500.html        # 500 错误页
    ├── static/
    │   ├── style.css       # 样式（卡片式布局）
    │   └── app.js          # 前端交互（复选框无刷新切换、JS 删除）
    └── README.md

运行：
    python app.py            # 默认 5000 端口
    python app.py --port 8000
"""

import argparse
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

# 基于脚本所在目录定位数据库，避免硬编码路径
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "todo.db"

app = Flask(__name__)


# ======================================================================
# SQLite 操作
# ======================================================================
def get_db():
    """获取当前请求的数据库连接（存在 g 中，请求结束自动关闭）。"""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row  # 让查询结果可按列名访问
    return g.db


@app.teardown_appcontext
def close_db(exc):
    """每个请求结束后关闭数据库连接，释放资源。"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """初始化数据库：表不存在则创建。

    表结构 todos：
        id         INTEGER  主键，自增
        content    TEXT     待办内容
        created_at TEXT     创建时间（字符串，格式 YYYY-MM-DD HH:MM:SS）
        is_done    INTEGER  完成状态，0=未完成，1=已完成
    """
    con = sqlite3.connect(DB_PATH)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            content    TEXT    NOT NULL,
            created_at TEXT    NOT NULL,
            is_done    INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    con.commit()
    con.close()


def wants_json():
    """判断请求是否来自前端 fetch（用于返回 JSON 还是重定向）。"""
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


# ======================================================================
# 路由
# ======================================================================
@app.route("/")
def index():
    """首页：查询全部待办，渲染到 index.html。

    前后端交互点：模板把每条待办的 id 渲染进复选框/删除按钮的
    data-id 属性，前端 JS 再拿该 id 去调用 /toggle 与 /delete。
    """
    db = get_db()
    todos = db.execute(
        "SELECT id, content, created_at, is_done FROM todos ORDER BY id ASC"
    ).fetchall()
    return render_template("index.html", todos=todos)


@app.route("/add", methods=["POST"])
def add():
    """添加待办：读取表单字段 content，写入数据库后重定向回首页。"""
    content = (request.form.get("content") or "").strip()
    if content:  # 内容为空则不写入
        db = get_db()
        db.execute(
            "INSERT INTO todos (content, created_at, is_done) VALUES (?, ?, 0)",
            (content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        db.commit()
    return redirect(url_for("index"))


@app.route("/toggle/<int:todo_id>", methods=["POST"])
def toggle(todo_id):
    """切换完成状态：把 is_done 在 0/1 间翻转。

    该接口由前端 fetch 调用（无刷新），返回 JSON 供 JS 更新样式；
    非 fetch 访问时回退为重定向。
    """
    db = get_db()
    row = db.execute("SELECT is_done FROM todos WHERE id = ?", (todo_id,)).fetchone()
    if row is None:
        if wants_json():
            return jsonify({"error": "not found", "id": todo_id}), 404
        return redirect(url_for("index"))

    new_state = 0 if row["is_done"] else 1
    db.execute("UPDATE todos SET is_done = ? WHERE id = ?", (new_state, todo_id))
    db.commit()

    if wants_json():
        return jsonify({"id": todo_id, "is_done": bool(new_state)})
    return redirect(url_for("index"))


@app.route("/delete/<int:todo_id>", methods=["POST"])
def delete(todo_id):
    """删除待办：fetch 请求返回 JSON（前端移除对应卡片），否则重定向。"""
    db = get_db()
    db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    db.commit()

    if wants_json():
        return jsonify({"deleted": todo_id})
    return redirect(url_for("index"))


# ======================================================================
# 错误处理
# ======================================================================
@app.errorhandler(404)
def not_found(error):
    """404：页面找不到。fetch 请求返回 JSON，其余返回错误页。"""
    if wants_json():
        return jsonify({"error": "Not Found"}), 404
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    """500：服务器内部错误。"""
    if wants_json():
        return jsonify({"error": "Internal Server Error"}), 500
    return render_template("500.html"), 500


def main():
    parser = argparse.ArgumentParser(description="待办事项 Web 应用")
    parser.add_argument("--port", type=int, default=5000, help="监听端口（默认 5000）")
    args = parser.parse_args()

    init_db()  # 启动前确保数据库与表已就绪
    url = f"http://127.0.0.1:{args.port}"
    print(f"待办事项 Web 应用已启动，访问地址：{url}")
    print("按 Ctrl+C 停止服务")
    app.run(host="127.0.0.1", port=args.port, debug=True)


if __name__ == "__main__":
    main()
