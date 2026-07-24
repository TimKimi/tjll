"""FileService 单元测试。"""

from __future__ import annotations
from unittest.mock import patch


from backend.services.file import FileService


class TestFileServiceDelete:
    """测试 FileService 文件删除方法。"""

    def test_delete_session_files_empty_username(self):
        """空 username 应直接返回。"""
        with patch("backend.services.file.logger") as mock_log:
            FileService.delete_session_files("", "sid")
            mock_log.info.assert_not_called()

    def test_delete_session_files_empty_section_id(self):
        """空 section_id 应直接返回。"""
        with patch("backend.services.file.logger") as mock_log:
            FileService.delete_session_files("user", "")
            mock_log.info.assert_not_called()

    @patch("shutil.rmtree")
    @patch("backend.services.file.Path.exists", return_value=True)
    def test_delete_session_files_deletes_dir(self, mock_exists, mock_rmtree):
        """目录存在时应删除。"""
        FileService.delete_session_files("user", "sid")
        mock_rmtree.assert_called_once()

    @patch("shutil.rmtree")
    @patch("backend.services.file.Path.exists", return_value=False)
    def test_delete_session_files_not_exists(self, mock_exists, mock_rmtree):
        """目录不存在时应跳过。"""
        FileService.delete_session_files("user", "sid")
        mock_rmtree.assert_not_called()

    def test_delete_all_user_files_empty_username(self):
        """空 username 应直接返回。"""
        with patch("backend.services.file.logger") as mock_log:
            FileService.delete_all_user_files("")
            mock_log.info.assert_not_called()

    @patch("shutil.rmtree")
    @patch("backend.services.file.Path.exists", return_value=True)
    def test_delete_all_user_files_deletes_dir(self, mock_exists, mock_rmtree):
        """目录存在时应删除。"""
        FileService.delete_all_user_files("user")
        mock_rmtree.assert_called_once()

    @patch("backend.llm.load_section_document", side_effect=Exception("test"))
    @patch("backend.services.file.logger")
    def test_load_doc_silent_on_failure(self, mock_log, mock_load):
        """_load_doc 在 load_section_document 失败时不应抛异常。"""
        from backend.services.file import FileService

        FileService._load_doc("u_abc", "sid", "./backend/static/file/test.md")
        mock_log.warning.assert_called_once()

    @patch("backend.llm.load_section_document")
    def test_load_doc_calls_llm(self, mock_load):
        """_load_doc 应调 load_section_document。"""
        from backend.services.file import FileService

        FileService._load_doc("u_abc", "sid", "./backend/static/file/test.md")
        mock_load.assert_called_once_with(
            "u_abc", "sid", "./backend/static/file/test.md"
        )
