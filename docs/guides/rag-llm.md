# RAG / LLM 后端协作指南

面向其他后端同学：如何调用本模块的 Python 门面。本模块**不直连 HTTP/前端**；路由层请自行封装 DTO 再转调本门面。

结构体禁止以 `Request` / `Response` 结尾。

---

## 1. 你们只需要调用 LLM 门面

**不要**直接 `import backend.rag`。检索、重排、OpenSearch 细节已封装在 LangGraph ask 管线内部。

推荐写法（**流式 ask** + **专用历史接口**）：

```python
from backend.llm import (
    ask,
    get_ask_history,
    get_section_ids,
    AskParams,
    AskResult,
    release_ask_session,
)

# 登录后列出该用户全部会话
section_ids = get_section_ids(uuid="req-550e8400")

stream = ask(
    AskParams(
        query="这家店适合约会吗？",
        section_id="user-42-session-1",
        uuid="req-550e8400",
        # 可选：insight_create / insight_use
        # 附件字段仅标记 used（须先 load_section_document）：pdf / docx / ...
    )
)

for piece in stream:          # answer 文本块
    print(piece, end="", flush=True)

resp: AskResult = stream.response  # 流结束后可读完整结果
assert resp is not None
print(resp.answer)
print(resp.sources)
print(resp.query_filename)    # 本轮附件路径（逗号拼接）
print(resp.query, resp.section_id, resp.uuid)

hist = get_ask_history(uuid=resp.uuid, section_id=resp.section_id)
print(hist.history)

ok = release_ask_session(uuid=resp.uuid, section_id=resp.section_id)  # bool
```

### AskParams 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `query` | 是 | 用户问题（str） |
| `uuid` | 是 | 用户 ID；与 `section_id` **同时必填**，共同作为历史 Redis key（`{uuid}::{section_id}`） |
| `section_id` | 是 | 会话/分区 ID |
| `insight_create` / `insight_use` | 否 | 默认 `false`；写入**用户轮**历史扩展字段 |
| `docx` / `doc` / `txt` / `md` / `pdf` / `images` | 否 | `list[str] \| null`；默认 `null`。非空则 `add_used_filenames`（**不**解析文件）。文件须先经 `load_section_document` 入库。路径约定：以 `./backend/` 开头指向最终文件 |

### AskResult 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `query` | `str` | 本轮原问题 |
| `section_id` | `str` | 会话 ID |
| `uuid` | `str` | 入参回传 |
| `answer` | `str` | 本轮 LLM 回复全文 |
| `sources` | `list[RagSnippet]` | 本轮检索/精排后的片段（无 embedding） |
| `query_filename` | `str` | 本轮附件路径（逗号拼接） |

> 会话历史**不**随 `AskResult` 返回，请用 `get_ask_history`。

`RagSnippet`：`content: str` + `metadata: dict`（索引全字段除 `embedding`，含 `score` / `rerank_score` 等）。

---

## 2. 对外函数一览

除 `ask` 使用 `AskParams` 外，其余一律 **keyword / 位置参数**（key=value），不收包装结构体。

| 函数 | 入参 | 返回 |
|------|------|------|
| `get_section_ids` | `uuid` | `list[str]` |
| `get_ask_history` | `uuid`, `section_id` | `AskHistory` |
| `delete_ask_history` | `uuid`, `section_id` | `bool` |
| `delete_ask_histories_by_uuid` | `uuid` | `DeleteHistoryResult` |
| `release_ask_session` | `uuid`, `section_id` | `bool` |
| `release_ask_sessions_by_uuid` | `uuid` | `bool` |
| `get_user_insight` | `uuid` | `dict`（裸 attrs） |
| `update_user_insight_attrs` | `uuid`, `attrs: dict` | `bool` |
| `delete_user_insight` | `uuid` | `bool` |
| `delete_all_insights` | `uuid` | `bool` |
| `get_section_insight` | `uuid`, `section_id` | `dict`（裸 attrs） |
| `update_section_insight_attrs` | `uuid`, `section_id`, `attrs: dict` | `bool` |
| `delete_section_insight` | `uuid`, `section_id` | `bool` |
| `get_section_facts` | `uuid`, `section_id` | `list[str]` |
| `update_section_facts` | `uuid`, `section_id`, `items: list[str]` | `bool` |
| `get_section_review` | `uuid`, `section_id` | `str` |
| `set_section_review` | `uuid`, `section_id`, `text: str` | `bool` |
| `load_section_document` | `uuid`, `section_id`, `file_path: str` | `bool` |
| `ask` | `AskParams` | `AskStream`（`.response` → `AskResult`） |

