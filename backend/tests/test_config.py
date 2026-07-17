"""Settings 配置模型单元测试 —— 只测有逻辑的属性和函数。"""

from __future__ import annotations

from pathlib import Path

from backend.config import REPO_ROOT, Settings, _resolve_path


def test_resolve_path_absolute():
    """绝对路径直接返回。"""
    abs_path = str(REPO_ROOT / "some" / "path")
    assert _resolve_path(abs_path) == abs_path


def test_repo_root_paths():
    """基于 REPO_ROOT 拼接的路径。"""
    s = Settings(YELP_DATASET_DIR="data/ds", YELP_ZIP_PATH="data/z.zip")
    assert s.yelp_dataset_dir == REPO_ROOT / "data/ds"
    assert s.yelp_zip_path == REPO_ROOT / "data/z.zip"


def test_redis_url():
    s = Settings(redis_password="p", redis_host="h", redis_port=6379, redis_db=1)
    assert s.redis_url == "redis://:p@h:6379/1"


def test_mineru_pipeline_model_dir_relative():
    """相对路径时拼接 modelscope_cache_dir。"""
    s = Settings(modelscope_cache_path="cache", mineru_pipeline_model_path="models/p")
    result = s.mineru_pipeline_model_dir
    assert "cache" in result
    assert Path(result).name == "p"


def test_mineru_pipeline_model_dir_absolute():
    """绝对路径时直接返回。"""
    abs_path = str(REPO_ROOT / "abs/pipeline")
    s = Settings(modelscope_cache_path="cache", mineru_pipeline_model_path=abs_path)
    assert Path(s.mineru_pipeline_model_dir) == REPO_ROOT / "abs/pipeline"


def test_opensearch_url():
    s = Settings(opensearch_use_ssl=False, opensearch_host="h", opensearch_port=9200)
    assert s.opensearch_url == "http://h:9200"


def test_opensearch_auth():
    s = Settings(opensearch_user="u", opensearch_password="p")
    assert s.opensearch_auth == ("u", "p")


def test_llm_kwargs():
    s = Settings(
        api_key="k",
        base_url="https://t.com",
        llm_model="m",
        llm_generate_temperature=0.5,
        llm_timeout=30,
        llm_max_retries=1,
    )
    assert s.llm_kwargs == {
        "api_key": "k",
        "base_url": "https://t.com",
        "model": "m",
        "temperature": 0.5,
        "timeout": 30,
        "max_retries": 1,
    }
