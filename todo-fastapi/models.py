"""Pydantic 数据模型：定义接口的请求体与响应体。

- TodoCreate：创建待办时客户端提交的 body
- TodoUpdate：更新待办时的 body（字段可选，只更新提供的字段）
- TodoResponse：接口返回给客户端的待办结构
"""

from typing import Optional

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    """创建待办请求体：{"content": "..."}"""

    content: str = Field(..., min_length=1, description="待办内容，不能为空")


class TodoUpdate(BaseModel):
    """更新待办请求体：content 与 is_done 均可选，只传需要修改的字段。"""

    content: Optional[str] = Field(None, min_length=1, description="新的待办内容")
    is_done: Optional[bool] = Field(None, description="是否完成")


class TodoComplete(BaseModel):
    """完成状态请求体：PUT /todos/{id}/complete，例如 {"is_done": true}。

    显式传入目标状态（而非服务端盲目取反），保证重复请求/快速点击时结果幂等。
    """

    is_done: bool = Field(..., description="目标完成状态：true 勾选，false 取消勾选")


class TodoResponse(BaseModel):
    """待办响应体，对应数据库 todos 表的一行。"""

    id: int
    content: str
    created_at: str
    is_done: bool
