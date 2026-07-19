"""用户业务逻辑层：个人信息获取与更新。"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.app_user import AppUser
from backend.schemas.user import UpdateProfileRequest, UserProfileResponse


class UserService:
    """用户信息服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_profile(self, user_id: str) -> UserProfileResponse | None:
        """通过用户id，获取用户个人信息。"""
        user = await self._find_by_id(user_id)
        if not user:
            return None
        return self._to_profile(user)

    async def update_profile(
        self, user_id: str, req: UpdateProfileRequest
    ) -> UserProfileResponse | None:
        """通过用户id，更新用户个人信息，只更新提供的字段。"""
        user = await self._find_by_id(user_id)
        if not user:
            return None

        update_fields = req.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return self._to_profile(user)

    async def _find_by_id(self, user_id: str) -> AppUser | None:
        result = await self.db.execute(select(AppUser).where(AppUser.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    def _to_profile(user: AppUser) -> UserProfileResponse:
        return UserProfileResponse(
            id=user.id,
            username=user.username,
            avatar=user.avatar or "",
            is_online=user.is_online,
            email=user.email,
            bio=user.bio or "",
            register_time=user.register_time,
        )
