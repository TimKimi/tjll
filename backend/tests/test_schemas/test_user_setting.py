"""用户设置 Schema 单元测试。"""

from __future__ import annotations

from backend.schemas.user_setting import (
    UserSettingResponse,
    UserSettingUpdateRequest,
)


class TestUserSettingResponse:
    """测试用户设置响应 Schema。"""

    def test_minimal(self):
        resp = UserSettingResponse()
        assert resp.id == ""
        assert resp.user_id == ""
        assert resp.insight_create is False
        assert resp.insight_use is False
        assert resp.created_at is None
        assert resp.updated_at is None

    def test_with_values(self):
        from datetime import datetime

        dt = datetime(2026, 7, 19, 14, 30, 0)
        resp = UserSettingResponse(
            id="s_abc",
            user_id="u_abc",
            insight_create=True,
            insight_use=False,
            created_at=dt,
            updated_at=dt,
        )
        assert resp.id == "s_abc"
        assert resp.insight_create is True
        assert resp.insight_use is False

    def test_extra_fields_ignored(self):
        resp = UserSettingResponse.model_validate({"unknown_field": "x"})
        assert resp.insight_create is False


class TestUserSettingUpdateRequest:
    """测试更新用户设置请求 Schema。"""

    def test_all_optional(self):
        req = UserSettingUpdateRequest()
        assert req.insight_create is None
        assert req.insight_use is None

    def test_partial_update(self):
        req = UserSettingUpdateRequest(insight_create=True)
        assert req.insight_create is True
        assert req.insight_use is None

    def test_extra_fields_ignored(self):
        req = UserSettingUpdateRequest(**{"unknown": 1, "insight_create": False})
        assert req.insight_create is False
        assert not hasattr(req, "unknown")
