# todo-fastapi 的 Docker 镜像配置
FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 先复制依赖清单并安装，充分利用镜像层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 对外暴露 8000 端口
EXPOSE 8000

# 启动命令：uvicorn 运行 app 模块中的 app 对象
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
