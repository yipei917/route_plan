# Docker 部署说明

本项目已配置为 Docker 容器化部署，提供 REST API 接口。

## 快速开始

### 方式一：使用 Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式二：使用 Docker 命令

```bash
# 构建镜像
docker build -t route-planner-api .

# 运行容器
docker run -d -p 8000:8000 --name route-planner-api route-planner-api

# 查看日志
docker logs -f route-planner-api

# 停止容器
docker stop route-planner-api
```

## API 文档

服务启动后，访问以下地址查看 API 文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 主要 API 端点

### 1. 健康检查
```
GET /health
```

### 2. 加载地图（JSON格式）
```
POST /api/v1/map/load
Content-Type: application/json

{
  "map_id": "map1",
  "width": 10,
  "height": 10,
  "cells": [
    {
      "x": 0,
      "y": 0,
      "type": "main_channel",
      "directions": ["up", "down", "left", "right"]
    }
  ],
  "main_channel_rows": [0]
}
```

### 3. 从文件加载地图
```
POST /api/v1/map/load/file?map_id=map1
Content-Type: multipart/form-data

file: <上传的JSON或Excel文件>
```

### 4. 路径规划
```
POST /api/v1/path/plan
Content-Type: application/json

{
  "map_id": "map1",
  "vehicle_id": "V1",
  "vehicle_type": "empty",
  "start": {"x": 8, "y": 7},
  "goal": {"x": 3, "y": 6}
}
```

### 5. 冲突检测
```
POST /api/v1/conflict/check
Content-Type: application/json

{
  "map_id": "map1",
  "vehicle_id": "V2",
  "vehicle_type": "empty",
  "path": [
    {"x": 6, "y": 7},
    {"x": 5, "y": 7}
  ],
  "existing_paths": {
    "V1": [
      {"x": 8, "y": 7},
      {"x": 7, "y": 7}
    ]
  }
}
```

## 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 加载地图
map_data = {
    "map_id": "test_map",
    "width": 10,
    "height": 10,
    "cells": [
        {"x": 0, "y": 0, "type": "main_channel", "directions": ["up", "down", "left", "right"]},
        # ... 更多单元格
    ]
}
response = requests.post(f"{BASE_URL}/api/v1/map/load", json=map_data)
print(response.json())

# 2. 路径规划
path_request = {
    "map_id": "test_map",
    "vehicle_id": "V1",
    "vehicle_type": "empty",
    "start": {"x": 8, "y": 7},
    "goal": {"x": 3, "y": 6}
}
response = requests.post(f"{BASE_URL}/api/v1/path/plan", json=path_request)
print(response.json())
```

### cURL 示例

```bash
# 健康检查
curl http://localhost:8000/health

# 路径规划
curl -X POST http://localhost:8000/api/v1/path/plan \
  -H "Content-Type: application/json" \
  -d '{
    "map_id": "map1",
    "vehicle_id": "V1",
    "vehicle_type": "empty",
    "start": {"x": 8, "y": 7},
    "goal": {"x": 3, "y": 6}
  }'
```

## 注意事项

1. **地图管理**：当前实现使用内存存储地图，容器重启后数据会丢失。生产环境建议使用数据库或 Redis。

2. **文件上传**：上传地图文件时，文件会临时保存到容器内，处理完成后自动删除。

3. **端口配置**：默认端口为 8000，可在 `docker-compose.yml` 中修改。

4. **资源目录**：`resource` 目录已挂载为只读卷，可直接访问其中的地图文件。

## 开发模式

如果需要本地开发（不使用 Docker）：

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
# 或
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

