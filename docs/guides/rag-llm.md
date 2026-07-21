# RAG / LLM 后端协作指南

面向其他后端同学：如何调用本模块的 Python 接口、如何准备数据，以及有显卡时如何加速 embedding。

---

## 1. 你们只需要调用 LLM 门面

**不要**直接 `import backend.rag`。检索、重排、OpenSearch 细节已封装在 LLM 管线内部。

推荐写法：

```python
from backend.llm import ask, AskRequest, AskResponse

# 方式一：dict（类似 JSON 包）
resp: AskResponse = ask(
    {
        "query": "这家店适合约会吗？",
        "section_id": "user-42-session-1",
        "uuid": "req-550e8400",
        # 以下字段本阶段可传，暂不处理：
        # "pdf": ..., "docx": ..., "doc": ..., "md": ..., "images": ...,
    }
)

print(resp.answer)       # LLM 回复
print(resp.sources)      # 本轮用到的 RAG 片段（无 embedding）
print(resp.history)      # 本轮写入前已有的会话历史
print(resp.query, resp.section_id, resp.uuid)

# 方式二：结构化对象
resp = ask(AskRequest(query="...", section_id="...", uuid="..."))
# 需要 dict 时：
payload = resp.model_dump()
```

### 请求字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `query` | 是 | 用户问题（str） |
| `section_id` | 是 | 会话/分区 ID，用作 Redis 多轮历史 key |
| `uuid` | 否 | 请求关联 ID，原样回传，不参与历史 |
| `docx` / `doc` / `md` / `pdf` / `images` | 否 | **占位**：可传，当前忽略；后续可能按附件分流路由 |

### 响应字段（`AskResponse` / `model_dump()`）

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | `str` | 本轮原问题 |
| `section_id` | `str` | 会话 ID |
| `uuid` | `str \| null` | 入参回传（未传则为 `null`） |
| `answer` | `str` | 本轮 LLM 回复全文 |
| `sources` | `list[RagSnippet]` | 本轮检索/精排后的片段（无 embedding） |
| `history` | `list[HistoryMessage]` | 本轮写入 Redis **之前**已有的会话消息 |

`RagSnippet`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `content` | `str` | 片段正文（索引字段 `text`） |
| `metadata` | `dict` | 索引全字段（除 `embedding` / `text`）+ `score` / `rerank_score` 等 |

`HistoryMessage`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `role` | `"user" \| "assistant" \| "system"` | 角色 |
| `content` | `str` | 消息正文 |

示例（`resp.model_dump()`）：

```json
{
  "query": "这家店适合约会吗？",
  "section_id": "user-42-session-1",
  "uuid": "req-550e8400",
  "answer": "根据现有资料……",
  "sources": [
    {
      "content": "服务很好，食物新鲜……",
      "metadata": {
        "chunk_id": "biz_pos_0000",
        "document_id": "biz",
        "chunk_index": 0,
        "score": 1.23,
        "rerank_score": 0.91,
        "polarity": "positive",
        "id": "biz",
        "name": "Acme Oyster House",
        "alias": "acme-oyster-house",
        "is_last_chunk": true
      }
    }
  ],
  "history": [
    { "role": "user", "content": "推荐一家性价比高的餐厅" },
    { "role": "assistant", "content": "推荐 Acme Oyster House……" }
  ]
}
```

说明：

- `sources[].metadata` 常见键（Yelp）：`chunk_id`、`document_id`、`chunk_index`、`polarity`、`id`、`name`、`alias`、`is_last_chunk`、`score`、`rerank_score` 等。PDF 遗留数据可能仍有 `source_file`，Yelp chunk 通常没有。
- `history` **不含**本轮的 `query` / `answer`（二者已在响应顶层）；首次提问时 `history` 为 `[]`。

### 本阶段唯一处理路径

```text
加载 Redis 历史
  → 查询重述（有历史时）
  → OpenSearch 混合检索（BM25 + 向量）
  → BGE Rerank
  → LLM 生成
  → 写回历史
```

后续若按附件走不同路由，仍会通过同一 `ask()` 门面扩展，调用方接口尽量保持稳定。

### 进阶（一般不需要）

`answer_query` / `answer_query_with_sources` / `stream_answer_query` 仍可从 `backend.llm` 导入，属于管线内部能力；**协作方请优先用 `ask`**。

---

## 2. 运行依赖（调用 ask 前请就绪）

