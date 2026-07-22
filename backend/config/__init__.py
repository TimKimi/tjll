"""应用配置 — 统一入口。

所有默认值在此集中定义，按领域分节。
.env 文件放在仓库根目录，只覆盖需要修改的默认值。

完整配置参考见仓库根目录 .env.example。
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.config.paths import REPO_ROOT, resolve_path


class Settings(BaseSettings):
    """全局配置 — 从 .env 读取，缺失字段走默认值。"""

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # ================================================================
    # 应用基础
    # ================================================================
    APP_ENV: str = "development"
    """运行环境：development / production / testing"""
    APP_HOST: str = "127.0.0.1"
    """服务监听地址"""
    APP_PORT: int = 8000
    """服务监听端口"""
    APP_BASE_URL: str = ""
    """外部访问地址，空则自动从 APP_HOST+APP_PORT 推导（反代场景需手动设置）"""
    log_dir: str = "logs"
    """日志输出目录（相对 backend/）"""
    log_level: str = "INFO"
    """日志级别：DEBUG / INFO / WARNING / ERROR"""

    # ================================================================
    # 数据库 — PostgreSQL + Redis
    # ================================================================
    DATABASE_URL: str = "postgresql+asyncpg://tjll:tjll_dev@localhost:5432/tjll"
    """PostgreSQL 连接串"""
    DATABASE_ECHO: bool = False
    """是否打印 SQL 语句（开发调试用）"""
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = "Jianyan_01"
    redis_history_ttl: int = 86400
    """对话历史过期时间（秒），默认 24h"""

    # ================================================================
    # JWT 认证
    # ================================================================
    JWT_SECRET: str = Field(default="change-me-in-production")
    """[必填] JWT 签名密钥"""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    """Token 过期时间（分钟），默认 24 小时"""
    JWT_REFRESH_EXPIRE_DAYS: int = 7
    EMAIL_CHECK_DELIVERABILITY: bool = False
    """注册时是否检查邮箱域名可送达性"""

    # ================================================================
    # 邮件发送（密码找回用）
    # ================================================================
    SMTP_HOST: str = ""
    """[必填] SMTP 服务器地址"""
    SMTP_PORT: int = 587
    """SMTP 端口（SSL: 465, TLS: 587）"""
    SMTP_USER: str = ""
    """[必填] SMTP 用户名"""
    SMTP_PASSWORD: str = Field(default="")
    """[必填] SMTP 密码"""
    SMTP_FROM: str = ""
    """[必填] 发件人地址"""
    SMTP_USE_TLS: bool = True
    """是否使用 TLS"""
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    """密码重置 Token 过期时间（分钟）"""

    # ================================================================
    # 文件上传
    # ================================================================
    FILE_MAX_SIZE: int = 10 * 1024 * 1024
    """上传文件大小上限（字节），默认 10MB"""

    # ================================================================
    # LLM
    # ================================================================
    api_key: str = Field(default="")
    """[必填] LLM API 密钥"""
    base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-v4-flash"
    llm_generate_temperature: float = 0.7
    """AI 对话/推荐温度（越高越随机）"""
    llm_rewrite_temperature: float = 0.3
    """查询重写温度（越低越确定）"""
    llm_timeout: int = 120
    llm_max_retries: int = 2

    # ================================================================
    # Yelp — 外部 API + 学术数据集
    # ================================================================
    YELP_API_KEY: str = Field(default="", validation_alias="YELP_API")
    """[必填] Yelp Fusion API 密钥"""
    YELP_CLIENT_ID: str = Field(default="", validation_alias="CLIENT_ID")
    """[必填] Yelp Client ID"""
    YELP_API_BASE_URL: str = "https://api.yelp.com/v3"
    YELP_DATASET_DIR: str = "data/yelp-dataset"
    """数据集目录（相对仓库根目录）"""
    YELP_ZIP_PATH: str = "data/Yelp-JSON.zip"
    """数据集压缩包路径（相对仓库根目录）"""
    YELP_BATCH_SIZE: int = 500

    # ================================================================
    # OpenSearch + Embedding / Rerank
    # ================================================================
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_user: str = "admin"
    opensearch_password: str = "Jianyan_01"
    opensearch_use_ssl: bool = True
    opensearch_verify_certs: bool = False
    opensearch_index: str = "yelp_biz_v1"
    """索引名称"""
    opensearch_insight_index: str = "user_insight_v1"
    """用户洞察专用索引"""
    opensearch_section_insight_index: str = "section_insight_v1"
    """会话洞察属性切块索引"""
    opensearch_section_document_index: str = "section_document_v1"
    """会话上传文档切块索引"""
    embedding_model_path: str = "rag/models/bge-base-zh-v1.5"
    """Embedding 模型路径（相对 backend/）"""
    rerank_model_path: str = "rag/models/bge-reranker-v2-m3"
    """Rerank 模型路径（相对 backend/）"""
    embedding_device: str = "cuda"
    """运行设备：cuda / cpu"""
    rerank_use_fp16: bool = True
    embedding_dims: int = 768
    """向量维度（与 bge-base-zh-v1.5 一致）"""
    chunk_size: int = 500
    """文本块大小（字符数）"""
    chunk_overlap: int = 50
    """文本块重叠（字符数）"""
    insight_chunk_size: int = 200
    """用户洞察拼接/切分目标长度（字符数）"""
    retrieval_top_k: int = 10
    """初筛返回条数"""
    rerank_top_n: int = 3
    """精排后返回条数"""
    section_document_top_n: int = 1
    """会话文档检索默认返回 chunk 数"""
    hybrid_pipeline_name: str = "rag_hybrid_pipeline"
    hybrid_bm25_weight: float = 0.3
    hybrid_vector_weight: float = 0.7

    # ================================================================
    # MinerU — PDF 解析
    # ================================================================
    mineru_model_source: str = "modelscope"
    """模型来源：modelscope / huggingface"""
    modelscope_cache_path: str = ""
    mineru_pipeline_model_path: str = (
        "models/OpenDataLab--PDF-Extract-Kit-1.0/snapshots/master"
    )
    mineru_vlm_model_path: str = (
        "models/OpenDataLab--MinerU2.5-Pro-2605-1.2B/snapshots/master"
    )
    mineru_backend: str = "pipeline"
    """后端：pipeline / vlm"""
    mineru_method: str = "auto"
    """解析方法：auto / pdf / image"""
    mineru_output_path: str = "data/mineru-output"
    """MinerU 输出目录（相对 backend/）"""
    pdfs_path: str = "data/pdfs"
    """PDF 源文件目录（相对 backend/）"""

    # ================================================================
    # Validators
    # ================================================================

    @field_validator("JWT_EXPIRE_MINUTES", mode="before")
    @classmethod
    def _parse_jwt_expire(cls, v: Any) -> int:
        """支持 ``60 * 24`` 这类表达式写法。"""
        if isinstance(v, str) and "*" in v:
            parts = v.split("*")
            try:
                return int(parts[0].strip()) * int(parts[1].strip())
            except (ValueError, IndexError):
                pass
        return int(v) if v is not None else 1440

    # ================================================================
    # 派生属性
    # ================================================================

    @property
    def jwt_expire_delta(self) -> timedelta:
        return timedelta(minutes=self.JWT_EXPIRE_MINUTES)

    @property
    def yelp_dataset_dir(self) -> Path:
        return REPO_ROOT / self.YELP_DATASET_DIR

    @property
    def yelp_zip_path(self) -> Path:
        return REPO_ROOT / self.YELP_ZIP_PATH

    @property
    def redis_url(self) -> str:
        return (
            f"redis://:{self.redis_password}"
            f"@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        )

    @property
    def embedding_model_dir(self) -> str:
        return resolve_path(self.embedding_model_path)

    @property
    def rerank_model_dir(self) -> str:
        return resolve_path(self.rerank_model_path)

    @property
    def modelscope_cache_dir(self) -> str:
        return resolve_path(self.modelscope_cache_path)

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
        return resolve_path(self.mineru_output_path)

    @property
    def pdfs_dir(self) -> str:
        return resolve_path(self.pdfs_path)

    @property
    def log_dir_path(self) -> Path:
        return Path(resolve_path(self.log_dir))

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
