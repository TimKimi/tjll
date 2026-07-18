# Qwen2.5-7B-Instruct（GGUF Q4_K_M）— 可选本地清洗 LLM

**仅 RTX 4060 8GB（或同等显存）且要跑离线评论清洗的同学需要。**
其他人可忽略本目录；主项目 `just install` / `.env` **不会**要求下载此权重。

| 项 | 值 |
|---|---|
| 基座 | Qwen2.5-7B-Instruct |
| 量化 | Q4_K_M（~4.7 GB） |
| 显存（短 ctx） | 约 5.5–6.8 GB |
| 推理 | llama.cpp（见 `../../tools/llama.cpp/`） |

配置与主项目隔离：复制 `config.local.example.toml` → `config.local.toml`（后者不入 Git）。

---

## 1. 手动下载模型（控制台执行）

在仓库根目录 `tjll/` 下。国内直连 `huggingface.co` 常超时，**优先用镜像**：

```powershell
# 当前 PowerShell 会话有效；也可写进用户环境变量
$env:HF_ENDPOINT = "https://hf-mirror.com"

uv run hf download bartowski/Qwen2.5-7B-Instruct-GGUF `
  --include "Qwen2.5-7B-Instruct-Q4_K_M.gguf" `
  --local-dir backend/RAG/models/qwen2.5-7b-instruct-gguf
```

成功标志：本目录出现约 **4.7 GB** 的 `Qwen2.5-7B-Instruct-Q4_K_M.gguf`。
若仍失败，浏览器打开镜像页手动下载后放到本目录：

- https://hf-mirror.com/bartowski/Qwen2.5-7B-Instruct-GGUF/blob/main/Qwen2.5-7B-Instruct-Q4_K_M.gguf
- 或官网（需能翻墙）：https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF

---

## 2. 本地配置

```powershell
Copy-Item config.local.example.toml config.local.toml
# 按需改 n_ctx / llama_cli 路径
```

---

## 3. 冒烟测试（需先装好 llama.cpp）

在仓库根目录 `tjll/` 下（路径按本机调整）：

```powershell
.\backend\RAG\tools\llama.cpp\llama-cli.exe `
  -m .\backend\RAG\models\qwen2.5-7b-instruct-gguf\Qwen2.5-7B-Instruct-Q4_K_M.gguf `
  -ngl 99 -c 2048 -n 32 -p "Say OK"
```

成功标准：数秒内出词、任务管理器 GPU 有占用、无缺 DLL。
若 OOM：把 `-c 2048` 保持或更小；清洗脚本默认用 `config.local.toml` 里的 `n_ctx = 4096`。

---

## 注意

- 跑本模型时不要同时加载 `bge-base-zh-v1.5` / `bge-reranker-v2-m3`（显存会挤爆）。
- 不要把路径写进仓库根 `.env` 或 `backend/config.py`。

---

## 4. 离线评论清洗（模型与 llama-server 就绪后）

```powershell
Copy-Item config.local.example.toml config.local.toml
# 确认 extract_n_predict=256、target_chars=800

just review-clean 5 10 0 0 5
# 前 5 个必填；第 6 个「最多扫描评论数」可省略（默认 200）
```

算法：每条评论 **1 次短抽取**（`>4` 只好评，`(3,4]` 双侧含 3.5/4，`<=3` 只坏评）→ 追加；写满约 800 字停该侧；最后每侧最多 **1 次润色**。
结果：`data/yelp-dataset/cleaned/{business_id}.json`。
