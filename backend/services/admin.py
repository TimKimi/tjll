"""Admin 业务逻辑层：管理员信息、用户管理。"""

from __future__ import annotations

import logging
import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import AppError
from backend.models.app_user import AppUser
from backend.schemas.admin import AdminProfileResponse, AdminUserItem
from backend.schemas.common import PaginatedData

logger = logging.getLogger("backend.services.admin")


class AdminService:
    """管理员服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_admin_profile(self, user_id: str) -> AdminProfileResponse | None:
        """通过用户 ID 获取管理员信息。"""
        result = await self.db.execute(select(AppUser).where(AppUser.id == user_id))
        user = result.scalar_one_or_none()
        if not user or user.role != "admin":
            return None
        return AdminProfileResponse(
            id=user.id,
            username=user.username,
            avatar=user.avatar or "",
            role=user.role,
        )

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
    ) -> PaginatedData[AdminUserItem]:
        """获取所有用户列表（分页，支持关键词搜索）。"""
        base_query = select(AppUser)
        count_query = select(func.count(AppUser.id))

        if keyword:
            like_pattern = f"%{keyword}%"
            base_query = base_query.where(AppUser.username.ilike(like_pattern))
            count_query = count_query.where(AppUser.username.ilike(like_pattern))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size

        q = (
            base_query.order_by(AppUser.register_time.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows_result = await self.db.execute(q)
        users = rows_result.scalars().all()

        items = [self._user_to_item(u) for u in users]

        return PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def change_role(
        self, admin_id: str, target_user_id: str, new_role: str
    ) -> AdminUserItem:
        """修改指定用户的角色。

        Raises:
            AppError: 目标用户不存在、不能修改自己的角色。
        """
        if admin_id == target_user_id:
            raise AppError("不能修改自己的角色", code=400)

        result = await self.db.execute(
            select(AppUser).where(AppUser.id == target_user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise AppError("用户不存在", code=404)

        old_role = user.role
        user.role = new_role
        await self.db.commit()

        logger.info(
            "角色变更 admin=%s target=%s %s → %s",
            admin_id,
            target_user_id,
            old_role,
            new_role,
        )
        return self._user_to_item(user)

    async def delete_user(self, admin_id: str, target_user_id: str) -> None:
        """删除指定用户。

        Raises:
            AppError: 目标用户不存在、不能删除自己。
        """
        if admin_id == target_user_id:
            raise AppError("不能删除自己的账号", code=400)

        result = await self.db.execute(
            select(AppUser).where(AppUser.id == target_user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise AppError("用户不存在", code=404)

        await self.db.delete(user)
        await self.db.commit()

        logger.warning(
            "用户被删除 admin=%s target=%s username=%s",
            admin_id,
            target_user_id,
            user.username,
        )

    @staticmethod
    def _user_to_item(user: AppUser) -> AdminUserItem:
        return AdminUserItem(
            id=user.id,
            username=user.username,
            avatar=user.avatar or "",
            is_online=user.is_online,
            email=user.email,
            bio=user.bio or "",
            register_time=user.register_time,
            role=user.role,
        )
