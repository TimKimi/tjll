# 本地模型目录（权重不入 Git）

本目录在 **backend/RAG/models/**，只提交占位结构。

## 全员需要：Embedding / Rerank

```powershell
$src = "D:\softwareinstal\pycharm\program\shixun\models"
$dst = "D:\softwareinstal\pycharm\program\SHIXUNDAXIANGMU\tjll\backend\RAG\models"
Copy-Item "$src\bge-base-zh-v1.5\*" "$dst\bge-base-zh-v1.5\" -Recurse -Force
Copy-Item "$src\bge-reranker-v2-m3\*" "$dst\bge-reranker-v2-m3\" -Recurse -Force
```

配置：仓库根 `.env.example` → 本地 `.env`（勿提交）。
代码：`from backend.config import settings`。

Docker：根目录 `docker-compose.yml`（Postgres + OpenSearch）；OpenSearch Dockerfile 在 `backend/RAG/infra/opensearch/`。

---

## 可选：离线评论清洗 LLM（仅 8GB 显卡）

目录：[`qwen2.5-7b-instruct-gguf/`](qwen2.5-7b-instruct-gguf/)
推理二进制：[`../tools/llama.cpp/`](../tools/llama.cpp/)

- **不写入** 根 `.env` / `backend/config.py`；旁路配置见该目录 `config.local.example.toml`
- **不进入** `just install`；需自行按子目录 README **手动下载**
- 无 8GB 卡或不做本地清洗的同学可完全跳过
