"""Favorite 模型单元测试（不需要数据库连接）。"""

from __future__ import annotations

from sqlalchemy import DateTime, String

from backend.models.favorite import Favorite


class TestFavoriteRepr:
    """测试 Favorite 模型的 __repr__ 方法。"""

    def test_repr_contains_id_and_shop_id(self):
        """__repr__ 应包含 id、user_id 和 shop_id。"""
        fav = Favorite(id="fav_001", user_id="u_abc", shop_id="biz_001")
        r = repr(fav)
        assert "Favorite" in r
        assert "fav_001" in r
        assert "u_abc" in r
        assert "biz_001" in r


class TestFavoriteColumns:
    """测试 Favorite 模型的列定义。"""

    def test_id_is_primary_key(self):
        """id 字段应是主键 String(22)。"""
        col = Favorite.__table__.c["id"]
        assert col.primary_key is True
        assert isinstance(col.type, String)
        assert col.type.length == 22

    def test_user_id_is_foreign_key(self):
        """user_id 字段应有外键约束。"""
        col = Favorite.__table__.c["user_id"]
        assert isinstance(col.type, String)
        assert col.type.length == 22
        assert col.index is True
        # 检查是否有外键
        fks = [fk for fk in col.foreign_keys]
        assert len(fks) == 1
        assert "app_users.id" in str(fks[0].target_fullname)

    def test_shop_id_is_indexed(self):
        """shop_id 字段应有索引。"""
        col = Favorite.__table__.c["shop_id"]
        assert isinstance(col.type, String)
        assert col.type.length == 22
        assert col.index is True

    def test_created_at_has_server_default(self):
        """created_at 字段应有 server_default。"""
        col = Favorite.__table__.c["created_at"]
        assert col.server_default is not None
        assert isinstance(col.type, DateTime)

    def test_user_id_ondelete_cascade(self):
        """user_id 的外键应配置 CASCADE 删除。"""
        col = Favorite.__table__.c["user_id"]
        for fk in col.foreign_keys:
            assert fk.ondelete == "CASCADE"


class TestFavoriteCreate:
    """测试通过构造函数创建 Favorite 实例。"""

    def test_create_with_minimal_fields(self):
        """仅用必填字段创建收藏记录。"""
        fav = Favorite(id="fav_001", user_id="u_abc", shop_id="biz_001")
        assert fav.id == "fav_001"
        assert fav.user_id == "u_abc"
        assert fav.shop_id == "biz_001"

    def test_create_with_all_fields(self):
        """使用所有字段创建收藏记录。"""
        from datetime import datetime

        fav = Favorite(
            id="fav_002",
            user_id="u_def",
            shop_id="biz_002",
            created_at=datetime(2026, 7, 19, 15, 0, 0),
        )
        assert fav.shop_id == "biz_002"
        assert fav.created_at == datetime(2026, 7, 19, 15, 0, 0)
