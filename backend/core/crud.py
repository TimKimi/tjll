"""泛型单例 CRUD 工厂。

为「一个用户一条记录」的资源自动生成 GET / PUT / reset 路由，
支持 flat（直接读写模型属性）和 json（读写 JSON 列内键值）两种模式。
"""

import logging
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Awaitable, Callable, Literal, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.common import ApiResponse

logger = logging.getLogger("backend.core.crud")


@dataclass
class SingletonConfig:
    """单例资源配置。

    Attributes:
        model: ORM 模型类。
        response_schema: 响应 Pydantic 模型。
        update_schema: 更新请求 Pydantic 模型（字段全部 optional，仅传要改的）。
        owner_field: 模型上标识所有者的字段名，默认 ``user_id``。
        owner_id_from: JWT 中取所有者 ID 的 claim，默认 ``sub``。
        data_mode: ``"flat"`` 直接读写模型列；``"json"`` 读写 JSON 列的键值对。
        json_column: ``data_mode="json"`` 时指定 JSON 列名。
        default_factory: 无参可调用对象，返回默认值 dict（GET 无记录用/ reset 时重置到）。
        prefix: 路由前缀，如 ``"/settings"``。
        tags: OpenAPI 标签。
        get: 是否注册 GET 路由。
        update: 是否注册 PUT 路由。
        reset: 是否注册 POST ``{prefix}/reset`` 路由（需提供 ``default_factory``）。
        delete: 是否注册 DELETE 路由。
        on_delete: DELETE 时的回调，参数为 ``(orm_instance, db_session)``，
            用于清理文件等外部资源。
    """

    # ── ORM / Schema ──
    model: type
    response_schema: type[BaseModel]
    update_schema: type[BaseModel] | None = None

    # ── 所有者绑定 ──
    owner_field: str = "user_id"
    owner_id_from: str = "sub"

    # ── 数据模式 ──
    data_mode: Literal["flat", "json"] = "flat"
    json_column: str | None = None
    default_factory: Callable[[], dict[str, Any]] | None = None

    # ── 路由路径 ──
    prefix: str = ""

    # ── OpenAPI 文档 ──
    tags: list[str] | None = None
    summary_get: str = "获取详情"
    summary_update: str = "更新详情"
    summary_reset: str = "重置为默认值"
    summary_delete: str = "删除记录"
    description_get: str = ""
    description_update: str = ""
    description_reset: str = ""
    description_delete: str = ""

    # ── 错误消息（可自定义） ──
    error_not_found: str = "记录不存在"
    error_invalid_data: str = "请求数据无效"

    # ── 回调 ──
    on_delete: Callable[[Any, AsyncSession], Awaitable[None]] | None = None

    # ── 开关 ──
    get: bool = True
    update: bool = True
    reset: bool = False
    delete: bool = False

    def __post_init__(self) -> None:
        if self.data_mode == "json" and not self.json_column:
            raise ValueError("data_mode='json' 必须指定 json_column")
        if self.reset and not self.default_factory:
            raise ValueError("reset=True 必须提供 default_factory")


