"""Yelp 配置 — API 密钥、数据集路径。"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field

from backend.config.paths import REPO_ROOT


class YelpMixin:
    """Yelp 外部 API + 学术数据集 配置。

    所有默认值在此统一修改。
    """

    # ── Yelp Fusion API ──────────────────────────────────────
    # [必填] Yelp Fusion API 密钥，无默认值
    YELP_API_KEY: str = Field(default="", validation_alias="YELP_API")
    # [必填] Yelp Client ID，无默认值
    YELP_CLIENT_ID: str = Field(default="", validation_alias="CLIENT_ID")
    # Yelp API 基础地址（一般不需要改）
    YELP_API_BASE_URL: str = "https://api.yelp.com/v3"

    # ── Yelp 学术数据集（JSONL）────
    # 数据集目录（相对仓库根目录）
    YELP_DATASET_DIR: str = "data/yelp-dataset"
    # 数据集压缩包路径（相对仓库根目录）
    YELP_ZIP_PATH: str = "data/Yelp-JSON.zip"
    # 每批写入数据库的行数
    YELP_BATCH_SIZE: int = 500

    # ── 派生属性 ─────────────────────────────────────────────

    @property
    def yelp_dataset_dir(self) -> Path:
        """数据集解压目录（绝对路径）。"""
        return REPO_ROOT / self.YELP_DATASET_DIR

    @property
    def yelp_zip_path(self) -> Path:
        """数据集压缩包（绝对路径）。"""
        return REPO_ROOT / self.YELP_ZIP_PATH
