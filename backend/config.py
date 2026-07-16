"""应用配置：Yelp/DB + RAG；密钥读仓库根 .env 与 backend/.env。"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/config.py → 应用根 backend/
PROJECT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT.parent


def _resolve_path(path: str) -> str:
    p = Path(path)
    if p.is_absolute():
        return str(p.resolve())
    return str((PROJECT_ROOT / p).resolve())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            str(REPO_ROOT / ".env"),
            str(PROJECT_ROOT / ".env"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # ---- Yelp API（develop）----
    YELP_API_KEY: str = Field(default="", validation_alias="YELP_API")
    YELP_CLIENT_ID: str = Field(default="", validation_alias="CLIENT_ID")
    YELP_API_BASE_URL: str = "https://api.yelp.com/v3"

    # ---- 数据库 ----
    DATABASE_URL: str = "postgresql+asyncpg://tjll:Jianyan_01@localhost:5432/tjll"
    DATABASE_ECHO: bool = False

    # ---- 服务器 ----
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # ---- LLM（后续生成；本期文档加载可空）----
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-v4-flash"
    llm_generate_temperature: float = 0.7
    llm_rewrite_temperature: float = 0.3
    llm_timeout: int = 120
    llm_max_retries: int = 2

    # ---- OpenSearch ----
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_user: str = "admin"
    opensearch_password: str = "Jianyan_01"
    opensearch_use_ssl: bool = True
    opensearch_verify_certs: bool = False
    opensearch_index: str = "rag_kb_v1"

    # ---- 项目内模型（相对 backend/）----
    embedding_model_path: str = "RAG/models/bge-base-zh-v1.5"
    rerank_model_path: str = "RAG/models/bge-reranker-v2-m3"
    embedding_device: str = "cuda"
    rerank_use_fp16: bool = True

    # ---- MinerU / ModelScope ----
    mineru_model_source: str = "modelscope"
    modelscope_cache_path: str = ""
    mineru_pipeline_model_path: str = (
        "models/OpenDataLab--PDF-Extract-Kit-1.0/snapshots/master"
    )
    mineru_vlm_model_path: str = (
        "models/OpenDataLab--MinerU2.5-Pro-2605-1.2B/snapshots/master"
    )
    mineru_backend: str = "pipeline"
    mineru_method: str = "auto"

    # ---- 数据目录 ----
    mineru_output_path: str = "data/mineru-output"
    pdfs_path: str = "data/pdfs"

    # ---- RAG 切分与检索 ----
    chunk_size: int = 500
    chunk_overlap: int = 50
    retrieval_top_k: int = 10
    rerank_top_n: int = 3
    embedding_dims: int = 768  # bge-base-zh-v1.5
    hybrid_pipeline_name: str = "rag_hybrid_pipeline"
    hybrid_bm25_weight: float = 0.3
    hybrid_vector_weight: float = 0.7

    # ---- Redis（对话历史，需 redis-stack）----
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = "Jianyan_01"
    redis_history_ttl: int = 86400  # 24h

    @property
    def redis_url(self) -> str:
        return (
            f"redis://:{self.redis_password}"
            f"@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        )

    @property
    def embedding_model_dir(self) -> str:
        return _resolve_path(self.embedding_model_path)

    @property
    def rerank_model_dir(self) -> str:
        return _resolve_path(self.rerank_model_path)

    @property
    def modelscope_cache_dir(self) -> str:
        return _resolve_path(self.modelscope_cache_path)

    @property
    def mineru_pipeline_model_dir(self) -> str:
        base = Path(self.modelscope_cache_dir)
        rel = Path(self.mineru_pipeline_model_path)
        if rel.is_absolute():
            return str(rel.resolve())
        return str((base / rel).resolve())

    @property
    def mineru_vlm_model_dir(self) -> str:
        base = Path(self.modelscope_cache_dir)
        rel = Path(self.mineru_vlm_model_path)
        if rel.is_absolute():
            return str(rel.resolve())
        return str((base / rel).resolve())

    @property
    def mineru_output_dir(self) -> str:
        return _resolve_path(self.mineru_output_path)

    @property
    def pdfs_dir(self) -> str:
        return _resolve_path(self.pdfs_path)

    @property
    def opensearch_url(self) -> str:
        scheme = "https" if self.opensearch_use_ssl else "http"
        return f"{scheme}://{self.opensearch_host}:{self.opensearch_port}"

    @property
    def opensearch_auth(self) -> tuple[str, str]:
        return self.opensearch_user, self.opensearch_password

    @property
    def llm_kwargs(self) -> dict[str, object]:
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.llm_model,
            "temperature": self.llm_generate_temperature,
            "timeout": self.llm_timeout,
            "max_retries": self.llm_max_retries,
        }


settings = Settings()