写操作约定：成功 `True`，失败 `False`（调用方可不校验）。

### AskHistory

| 字段 | 类型 | 说明 |
|------|------|------|
| `uuid` / `section_id` | `str` | 入参回传 |
| `history` | `list[HistoryMessage]` | 完整会话历史 |
| `insight_create` | `bool` | 末条 user 消息的 `insight_create`；无 user 时为 `false` |
| `insight_use` | `bool` | 末条 user 消息的 `insight_use`；无 user 时为 `false` |

`HistoryMessage`：

| 字段 | 类型 | 说明 |
|------|------|------|
| `role` | `"user" \| "assistant" \| "system"` | 角色 |
| `content` | `str` | 消息正文 |
| `filename` | `str \| null` | **用户轮**关联文件路径，可为空；约定 `./backend/.../name.ext` |
| `insight_create` / `insight_use` | `bool \| null` | **用户轮**该次开关；助手/系统为 `null` |
| `sources` | `list[RagSnippet] \| null` | **助手轮**参考资料 |

### DeleteHistoryResult（仅全删）

| 字段 | 类型 | 说明 |
|------|------|------|
| `uuid` | `str` | 入参回传 |
| `section_id` | `str \| null` | 全删时为 `null` |
| `deleted_sessions` | `int` | 实际清理的会话数 |
| `section_ids` | `list[str]` | 被清理的 `section_id` 列表 |

### 文档加载

```python
from backend.llm import load_section_document

ok = load_section_document(
    uuid="req-550e8400",
    section_id="user-42-session-1",
    file_path="./backend/data/uploads/note.md",
)
# 成功入库后会删除磁盘原文件；ask 附件字段再带同一路径标记 used
```

### 示例

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
        "score": 1.23,
        "rerank_score": 0.91,
        "name": "Acme Oyster House"
      }
    }
  ]
}
```

```json
{
  "uuid": "req-550e8400",
  "section_id": "user-42-session-1",
  "insight_create": false,
  "insight_use": true,
  "history": [
    {
      "role": "user",
      "content": "推荐一家性价比高的餐厅",
      "filename": "",
      "insight_create": false,
      "insight_use": true,
      "sources": null
    },
    {
      "role": "assistant",
      "content": "推荐 Acme Oyster House……",
      "filename": null,
      "insight_create": null,
      "insight_use": null,
      "sources": [
        { "content": "……", "metadata": { "name": "Acme Oyster House" } }
      ]
    }
  ]
}
```

契约定义见：`backend/schemas/llm.py`（`backend/llm/schemas.py` 为重导出）；实现见：`backend/llm/graph/service.py`。

---

## 3. 运行依赖（调用 ask 前请就绪）

| 依赖 | 用途 | 配置要点 |
|------|------|----------|
| OpenAI 兼容 LLM | 生成与重述 | `.env` 中 LLM 相关项 |
| Redis | 多轮历史 + LangGraph checkpoint | `REDIS_*`（需 Redis Stack） |
| OpenSearch | 混合检索 | 索引默认 `yelp_biz_v1`（`OPENSEARCH_INDEX`） |
| 本机 BGE embedding / rerank | 向量化与精排 | `backend/rag/models/` 下权重；`EMBEDDING_DEVICE` |

```bash
just serve
# 或 just up
```

---

## 4. Just：评论清洗与入库 OpenSearch

```bash
just review-clean 5 10 0 0 5 200
just index-cleaned-backfill
just index-cleaned-rewrite
just index-cleaned-recreate
```

进度文件：`data/yelp-dataset/cleaned/index_progress.json`。

---

## 5. 有显卡：在项目 `.venv` 中换成 CUDA 版 PyTorch

```powershell
cd D:\softwareinstal\pycharm\program\SHIXUNDAXIANGMU\tjll
.\.venv\Scripts\python.exe -m pip uninstall -y torch torchvision torchaudio
.\.venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

本地 `.env` 设 `EMBEDDING_DEVICE=cuda`。

---

## 6. 日志

| 文件 | Logger |
|------|--------|
| `logs/llm.log` | `backend.llm.*` |
| `logs/rag.log` | `backend.rag.*` |

---

## 7. 自检清单

- [ ] `from backend.llm import ask, AskParams` 可导入，且为流式
- [ ] Redis Stack / OpenSearch / LLM 可达
- [ ] `yelp_biz_v1` 已有 cleaned 入库数据
- [ ] （可选）CUDA torch + `EMBEDDING_DEVICE=cuda`
