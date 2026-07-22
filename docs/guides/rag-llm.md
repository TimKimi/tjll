# RAG / LLM 后端协作指南

面向其他后端同学：如何调用本模块的 Python 接口、如何准备数据，以及有显卡时如何加速 embedding。

---

## 1. 你们只需要调用 LLM 门面

**不要**直接 `import backend.rag`。检索、重排、OpenSearch 细节已封装在 LangGraph ask 管线内部。

推荐写法（**流式 ask** + **专用历史接口**）：

```python
from backend.llm import (
    ask,
    get_ask_history,
    AskRequest,
    AskResponse,
    release_ask_session,
)

# 方式一：dict（类似 JSON 包）
stream = ask(
    {
        "query": "这家店适合约会吗？",
        "section_id": "user-42-session-1",
        "uuid": "req-550e8400",
        # 可选：insight_create / insight_use（本阶段透传；insight_create 会写入用户历史）
        # 附件字段可传，当前忽略：pdf / docx / doc / md / images
    }
)

for piece in stream:          # answer 文本块
    print(piece, end="", flush=True)

resp: AskResponse = stream.response  # 流结束后可读完整响应
assert resp is not None
print(resp.answer)            # 完整回复
print(resp.sources)           # 本轮 RAG 片段（无 embedding）
print(resp.query_filename)    # 本轮附带文件名（暂为空串）
print(resp.query, resp.section_id, resp.uuid)

# 需要会话历史时单独拉取（完整历史 + 扩展字段）
hist = get_ask_history(uuid=resp.uuid, section_id=resp.section_id)
print(hist.history)

# 可选：释放会话槽（历史已在每轮结束写入 Redis；release 主要用于腾出 LRU 池）
release_ask_session(resp.uuid, resp.section_id)

# 方式二：结构化对象
stream = ask(AskRequest(query="...", section_id="...", uuid="..."))
"".join(stream)
payload = stream.response.model_dump()
```

### 请求字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `query` | 是 | 用户问题（str） |
| `uuid` | 是 | 用户/请求关联 ID；与 `section_id` **同时必填**，共同作为历史 Redis key（`{uuid}::{section_id}`） |
| `section_id` | 是 | 会话/分区 ID |
| `insight_create` / `insight_use` | 否 | 占位，默认 `false`；`insight_create` 会写入**用户轮**历史扩展字段（读取暂不处理业务） |
| `docx` / `doc` / `md` / `pdf` / `images` | 否 | **占位**：可传，当前忽略 |

### 响应字段（`AskResponse` / `model_dump()`）

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | `str` | 本轮原问题 |
| `section_id` | `str` | 会话 ID |
| `uuid` | `str` | 入参回传（必填） |
| `answer` | `str` | 本轮 LLM 回复全文 |
| `sources` | `list[RagSnippet]` | 本轮检索/精排后的片段（无 embedding） |
| `query_filename` | `str` | 当前轮用户请求附带文件名；**暂固定为空串**，后续维护 |

> 会话历史**不再**随 `AskResponse` 返回，请用下方 `get_ask_history`。

`RagSnippet`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `content` | `str` | 片段正文 |
| `metadata` | `dict` | 索引全字段（除 `embedding`）+ `score` / `rerank_score` 等 |

### 历史接口（`get_ask_history` / 删除）

