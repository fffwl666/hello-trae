"""todo-fastapi —— 待办事项 Web API（FastAPI + SQLite + Pydantic）。

RESTful 接口：
    GET    /todos        获取全部待办
    POST   /todos        创建待办         body: {"content": "..."}
    PATCH  /todos/{id}   更新待办         body: {"content": "...", "is_done": true}
    DELETE /todos/{id}   删除待办

前端：
    GET /                返回 static/index.html（由 StaticFiles 挂载，html=True）
    GET /docs            FastAPI 自动生成的交互式 API 文档

运行：
    python app.py         # 默认 8000 端口
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from database import get_connection, init_db, row_to_dict
from models import TodoCreate, TodoResponse, TodoUpdate

# 静态资源目录（前端页面所在目录）
STATIC_DIR = Path(__file__).resolve().parent / "static"

# 查询单条/列表共用的 SQL 片段，避免重复书写
SELECT_FIELDS = "SELECT id, content, created_at, is_done FROM todos"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时自动建表。"""
    init_db()
    yield


app = FastAPI(
    title="todo-fastapi",
    description="待办事项 Web API，FastAPI + SQLite + Pydantic",
    version="1.0.0",
    lifespan=lifespan,
)


# ----------------------------------------------------------------------
# 路由
# ----------------------------------------------------------------------
@app.get("/todos", response_model=List[TodoResponse], summary="获取全部待办")
def list_todos():
    """返回所有待办，按 id 升序。"""
    con = get_connection()
    try:
        rows = con.execute(f"{SELECT_FIELDS} ORDER BY id ASC").fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        con.close()


@app.post("/todos", response_model=TodoResponse, status_code=201, summary="创建待办")
def create_todo(payload: TodoCreate):
    """创建一条待办；is_done 默认 0，created_at 由数据库默认值填充。"""
    con = get_connection()
    try:
        cur = con.execute("INSERT INTO todos (content) VALUES (?)", (payload.content,))
        con.commit()
        row = con.execute(f"{SELECT_FIELDS} WHERE id = ?", (cur.lastrowid,)).fetchone()
        return row_to_dict(row)
    finally:
        con.close()


@app.patch("/todos/{todo_id}", response_model=TodoResponse, summary="更新待办")
def update_todo(todo_id: int, payload: TodoUpdate):
    """更新待办内容或完成状态；只更新 body 中提供的字段，不存在则返回 404。"""
    con = get_connection()
    try:
        row = con.execute(f"{SELECT_FIELDS} WHERE id = ?", (todo_id,)).fetchone()
        if row is None:
            # 待办不存在 → 404
            raise HTTPException(status_code=404, detail=f"待办 {todo_id} 不存在")

        # 未提供的字段保持原值
        new_content = payload.content if payload.content is not None else row["content"]
        new_is_done = (
            int(payload.is_done) if payload.is_done is not None else row["is_done"]
        )
        con.execute(
            "UPDATE todos SET content = ?, is_done = ? WHERE id = ?",
            (new_content, new_is_done, todo_id),
        )
        con.commit()

        updated = con.execute(f"{SELECT_FIELDS} WHERE id = ?", (todo_id,)).fetchone()
        return row_to_dict(updated)
    finally:
        con.close()


@app.delete("/todos/{todo_id}", summary="删除待办")
def delete_todo(todo_id: int):
    """删除待办；不存在则返回 404。"""
    con = get_connection()
    try:
        row = con.execute("SELECT id FROM todos WHERE id = ?", (todo_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"待办 {todo_id} 不存在")
        con.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        con.commit()
        return {"deleted": todo_id}
    finally:
        con.close()


# ----------------------------------------------------------------------
# 挂载静态目录：放在所有 API 路由之后，确保 /todos 等接口优先匹配。
# html=True 时访问 "/" 会返回该目录下的 index.html。
# ----------------------------------------------------------------------
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
