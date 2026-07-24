"""CRUD 工厂单元测试。

测试路由注册的正确性，不依赖数据库。
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from fastapi import APIRouter
from fastapi.routing import APIRoute

from backend.core.crud import SingletonConfig, register_singleton_routes


class _FakeModel(BaseModel):
    id: str
    name: str


class _FakeResponse(BaseModel):
    id: str
    name: str


class _FakeUpdate(BaseModel):
    name: str | None = None


class _FakeJsonResponse(BaseModel):
    id: str
    user_id: str
    extra: dict = {}
    created_at: str | None = None
    updated_at: str | None = None


class TestSingletonConfig:
    """验证 SingletonConfig 参数校验。"""

    def test_json_mode_requires_json_column(self):
        """data_mode='json' 时必须指定 json_column。"""
        with pytest.raises(ValueError, match="必须指定 json_column"):
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                update_schema=_FakeUpdate,
                owner_field="id",
                data_mode="json",
            )

    def test_reset_requires_default_factory(self):
        """reset=True 时必须提供 default_factory。"""
        with pytest.raises(ValueError, match="reset=True 必须提供 default_factory"):
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                update_schema=_FakeUpdate,
                owner_field="id",
                reset=True,
            )

    def test_json_mode_with_valid_config(self):
        """json 模式 + json_column + factory 合法配置。"""
        cfg = SingletonConfig(
            model=_FakeModel,
            response_schema=_FakeJsonResponse,
            update_schema=_FakeUpdate,
            owner_field="user_id",
            data_mode="json",
            json_column="extra",
            default_factory=lambda: {"theme": "dark"},
        )
        assert cfg.data_mode == "json"
        assert cfg.json_column == "extra"


class TestRegisterSingletonRoutes:
    """验证注册的路由集合是否正确。"""

    def _paths(self, router: APIRouter) -> list[tuple[str, frozenset[str]]]:
        """提取路由的 (path, methods) 列表。"""
        return sorted(
            (r.path, frozenset(r.methods or []))
            for r in router.routes
            if isinstance(r, APIRoute)
        )

    # ── 基本功能 ───────────────────────────────────────────

    def test_get_and_put_only(self):
        """GET + PUT（flat 模式，最常用场景）。"""
        router = APIRouter()
        register_singleton_routes(
            router,
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                update_schema=_FakeUpdate,
                owner_field="id",
                prefix="/profile",
            ),
        )
        assert self._paths(router) == [
            ("/profile", frozenset({"GET"})),
            ("/profile", frozenset({"PUT"})),
        ]

    def test_reset_only(self):
        """注册 reset 路由。"""
        router = APIRouter()
        register_singleton_routes(
            router,
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                update_schema=_FakeUpdate,
                owner_field="id",
                prefix="/settings",
                reset=True,
                default_factory=lambda: {"name": ""},
            ),
        )
        assert self._paths(router) == [
            ("/settings", frozenset({"GET"})),
            ("/settings", frozenset({"PUT"})),
            ("/settings/reset", frozenset({"POST"})),
        ]

    def test_get_and_delete(self):
        """GET + DELETE（无 PUT，如只读+删除的场景）。"""
        router = APIRouter()
        register_singleton_routes(
            router,
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                owner_field="id",
                prefix="/resource",
                update=False,
                delete=True,
            ),
        )
        assert self._paths(router) == [
            ("/resource", frozenset({"GET"})),
            ("/resource", frozenset({"DELETE"})),
        ]

    # ── 只注册一种方法 ─────────────────────────────────────

    def test_delete_only(self):
        """delete=True 且其他全部显式关闭 → 只注册 DELETE。"""
        router = APIRouter()
        register_singleton_routes(
            router,
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                owner_field="id",
                prefix="/account",
                get=False,
                update=False,
                delete=True,
            ),
        )
        assert self._paths(router) == [
            ("/account", frozenset({"DELETE"})),
        ]

    def test_default_get_true_with_delete(self):
        """只设 delete=True 不设 get=False → get=True 仍是默认，同时有 GET 和 DELETE。"""
        router = APIRouter()
        register_singleton_routes(
            router,
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                owner_field="id",
                prefix="/account",
                delete=True,
            ),
        )
        assert self._paths(router) == [
            ("/account", frozenset({"GET"})),
            ("/account", frozenset({"DELETE"})),
        ]

    # ── json 模式 ────────────────────────────────────────

    def test_json_mode_routes(self):
        """json 模式注册 GET + PUT + reset。"""
        router = APIRouter()
        register_singleton_routes(
            router,
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeJsonResponse,
                update_schema=_FakeUpdate,
                owner_field="user_id",
                data_mode="json",
                json_column="extra",
                prefix="/config",
                reset=True,
                default_factory=lambda: {"key": "val"},
            ),
        )
        assert self._paths(router) == [
            ("/config", frozenset({"GET"})),
            ("/config", frozenset({"PUT"})),
            ("/config/reset", frozenset({"POST"})),
        ]

    # ── 多次调用无反重 ─────────────────────────────────────

    def test_multiple_calls_no_duplicates(self):
        """多次调用产生不同的路由，不能有完全相同的 (path, methods)。"""
        router = APIRouter()

        register_singleton_routes(
            router,
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                update_schema=_FakeUpdate,
                owner_field="id",
                prefix="/profile",
            ),
        )
        register_singleton_routes(
            router,
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                update_schema=_FakeUpdate,
                owner_field="id",
                prefix="/settings",
            ),
        )
        register_singleton_routes(
            router,
            SingletonConfig(
                model=_FakeModel,
                response_schema=_FakeResponse,
                owner_field="id",
                prefix="/account",
                get=False,
                update=False,
                delete=True,
            ),
        )

        seen: set[tuple[str, frozenset[str]]] = set()
        for r in router.routes:
            if not isinstance(r, APIRoute):
                continue
            key = (r.path, frozenset(r.methods or []))
            assert key not in seen, f"发现重复路由: {key}"
            seen.add(key)

        assert seen == {
            ("/profile", frozenset({"GET"})),
            ("/profile", frozenset({"PUT"})),
            ("/settings", frozenset({"GET"})),
            ("/settings", frozenset({"PUT"})),
            ("/account", frozenset({"DELETE"})),
        }
