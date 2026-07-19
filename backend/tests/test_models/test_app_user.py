"""AppUser 模型单元测试（不需要数据库连接）。

注意：SQLAlchemy 中 mapped_column(default=...) 是数据库级默认值，
Python 构造时不传参的属性值为 None，不是 default 值。
"""

from __future__ import annotations

from sqlalchemy import Boolean, DateTime, String

from backend.models.app_user import AppUser


class TestAppUserRepr:
    """测试 AppUser 模型的 __repr__ 方法。"""

    def test_repr_contains_id_and_username(self):
        """__repr__ 应包含 id 和 username。"""
        user = AppUser(id="u_test_001", username="测试用户")
        r = repr(user)
        assert "AppUser" in r
        assert "u_test_001" in r
        assert "测试用户" in r


class TestAppUserColumns:
    """测试 AppUser 模型的列定义（不依赖 Python 构造函数默认值）。"""

    def test_id_is_primary_key(self):
        """id 字段应是主键 String(22)。"""
        col = AppUser.__table__.c["id"]
        assert col.primary_key is True
        assert isinstance(col.type, String)
        assert col.type.length == 22

    def test_username_is_unique_and_indexed(self):
        """username 字段应是唯一索引。"""
        col = AppUser.__table__.c["username"]
        assert col.unique is True
        assert col.index is True
        assert isinstance(col.type, String)
        assert col.type.length == 255

    def test_password_hash_not_nullable(self):
        """password_hash 字段不可为空。"""
        col = AppUser.__table__.c["password_hash"]
        assert col.nullable is False
        assert isinstance(col.type, String)
        assert col.type.length == 255

    def test_role_column_type_and_default(self):
        """role 字段应为 String(16)，默认 'user'。"""
        col = AppUser.__table__.c["role"]
        assert isinstance(col.type, String)
        assert col.type.length == 16
        assert col.default is not None and col.default.arg == "user"

    def test_is_online_column_type_and_default(self):
        """is_online 字段应为 Boolean，默认 True。"""
        col = AppUser.__table__.c["is_online"]
        assert isinstance(col.type, Boolean)
        assert col.default is not None and col.default.arg is True

    def test_register_time_has_server_default(self):
        """register_time 字段应有 server_default。"""
        col = AppUser.__table__.c["register_time"]
        assert col.server_default is not None
        assert isinstance(col.type, DateTime)

    def test_optional_string_fields_nullable(self):
        """email、bio、avatar 可为空。"""
        for field in ["email", "bio", "avatar"]:
            col = AppUser.__table__.c[field]
            assert col.nullable is True, f"{field} should be nullable"

    def test_email_default_to_empty_string(self):
        """email 字段默认值为空字符串。"""
        col = AppUser.__table__.c["email"]
        assert col.default is not None and col.default.arg == ""

    def test_bio_default_to_empty_string(self):
        """bio 字段默认值为空字符串。"""
        col = AppUser.__table__.c["bio"]
        assert col.default is not None and col.default.arg == ""

    def test_avatar_default_to_empty_string(self):
        """avatar 字段默认值为空字符串。"""
        col = AppUser.__table__.c["avatar"]
        assert col.default is not None and col.default.arg == ""


class TestAppUserCreate:
    """测试通过构造函数创建 AppUser 实例。"""

    def test_create_with_minimal_fields(self):
        """仅用必填字段创建用户。"""
        user = AppUser(id="u_min", username="min_user", password_hash="abc123")
        assert user.id == "u_min"
        assert user.username == "min_user"
        assert user.password_hash == "abc123"

    def test_create_with_all_fields(self):
        """使用所有字段创建用户。"""
        from datetime import datetime

        user = AppUser(
            id="u_full",
            username="full_user",
            password_hash="hashed_pw",
            email="test@example.com",
            bio="热爱美食",
            avatar="https://example.com/avatar.jpg",
            is_online=False,
            role="admin",
            register_time=datetime(2026, 7, 19, 14, 30, 0),
        )
        assert user.email == "test@example.com"
        assert user.bio == "热爱美食"
        assert user.role == "admin"
        assert user.is_online is False
