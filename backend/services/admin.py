"""Admin 业务逻辑层：管理员信息、用户管理。"""

from __future__ import annotations

import math

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.app_user import AppUser
from backend.schemas.admin import AdminProfileResponse, AdminUserItem
from backend.schemas.common import PaginatedData


class AdminService:
    """管理员服务。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_admin_profile(self, user_id: str) -> AdminProfileResponse | None:
        """通过用户 ID 获取管理员信息。

        Args:
            user_id: 用户 ID。

        Returns:
            管理员信息，若非管理员则返回 None。
        """
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
        """获取所有用户列表（分页）。

        Args:
            page: 页码（从 1 开始）。
            page_size: 每页条数。
            keyword: 搜索关键词（按用户名模糊匹配）。

        Returns:
            分页的用户列表。
        """
        # 构建查询条件
        base_query = select(AppUser)
        count_query = select(func.count(AppUser.id))

        if keyword:
            like_pattern = f"%{keyword}%"
            base_query = base_query.where(AppUser.username.ilike(like_pattern))
            count_query = count_query.where(AppUser.username.ilike(like_pattern))

        # 总数
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        total_pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size

        # 分页查询
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

    @staticmethod
    def _user_to_item(user: AppUser) -> AdminUserItem:
        return AdminUserItem(
            id=user.id,
            username=user.username,
            email=user.email,
            bio=user.bio or "",
            avatar=user.avatar or "",
            is_online=user.is_online,
            register_time=user.register_time,
            role=user.role,
        )
