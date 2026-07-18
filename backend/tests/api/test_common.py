# backend/tests/api/test_common.py
"""通用响应模型和分页模型的单元测试。"""

import pytest
from pydantic import ValidationError

from backend.schemas.common import ApiResponse, PaginatedData, PaginationParams


class TestApiResponse:
    """测试统一响应格式 ApiResponse。"""

    def test_ok_without_data(self):
        """测试成功响应无数据。"""
        resp = ApiResponse.ok()
        assert resp.code == 0
        assert resp.message == "success"
        assert resp.data is None

    def test_ok_with_data(self):
        """测试成功响应携带数据。"""
        data = {"key": "value"}
        resp = ApiResponse.ok(data=data)
        assert resp.code == 0
        assert resp.message == "success"
        assert resp.data == data

    def test_ok_with_custom_message(self):
        """测试成功响应自定义消息。"""
        resp = ApiResponse.ok(message="自定义成功")
        assert resp.code == 0
        assert resp.message == "自定义成功"
        assert resp.data is None

    def test_ok_with_data_and_message(self):
        """测试成功响应同时携带数据和自定义消息。"""
        resp = ApiResponse.ok(data=[1, 2, 3], message="操作成功")
        assert resp.code == 0
        assert resp.message == "操作成功"
        assert resp.data == [1, 2, 3]

    def test_fail_default(self):
        """测试失败响应默认值。"""
        resp = ApiResponse.fail()
        assert resp.code == 400
        assert resp.message == "error"
        assert resp.data is None

    def test_fail_custom(self):
        """测试失败响应自定义状态码和消息。"""
        resp = ApiResponse.fail(code=404, message="资源未找到")
        assert resp.code == 404
        assert resp.message == "资源未找到"
        assert resp.data is None

    def test_fail_with_data_override(self):
        """测试 fail 方法虽然通常 data=None，但类本身允许 data 非空（不推荐，但测试灵活性）。"""
        resp = ApiResponse.fail(code=500, message="服务器错误")
        # fail 返回 data=None，但我们也可以手动构造
        # 这里仅验证 fail 方法的行为
        assert resp.data is None

    def test_direct_instantiation(self):
        """测试直接实例化模型。"""
        resp = ApiResponse(code=1, message="自定义错误", data={"id": 1})
        assert resp.code == 1
        assert resp.message == "自定义错误"
        assert resp.data == {"id": 1}

    def test_generic_with_different_types(self):
        """测试泛型支持不同数据类型。"""
        # int 列表
        resp_int = ApiResponse.ok(data=[1, 2, 3])
        assert resp_int.data == [1, 2, 3]

        # 字符串
        resp_str = ApiResponse.ok(data="hello")
        assert resp_str.data == "hello"

        # None
        resp_none = ApiResponse.ok(data=None)
        assert resp_none.data is None

        # 嵌套对象
        resp_obj = ApiResponse.ok(data={"name": "test", "value": 42})
        assert resp_obj.data == {"name": "test", "value": 42}


class TestPaginationParams:
    """测试分页参数模型 PaginationParams。"""

    def test_defaults(self):
        """测试默认值。"""
        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 10

    def test_valid_values(self):
        """测试合法传入值。"""
        params = PaginationParams(page=5, page_size=20)
        assert params.page == 5
        assert params.page_size == 20

    def test_page_ge_1(self):
        """测试 page 小于 1 时触发验证错误。"""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(page=0)
        errors = exc_info.value.errors()
        assert any("page" in err["loc"] for err in errors)

    def test_page_size_ge_1(self):
        """测试 page_size 小于 1 时触发验证错误。"""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(page_size=0)
        errors = exc_info.value.errors()
        assert any("page_size" in err["loc"] for err in errors)

    def test_page_size_le_100(self):
        """测试 page_size 大于 100 时触发验证错误。"""
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(page_size=101)
        errors = exc_info.value.errors()
        assert any("page_size" in err["loc"] for err in errors)

    def test_page_size_boundary_values(self):
        """测试 page_size 边界值 1 和 100。"""
        params_min = PaginationParams(page_size=1)
        assert params_min.page_size == 1

        params_max = PaginationParams(page_size=100)
        assert params_max.page_size == 100


class TestPaginatedData:
    """测试分页数据模型 PaginatedData。"""

    def test_instantiation(self):
        """测试正常实例化。"""
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
        """测试字符串列表项。"""
        data = PaginatedData(
            items=["a", "b"],
            total=2,
            page=1,
            page_size=10,
            total_pages=1,
        )
        assert data.items == ["a", "b"]

    def test_with_complex_objects(self):
        """测试复杂对象（字典）作为项。"""
        data = PaginatedData(
            items=[{"id": 1}, {"id": 2}],
            total=2,
            page=1,
            page_size=10,
            total_pages=1,
        )
        assert data.items == [{"id": 1}, {"id": 2}]

    def test_empty_items(self):
        """测试空列表。"""
        data = PaginatedData(
            items=[],
            total=0,
            page=1,
            page_size=10,
            total_pages=0,
        )
        assert data.items == []
        assert data.total == 0
        assert data.total_pages == 0

    def test_no_validation_restrictions(self):
        """测试 PaginatedData 本身没有字段验证限制（如 total 可为负数？不，它只是 int，但未加 ge 约束）。"""
        # 可以实例化，但实际业务中 total 不应为负，但模型未限制，这里仅测试无额外校验。
        data = PaginatedData(
            items=[],
            total=-1,
            page=0,  # 即使 page=0 也允许，因为模型未加 ge
            page_size=0,
            total_pages=-1,
        )
        # 只测试字段存在性，不测试值合法性
        assert data.total == -1
        assert data.page == 0
