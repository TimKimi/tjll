"""AI 对话编排：用户设置合并、桥接 backend.llm。"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.llm.schemas import AskRequest
from backend.models.user_setting import UserSetting

logger = logging.getLogger("backend.services.llm")


class LlmService:
    """AI 对话编排服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def prepare_ask_request(
        self,
        query: str,
        section_id: str,
        user: dict,
        insight_create: bool | None = None,
        insight_use: bool | None = None,
    ) -> AskRequest:
        """合并用户设置后构建 AskRequest。

        优先级：请求参数 > 用户全局配置 > 默认值 (false)。
        """
        owner_id = user.get("sub", "")
        cfg_insight_create: bool = False
        cfg_insight_use: bool = False

        if owner_id:
            result = await self.db.execute(
                select(UserSetting).where(UserSetting.user_id == owner_id)
            )
            setting = result.scalar_one_or_none()
            if setting and setting.settings:
                s = setting.settings
                cfg_insight_create = bool(s.get("insight_create", False))
                cfg_insight_use = bool(s.get("insight_use", False))

        if insight_create is not None:
            cfg_insight_create = insight_create
        if insight_use is not None:
            cfg_insight_use = insight_use

        logger.debug(
            "ask settings merged user=%s insight_create=%s insight_use=%s",
            owner_id,
            cfg_insight_create,
            cfg_insight_use,
        )

        return AskRequest(
            query=query,
            section_id=section_id,
            uuid=owner_id,
            insight_create=cfg_insight_create,
            insight_use=cfg_insight_use,
        )
