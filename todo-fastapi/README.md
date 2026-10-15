# todo-fastapi · 待办事项 Web API

基于 **FastAPI + SQLite + Pydantic** 的待办事项 API，附带原生 JS 前端页面。
不使用 SQLAlchemy，直接用标准库 `sqlite3` 操作，保持轻量。

## 技术栈

- **Web 框架**：FastAPI（含自动生成的 `/docs` 交互式文档）
- **数据校验**：Pydantic v2
- **数据库**：SQLite（标准库 `sqlite3`）
- **前端**：原生 HTML + CSS + `fetch`
- **ASGI 服务器**：uvicorn

## 项目结构

```
todo-fastapi/
├── app.py              # 主程序：FastAPI 应用 + 路由 + 挂载静态目录
├── models.py           # Pydantic 模型：TodoCreate / TodoUpdate / TodoResponse
├── database.py         # 数据库连接与建表
├── static/
│   └── index.html      # 前端页面（原生 JS 调用接口）
├── requirements.txt    # 依赖列表
├── Dockerfile          # Docker 配置
└── README.md           # 项目说明
```

## 数据表结构

表 `todos`（启动时自动创建）：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER | 主键，自增 |
| content | TEXT | 待办内容，非空 |
| is_done | BOOLEAN | 完成状态，默认 0 |
| created_at | TIMESTAMP | 创建时间，默认 CURRENT_TIMESTAMP |

## 接口一览

| 方法 | 路径 | 请求体 | 说明 |
|---|---|---|---|
| GET | `/todos` | — | 获取全部待办 |
| POST | `/todos` | `{"content": "..."}` | 创建待办（201） |
| PATCH | `/todos/{id}` | `{"content": "...", "is_done": true}` | 更新待办（字段可选） |
| DELETE | `/todos/{id}` | — | 删除待办 |

- 待办不存在时，PATCH / DELETE 返回 **404**。
- 所有接口均返回 JSON。

## 本地运行

```bash
pip install -r requirements.txt
python app.py
```

启动后：

- 前端页面：<http://localhost:8000>
- API 文档：<http://localhost:8000/docs>

> 也可用 `uvicorn app:app --reload` 启动（热重载）。

## Docker 运行

```bash
docker build -t todo-fastapi .
docker run -p 8000:8000 todo-fastapi
```

## curl 测试命令

```bash
# 1. 查询列表（初始为空数组 []）
curl http://localhost:8000/todos

# 2. 创建待办
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"content": "买牛奶"}'

# 3. 创建第二条
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"content": "写周报"}'

# 4. 更新内容
curl -X PATCH http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"content": "买牛奶和面包"}'

# 5. 切换完成状态
curl -X PATCH http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"is_done": true}'

# 6. 删除
curl -X DELETE http://localhost:8000/todos/2

# 7. 访问不存在的待办（应返回 404）
curl -i http://localhost:8000/todos/999
```

Windows PowerShell 中内层引号建议转义为 `\"`，或改用 `Invoke-RestMethod`：

```powershell
Invoke-RestMethod -Uri http://localhost:8000/todos -Method Post `
  -ContentType "application/json" -Body '{"content": "买牛奶"}'
```

## 说明

- `database.py` 中 `DB_PATH` 由 `__file__` 推导，数据库文件与代码同目录，无硬编码路径。
- 应用通过 `lifespan` 在启动时调用 `init_db()` 自动建表。
- 静态目录用 `StaticFiles(html=True)` 挂载在 `/`，且位于所有 API 路由之后注册，
  因此 `/todos` 等接口优先匹配，`/` 返回 `static/index.html`。