| 依赖 | 用途 | 配置要点 |
|------|------|----------|
| OpenAI 兼容 LLM | 生成与重述 | `.env` 中 LLM 相关项 |
| Redis | 多轮历史 | `REDIS_*` |
| OpenSearch | 混合检索 | 索引默认 `yelp_biz_v1`（`OPENSEARCH_INDEX`） |
| 本机 BGE embedding / rerank | 向量化与精排 | `backend/rag/models/` 下权重；`EMBEDDING_DEVICE` |

启动 API 服务（若你们在 FastAPI 进程内调 `ask`）：

```bash
just serve
# 或 just up
```

---

## 3. Just：评论清洗与入库 OpenSearch

### 离线评论清洗（需本机 GGUF + llama.cpp，见 `backend/rag/models/.../README`）

```bash
# just review-clean <商家数> <最低评论数> <shard> <start> <end> [最多扫描评论数]
just review-clean 5 10 0 0 5 200
```

结果写入：`data/yelp-dataset/cleaned/{business_id}.json`。

### cleaned → OpenSearch

```bash
just index-cleaned-backfill      # 补写：只入库进度里没有的商家
just index-cleaned-rewrite       # 复写：全部重写（不删索引，同 chunk_id 覆盖）
just index-cleaned               # 同 backfill（兼容旧名）
just index-cleaned-recreate      # 删除索引重建后再复写
```

进度文件：`data/yelp-dataset/cleaned/index_progress.json`
仅当某商家**好评与坏评都成功写入**后才记录其 id。

首次使用请确认：

1. OpenSearch 已启动（见仓库 `docker-compose`）
2. BGE 权重已放到 `backend/rag/models/bge-base-zh-v1.5`（目录内应有 `modules.json`、`pytorch_model.bin` 等，不能只有 `.gitkeep`）
3. `.env` 中 `OPENSEARCH_INDEX=yelp_biz_v1`、`EMBEDDING_DEVICE` 合理

---

## 4. 有显卡：在项目 `.venv` 中换成 CUDA 版 PyTorch

`just` / `uv run` 使用仓库根目录 **`.venv`**。llama.cpp 离线清洗可自行走 GPU；**BGE embedding / rerank 走 PyTorch**。若 `.venv` 里是 `torch==...+cpu`，即使本机有显卡也无法加速。

### 操作步骤（在仓库根目录）

```powershell
cd D:\softwareinstal\pycharm\program\SHIXUNDAXIANGMU\tjll

# 1) 确认当前是否为 CPU 轮
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available())"

# 2) 卸掉 CPU 版
.\.venv\Scripts\python.exe -m pip uninstall -y torch torchvision torchaudio

# 3) 安装 CUDA 轮（推荐 cu128；不行再试 cu126）
.\.venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# 备选：
# .\.venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# 4) 验证
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__); print(torch.version.cuda); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"
```

期望：`...+cu128`（或 cu126）、`True`、能打印 GPU 名称。

### 需要改的配置文件

| 文件 | 改什么 |
|------|--------|
| 仓库根目录 **`.env`**（本地，勿提交） | 设 `EMBEDDING_DEVICE=cuda` |
| **`.env.example`** | 仅作文档参考；每人本地 `.env` 自行改 |
| **`uv.lock` / `pyproject.toml`** | **默认不要改**。CUDA 轮与平台相关，用上面 pip 覆盖本机 `.venv` 即可 |

说明：代码里若请求 `cuda` 但当前 Torch 无 CUDA，会自动回退到 `cpu` 并打 warning（见 `backend/rag/document/embed.py`）。装好 CUDA torch 并设置 `EMBEDDING_DEVICE=cuda` 后即可走 GPU。

团队协作以 **`.venv` + just** 为准。

---

## 5. 日志

`ask` / 检索 / 入库脚本会把日志写到 `backend/docs/`（可由 `.env` 的 `LOG_DIR` / `LOG_LEVEL` 调整；**只写文件，不打控制台**）：

| 文件 | Logger |
|------|--------|
| `backend/docs/llm.log` | `backend.llm.*` |
| `backend/docs/rag.log` | `backend.rag.*` |

每轮 `ask` 在 `llm.log` 中会记录：写入前历史全文、query 改造前后、精排后完整 chunk（`content` + metadata，无 embedding）、AI 回复全文。

`*.log` 已在 `.gitignore` 中，不会进 git。

---

## 6. 自检清单

- [ ] `from backend.llm import ask` 可导入
- [ ] Redis / OpenSearch / LLM 可达
- [ ] `yelp_biz_v1` 已有 cleaned 入库数据
- [ ] （可选）`.venv` 中 `torch.cuda.is_available() == True` 且 `.env` 为 `EMBEDDING_DEVICE=cuda`