```python
from backend.llm import (
    get_ask_history,
    delete_ask_history,
    delete_ask_histories_by_uuid,
    HistoryRequest,
)

hist = get_ask_history(uuid="req-550e8400", section_id="user-42-session-1")
# 或
hist = get_ask_history(HistoryRequest(uuid="...", section_id="..."))
print(hist.model_dump())

# 删除单个会话历史
delete_ask_history(uuid="req-550e8400", section_id="user-42-session-1")

# 删除该 uuid 下全部会话历史
delete_ask_histories_by_uuid(uuid="req-550e8400")
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `uuid` / `section_id` | `str` | 入参回传 |
| `history` | `list[HistoryMessage]` | **完整**会话历史（含本轮已写入的消息） |

删除接口返回 `DeleteHistoryResponse`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `uuid` | `str` | 入参回传 |
| `section_id` | `str \| null` | 单会话删除时回传；按 uuid 全删时为 `null` |
| `deleted_sessions` | `int` | 实际清理的会话数 |
| `section_ids` | `list[str]` | 被清理的 `section_id` 列表 |

说明：删除会同时清理内存会话池中的对应槽位，并调用 Redis 历史 `clear()`；按 uuid 全删时通过扫描 `chat:{uuid}::*` 找到全部会话。

`HistoryMessage`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `role` | `"user" \| "assistant" \| "system"` | 角色 |
| `content` | `str` | 消息正文 |
| `filename` | `str \| null` | **用户轮**关联文件名，可为空 |
| `insight_create` | `bool \| null` | **用户轮**该次是否要求创建洞察；助手/系统为 `null` |
| `sources` | `list[RagSnippet] \| null` | **助手轮**该次回复用到的参考资料 |

说明：内部 Redis 仍会持久化用户轮的 `search_query`（改写后的检索句），但**不出现在**对外 `history` 中。

示例（`AskResponse.model_dump()`）：

```json
{
  "query": "这家店适合约会吗？",
  "section_id": "user-42-session-1",
  "uuid": "req-550e8400",
  "answer": "根据现有资料……",
  "query_filename": "",
  "sources": [
    {
      "content": "服务很好，食物新鲜……",
      "metadata": {
        "chunk_id": "biz_pos_0000",
        "id": "biz",
        "chunk_index": 0,
        "score": 1.23,
        "rerank_score": 0.91,
        "polarity": "positive",
        "id": "biz",
        "name": "Acme Oyster House"
      }
    }
  ]
}
```

示例（`get_ask_history(...).model_dump()`）：

```json
{
  "uuid": "req-550e8400",
  "section_id": "user-42-session-1",
  "history": [
    {
      "role": "user",
      "content": "推荐一家性价比高的餐厅",
      "filename": "",
      "insight_create": false,
      "sources": null
    },
    {
      "role": "assistant",
      "content": "推荐 Acme Oyster House……",
      "filename": null,
      "insight_create": null,
      "sources": [
        { "content": "……", "metadata": { "name": "Acme Oyster House" } }
      ]
    }
  ]
}
```

说明：

- 历史按 `uuid` + `section_id` **同时必填**隔离；缺任一则拒绝。
- 内存会话池最多 5 个；**每轮 ask 结束后立即刷 Redis**（release / LRU / 进程退出仍会再 flush 空 pending）。
- `get_ask_history`：若会话仍在池内则读内存副本，否则从 Redis 加载（不额外驱逐其它会话）。

### 本阶段处理路径

```text
按 uuid+section_id 取/建会话（内存历史）
  → LangGraph：prepare →（有历史则 rewrite）→ retrieve_rerank
  → 流式 LLM 生成
  → 本轮写入内存历史并立即刷 Redis（含 search_query / filename / insight_create / sources）
```

契约定义见：`backend/llm/schemas.py`；实现见：`backend/llm/graph/`。

### 进阶（一般不需要）

`answer_query` / `answer_query_with_sources` / `stream_answer_query` 仍可从 `backend.llm` 导入（旧 LCEL 管线）；**协作方请优先用流式 `ask`**。

---

## 2. 运行依赖（调用 ask 前请就绪）

| 依赖 | 用途 | 配置要点 |
|------|------|----------|
| OpenAI 兼容 LLM | 生成与重述 | `.env` 中 LLM 相关项 |
| Redis | 多轮历史 + LangGraph checkpoint | `REDIS_*`（需 Redis Stack） |
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

`ask` / 检索 / 入库脚本会把日志写到 `logs/`（可由 `.env` 的 `LOG_DIR` / `LOG_LEVEL` 调整）：

| 文件 | Logger |
|------|--------|
| `logs/llm.log` | `backend.llm.*` |
| `logs/rag.log` | `backend.rag.*` |

开发环境（`APP_ENV=development`）下部分模块会额外打到控制台；详见 `backend/core/logger.py`。

`*.log` 已在 `.gitignore` 中，不会进 git。

---

## 6. 自检清单

- [ ] `from backend.llm import ask` 可导入，且为流式（`for x in ask(...): ...`）
- [ ] Redis Stack / OpenSearch / LLM 可达
- [ ] `yelp_biz_v1` 已有 cleaned 入库数据
- [ ] （可选）`.venv` 中 `torch.cuda.is_available() == True` 且 `.env` 为 `EMBEDDING_DEVICE=cuda`
