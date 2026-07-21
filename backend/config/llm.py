"""LLM 配置 — API 密钥、模型参数。"""

from __future__ import annotations

from pydantic import Field


class LLMMixin:
    """大语言模型配置。

    所有默认值在此统一修改。
    """

    # ── API 连接 ─────────────────────────────────────────────
    # [必填] LLM API 密钥，无默认值
    api_key: str = Field(default="")
    # API 基础地址
    base_url: str = "https://api.deepseek.com/v1"
    # 模型名称
    llm_model: str = "deepseek-v4-flash"

    # ── 生成参数 ─────────────────────────────────────────────
    # AI 对话/推荐温度（越高越随机）
    llm_generate_temperature: float = 0.7
    # 查询重写温度（越低越确定）
    llm_rewrite_temperature: float = 0.3
    # 请求超时（秒）
    llm_timeout: int = 120
    # 失败重试次数
    llm_max_retries: int = 2

    # ── 派生属性 ─────────────────────────────────────────────

    @property
    def llm_kwargs(self) -> dict[str, object]:
        """LLM 客户端关键字参数字典。"""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.llm_model,
            "temperature": self.llm_generate_temperature,
            "timeout": self.llm_timeout,
            "max_retries": self.llm_max_retries,
        }
