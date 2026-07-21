"""通用响应模型和分页模型的单元测试。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.schemas.common import ApiResponse, PaginatedData, PaginationParams


class TestApiResponse:
    """测试统一响应格式 ApiResponse。"""

    def test_ok_without_data(self):
        resp = ApiResponse.ok()
        assert resp.code == 200
        assert resp.message == "success"
        assert resp.data is None

    def test_ok_with_data(self):
        data = {"key": "value"}
        resp = ApiResponse.ok(data=data)
        assert resp.code == 200
        assert resp.message == "success"
        assert resp.data == data

    def test_ok_with_custom_message(self):
        resp = ApiResponse.ok(message="自定义成功")
        assert resp.code == 200
        assert resp.message == "自定义成功"
        assert resp.data is None

    def test_fail_default(self):
        resp = ApiResponse.fail()
        assert resp.code == 400
        assert resp.message == "error"
        assert resp.data is None

    def test_fail_custom(self):
        resp = ApiResponse.fail(code=404, message="资源未找到")
        assert resp.code == 404
        assert resp.message == "资源未找到"
        assert resp.data is None

    def test_direct_instantiation(self):
        resp = ApiResponse(code=1, message="自定义错误", data={"id": 1})
        assert resp.code == 1
        assert resp.data == {"id": 1}

    def test_generic_with_different_types(self):
        resp_int = ApiResponse.ok(data=[1, 2, 3])
        assert resp_int.data == [1, 2, 3]
        resp_str = ApiResponse.ok(data="hello")
        assert resp_str.data == "hello"


class TestPaginationParams:
    """测试分页参数模型 PaginationParams。"""

    def test_defaults(self):
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 10

    def test_valid_values(self):
        params = PaginationParams(page=5, page_size=20)
        assert params.page == 5
        assert params.page_size == 20

    def test_page_ge_1(self):
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

    def test_page_size_ge_1(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

    def test_page_size_le_100(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)

    def test_page_size_boundary_values(self):
        params_min = PaginationParams(page_size=1)
        assert params_min.page_size == 1
        params_max = PaginationParams(page_size=100)
        assert params_max.page_size == 100


class TestPaginatedData:
    """测试分页数据模型 PaginatedData。"""

    def test_instantiation(self):
        data = PaginatedData(
            items=[1, 2, 3],
            total=10,
            page=2,
            page_size=5,
            total_pages=2,
        )
        assert data.items == [1, 2, 3]
        assert data.total == 10
        assert data.page == 2
        assert data.page_size == 5
        assert data.total_pages == 2

    def test_with_string_items(self):
        data = PaginatedData(
            items=["a", "b"], total=2, page=1, page_size=10, total_pages=1
        )
        assert data.items == ["a", "b"]

    def test_with_complex_objects(self):
        data = PaginatedData(
            items=[{"id": 1}, {"id": 2}], total=2, page=1, page_size=10, total_pages=1
        )
        assert data.items == [{"id": 1}, {"id": 2}]

    def test_empty_items(self):
        data = PaginatedData(items=[], total=0, page=1, page_size=10, total_pages=0)
        assert data.items == []
        assert data.total == 0
        assert data.total_pages == 0
