"""数据库模块：SQLite 连接与建表（直接用 sqlite3，保持轻量，不引入 ORM）。"""

import sqlite3
from pathlib import Path

# 数据库文件与代码同目录，路径由 __file__ 推导，避免硬编码
DB_PATH = Path(__file__).resolve().parent / "todo.db"


def get_connection() -> sqlite3.Connection:
    """创建并返回一个数据库连接；row_factory 让结果可按列名访问。"""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    """应用启动时调用：表不存在则自动创建。

    表结构 todos：
        id         INTEGER   主键，自增
        content    TEXT      待办内容，非空
        is_done    BOOLEAN   完成状态，默认 0（未完成）
        created_at TIMESTAMP 创建时间，默认当前时间
    """
    con = get_connection()
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id         INTEGER   PRIMARY KEY AUTOINCREMENT,
                content    TEXT      NOT NULL,
                is_done    BOOLEAN   NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        con.commit()
    finally:
        con.close()


def row_to_dict(row: sqlite3.Row) -> dict:
    """把数据库行转成响应字典；把 0/1 的 is_done 转成真正的布尔值。"""
    return {
        "id": row["id"],
        "content": row["content"],
        "created_at": row["created_at"],
        "is_done": bool(row["is_done"]),
    }
