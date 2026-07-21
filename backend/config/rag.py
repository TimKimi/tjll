"""RAG 配置 — OpenSearch 连接 + Embedding/Rerank 模型 + 检索参数。"""

from __future__ import annotations

from backend.config.paths import resolve_path


class RAGMixin:
    """RAG（检索增强生成）配置。

    所有默认值在此统一修改。
    """

    # ── OpenSearch ───────────────────────────────────────────
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_user: str = "admin"
    opensearch_password: str = "Jianyan_01"
    opensearch_use_ssl: bool = True
    opensearch_verify_certs: bool = False
    # 索引名称（不同实验建议用不同索引隔离）
    opensearch_index: str = "yelp_biz_v1"

    # ── 向量模型（相对 backend/；权重文件不入 git）──
    # bge-base-zh-v1.5 中文 Embedding 模型路径
    embedding_model_path: str = "rag/models/bge-base-zh-v1.5"
    # bge-reranker-v2-m3 精排模型路径
    rerank_model_path: str = "rag/models/bge-reranker-v2-m3"
    # 运行设备：cuda / cpu
    embedding_device: str = "cuda"
    # Rerank 是否使用 FP16 精度
    rerank_use_fp16: bool = True
    # Embedding 向量维度（与模型一致）
    embedding_dims: int = 768

    # ── 切分参数 ─────────────────────────────────────────────
    # 文本块大小（字符数）
    chunk_size: int = 500
    # 文本块重叠（字符数）
    chunk_overlap: int = 50

    # ── 检索参数 ─────────────────────────────────────────────
    # 初筛返回条数
    retrieval_top_k: int = 10
    # 精排后返回条数
    rerank_top_n: int = 3
    # 混合检索管道名称
    hybrid_pipeline_name: str = "rag_hybrid_pipeline"
    # BM25 权重
    hybrid_bm25_weight: float = 0.3
    # 向量检索权重
    hybrid_vector_weight: float = 0.7

    # ── 派生属性 ─────────────────────────────────────────────

    @property
    def opensearch_url(self) -> str:
        """OpenSearch 连接地址。"""
        scheme = "https" if self.opensearch_use_ssl else "http"
        return f"{scheme}://{self.opensearch_host}:{self.opensearch_port}"

    @property
    def opensearch_auth(self) -> tuple[str, str]:
        """OpenSearch 认证元组 (user, password)。"""
        return self.opensearch_user, self.opensearch_password

    @property
    def embedding_model_dir(self) -> str:
        """Embedding 模型绝对路径。"""
        return resolve_path(self.embedding_model_path)

    @property
    def rerank_model_dir(self) -> str:
        """Rerank 模型绝对路径。"""
        return resolve_path(self.rerank_model_path)