def register_singleton_routes(
    router: APIRouter,
    config: SingletonConfig,
) -> None:
    """在 ``router`` 上注册单例资源的 GET / PUT / reset / DELETE 路由。"""
    _get_db = _make_db_dep()
    _get_user = _make_auth_dep()
    _tag = config.prefix.strip("/").replace("/", "_")

    # 提取到局部变量，帮助 mypy 闭包类型收窄
    model_cls: type = config.model
    resp_schema: type[BaseModel] = config.response_schema
    upd_schema: type[BaseModel] | None = config.update_schema
    owner_field: str = config.owner_field
    owner_id_from: str = config.owner_id_from
    data_mode: Literal["flat", "json"] = config.data_mode
    json_col: str | None = config.json_column
    factory: Callable[[], dict[str, Any]] | None = config.default_factory
    prefix: str = config.prefix
    tags: list[str | Enum] | None = cast("list[str | Enum] | None", config.tags)
    summary_get: str = config.summary_get
    summary_update: str = config.summary_update
    summary_reset: str = config.summary_reset
    summary_delete: str = config.summary_delete
    desc_get: str = config.description_get
    desc_update: str = config.description_update
    desc_reset: str = config.description_reset
    desc_delete: str = config.description_delete
    err_not_found: str = config.error_not_found
    enable_get: bool = config.get
    enable_update: bool = config.update
    enable_reset: bool = config.reset
    enable_delete: bool = config.delete
    on_delete_cb: Callable[[Any, AsyncSession], Awaitable[None]] | None = (
        config.on_delete
    )

    # ── 构建响应 ─────────────────────────────────────────────
    def _build(obj: Any) -> dict[str, Any]:
        """
        将 ORM 实例转为响应字典。

        - flat 模式：resp_schema.model_validate(obj, from_attributes=True)
          → Pydantic 从 ORM 对象的属性读取字段值，自动映射到同名字段。
        - json 模式：手动从 ORM 对象提取字段，JSON 列的值作为响应 schema
          的对应字段传入（如 settings 字段）。
        """
        if data_mode == "flat":
            return resp_schema.model_validate(obj, from_attributes=True).model_dump()
        assert json_col is not None
        raw = getattr(obj, json_col) or {}
        return resp_schema(
            id=obj.id,
            user_id=obj.user_id,
            **{json_col: raw},
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        ).model_dump()

    # ── GET ──────────────────────────────────────────────────
    if enable_get:

        @router.get(
            prefix,
            summary=summary_get,
            description=desc_get or None,
            response_model=ApiResponse[dict[str, Any]],
            responses={
                404: {"description": err_not_found, "model": ApiResponse},
            },
            tags=tags,
            operation_id=f"get_{_tag}",
        )
        async def _get_route(
            db: AsyncSession = Depends(_get_db),
            current_user: dict[str, Any] = Depends(_get_user),
        ) -> ApiResponse[dict[str, Any]]:
            owner_id = current_user.get(owner_id_from)
            result: Result[Any] = await db.execute(
                select(model_cls).where(getattr(model_cls, owner_field) == owner_id)
            )
            instance = result.scalar_one_or_none()
            if instance:
                return ApiResponse.ok(data=_build(instance))

            # 没有记录但配置了 default_factory → 返回默认值（不写入 DB）
            if factory:
                # resp_schema(**factory())：将默认值 dict 解包为
                # Pydantic 模型的字段，由 Pydantic 自动填充缺失字段的默认值
                if data_mode == "flat":
                    data = resp_schema(**factory()).model_dump()
                else:
                    assert json_col is not None
                    data = resp_schema(**{json_col: factory()}).model_dump()
                return ApiResponse.ok(data=data)
            raise HTTPException(status_code=404, detail=err_not_found)

    # ── PUT ──────────────────────────────────────────────────
    if enable_update and upd_schema is not None:

        @router.put(
            prefix,
            summary=summary_update,
            description=desc_update or None,
            response_model=ApiResponse[dict[str, Any]],
            responses={
                404: {"description": err_not_found, "model": ApiResponse},
                400: {"description": "请求数据无效", "model": ApiResponse},
            },
            tags=tags,
            operation_id=f"put_{_tag}",
        )
        async def _put_route(
            req: upd_schema,  # type: ignore
            db: AsyncSession = Depends(_get_db),
            current_user: dict[str, Any] = Depends(_get_user),
        ) -> ApiResponse[dict[str, Any]]:
            owner_id = current_user.get(owner_id_from)
            result: Result[Any] = await db.execute(
                select(model_cls).where(getattr(model_cls, owner_field) == owner_id)
            )
            instance = result.scalar_one_or_none()

            # req 的类型注解是 upd_schema（Pydantic 模型），
            # FastAPI 启动时读取注解后自动做 JSON 校验与反序列化。
            # model_dump(exclude_none=True) → 只保留请求中显式传了的字段，
            # 排除 None 字段，实现「只更新传了的字段」的语义。
            update_data = req.model_dump(exclude_none=True)  # type: ignore[attr-defined]

            if not instance:
                # 没有现有记录 → 新建
                instance = model_cls(
                    id=uuid.uuid4().hex[:22],
                    **{owner_field: owner_id},
                )
                if data_mode == "flat":
                    # 新建时如果有 default_factory，先合并默认值再写入，
                    # 确保未传的字段也有合理的默认值。
                    if factory:
                        merged = dict(factory())
                        merged.update(update_data)
                        for field, value in merged.items():
                            setattr(instance, field, value)
                    else:
                        for field, value in update_data.items():
                            setattr(instance, field, value)
                else:
                    # json 模式：直接将更新数据赋值给 JSON 列
                    assert json_col is not None
                    setattr(instance, json_col, update_data)
                db.add(instance)
            else:
                if data_mode == "flat":
                    for field, value in update_data.items():
                        setattr(instance, field, value)
                else:
                    # json 模式：读取现有 JSON 列，合并更新
                    assert json_col is not None
                    current = dict(getattr(instance, json_col) or {})
                    current.update(update_data)
                    setattr(instance, json_col, current)

            await db.commit()
            await db.refresh(instance)
            logger.info("配置已更新 owner=%s prefix=%s", owner_id, prefix)
            return ApiResponse.ok(data=_build(instance), message="更新成功")

    # ── POST reset ───────────────────────────────────────────
    if enable_reset and factory is not None:

        @router.post(
            f"{prefix}/reset",
            summary=summary_reset,
            description=desc_reset or None,
            response_model=ApiResponse[dict[str, Any]],
            responses={
                404: {"description": err_not_found, "model": ApiResponse},
            },
            tags=tags,
            operation_id=f"reset_{_tag}",
        )
        async def _reset_route(
            db: AsyncSession = Depends(_get_db),
            current_user: dict[str, Any] = Depends(_get_user),
        ) -> ApiResponse[dict[str, Any]]:
            owner_id = current_user.get(owner_id_from)
            result: Result[Any] = await db.execute(
                select(model_cls).where(getattr(model_cls, owner_field) == owner_id)
            )
            instance = result.scalar_one_or_none()
            defaults = factory()

            if not instance:
                instance = model_cls(
                    id=uuid.uuid4().hex[:22],
                    **{owner_field: owner_id},
                )
                if data_mode == "json":
                    assert json_col is not None
                    setattr(instance, json_col, defaults)
                else:
                    for field, value in defaults.items():
                        setattr(instance, field, value)
                db.add(instance)
            else:
                if data_mode == "json":
                    assert json_col is not None
                    setattr(instance, json_col, defaults)
                else:
                    for field, value in defaults.items():
                        setattr(instance, field, value)

            await db.commit()
            await db.refresh(instance)
            logger.info("配置已重置 owner=%s prefix=%s", owner_id, prefix)
            return ApiResponse.ok(data=_build(instance), message="已重置为默认值")

    # ── DELETE ────────────────────────────────────────────────
    if enable_delete:

        @router.delete(
            prefix,
            summary=summary_delete,
            description=desc_delete or None,
            response_model=ApiResponse,
            responses={
                404: {"description": err_not_found, "model": ApiResponse},
            },
            tags=tags,
            operation_id=f"delete_{_tag}",
        )
        async def _delete_route(
            db: AsyncSession = Depends(_get_db),
            current_user: dict[str, Any] = Depends(_get_user),
        ) -> ApiResponse:
            owner_id = current_user.get(owner_id_from)
            result: Result[Any] = await db.execute(
                select(model_cls).where(getattr(model_cls, owner_field) == owner_id)
            )
            instance = result.scalar_one_or_none()
            if not instance:
                raise HTTPException(status_code=404, detail=err_not_found)

            # on_delete_cb：用户配置的资源清理回调（如删除头像文件、附件目录等）
            if on_delete_cb:
                await on_delete_cb(instance, db)

            await db.delete(instance)
            await db.commit()
            logger.info("记录已删除 owner=%s prefix=%s", owner_id, prefix)
            return ApiResponse.ok(message="已删除")


def _make_db_dep() -> Any:
    """延迟导入 get_db，避免启动时循环依赖。"""
    from backend.database import get_db

    return get_db


def _make_auth_dep() -> Any:
    """延迟导入 get_current_user，避免启动时循环依赖。"""
    from backend.core.dependencies import get_current_user

    return get_current_user
