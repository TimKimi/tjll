# llama.cpp（Windows CUDA 预编译）— 可选

**仅需要本地 GGUF 推理（评论清洗）的同学安装。**
不进入 `just install`；二进制不入 Git。

推荐：从官方 Release 下载 **CUDA 12.4** 预编译包（勿下 CPU-only 包）。

## 下载（手动）

1. 打开最新 Release：https://github.com/ggml-org/llama.cpp/releases
2. 下载同版本的两个 zip：
   - `llama-bXXXX-bin-win-cuda-12.4-x64.zip`
   - `cudart-llama-bin-win-cuda-12.4-x64.zip`
3. 将两个 zip 内的内容解压到**本目录**（`backend/rag/tools/llama.cpp/`），保证 `llama-cli.exe` 与 `.dll` 同级。

解压后应至少看到：

```text
llama-cli.exe
llama-server.exe   # 评论清洗脚本会用到
ggml-cuda.dll 等
cudart64_*.dll 等（来自 cudart 包）
```

清洗旁路配置里的 `llama_server` 默认指向本目录的 `llama-server.exe`。

## 冒烟

见 `../../models/qwen2.5-7b-instruct-gguf/README.md`。

常用参数（4060 8GB）：

- `-ngl 99`：尽量全层上 GPU
- `-c 4096`：默认上下文；OOM 时改 `2048`
- 不要用满 32K 上下文

## 与主项目关系

- 不写入根 `.env` / `backend/config.py`
- 清洗脚本若启用，应读 `models/qwen2.5-7b-instruct-gguf/config.local.toml` 中的 `llama_cli` 路径
