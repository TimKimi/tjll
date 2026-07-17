# 本地模型目录（权重不入 Git）

本目录在 **backend/RAG/models/**，只提交占位结构。

## 获取权重

```powershell
$src = "D:\softwareinstal\pycharm\program\shixun\models"
$dst = "D:\softwareinstal\pycharm\program\SHIXUNDAXIANGMU\tjll\backend\RAG\models"
Copy-Item "$src\bge-base-zh-v1.5\*" "$dst\bge-base-zh-v1.5\" -Recurse -Force
Copy-Item "$src\bge-reranker-v2-m3\*" "$dst\bge-reranker-v2-m3\" -Recurse -Force
```

配置：仓库根 `.env.example` → 本地 `.env`（勿提交）。
代码：`from backend.config import settings`。

Docker：根目录 `docker-compose.yml`（Postgres + OpenSearch）；OpenSearch Dockerfile 在 `backend/RAG/infra/opensearch/`。
