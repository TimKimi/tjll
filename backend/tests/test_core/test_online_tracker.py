"""OnlineTracker 单元测试。"""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import MagicMock, patch

from backend.core.online_tracker import _OnlineTracker


class TestOnlineTracker:
    """测试在线追踪器核心逻辑。"""

    def setup_method(self):
        self.tracker = _OnlineTracker()

    def test_mark_online_adds_user(self):
        """mark_online 应记录用户过期时间。"""
        self.tracker.mark_online("u_abc", timedelta(minutes=60))
        with self.tracker._lock:
            assert "u_abc" in self.tracker._users
            assert self.tracker._users["u_abc"] > 0

    def test_mark_offline_removes_user(self):
        """mark_offline 应移除用户记录。"""
        self.tracker.mark_online("u_abc", timedelta(minutes=60))
        self.tracker.mark_offline("u_abc")
        with self.tracker._lock:
            assert "u_abc" not in self.tracker._users

    def test_mark_offline_nonexistent_user(self):
        """移除不存在的用户不应报错。"""
        self.tracker.mark_offline("u_nonexistent")  # 不应抛异常

    def test_check_expired_removes_expired(self):
        """过期用户应被移除并返回。"""
        self.tracker.mark_online("u_expired", timedelta(days=-1))
        self.tracker.mark_online("u_valid", timedelta(hours=1))
        self.tracker._check_expired()
        with self.tracker._lock:
            assert "u_expired" not in self.tracker._users
            assert "u_valid" in self.tracker._users

    def test_check_expired_no_expired(self):
        """没有过期用户时不应执行同步。"""
        self.tracker.mark_online("u_valid", timedelta(hours=1))
        with patch.object(self.tracker, "_sync_offline") as mock_sync:
            self.tracker._check_expired()
            mock_sync.assert_not_called()

    @patch("backend.core.online_tracker._OnlineTracker._sync_offline")
    def test_check_expired_calls_sync(self, mock_sync):
        """有过期用户时应调 _sync_offline。"""
        self.tracker.mark_online("u_expired", timedelta(days=-1))
        self.tracker._check_expired()
        mock_sync.assert_called_once_with(["u_expired"])

    @patch("backend.core.online_tracker.settings")
    @patch("backend.core.online_tracker.create_engine")
    def test_start_creates_engine_and_resets(self, mock_create_engine, mock_settings):
        """start() 应创建引擎并重置所有用户离线。"""
        mock_settings.ONLINE_TRACKER_RESET_ON_STARTUP = True
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        with patch.object(self.tracker, "_reset_all_online") as mock_reset:
            self.tracker.start()
            assert self.tracker._engine is not None
            mock_reset.assert_called_once()
            self.tracker.stop()

    @patch("backend.core.online_tracker.settings")
    def test_double_start_ignored(self, mock_settings):
        """重复 start() 应被忽略。"""
        mock_settings.ONLINE_TRACKER_RESET_ON_STARTUP = True
        with patch.object(self.tracker, "_reset_all_online") as mock_reset:
            self.tracker.start()
            self.tracker.start()
            mock_reset.assert_called_once()
            self.tracker.stop()

    def test_stop_flushes_all(self):
        """stop() 应清空所有追踪用户。"""
        self.tracker.mark_online("u_abc", timedelta(minutes=60))
        with patch.object(self.tracker, "_flush_all") as mock_flush:
            self.tracker.stop()
            mock_flush.assert_called_once()

    @patch("backend.core.online_tracker._OnlineTracker._sync_offline")
    def test_flush_all_syncs_remaining(self, mock_sync):
        """_flush_all 应同步剩余用户。"""
        self.tracker.mark_online("u_abc", timedelta(hours=1))
        self.tracker._flush_all()
        with self.tracker._lock:
            assert self.tracker._users == {}
        mock_sync.assert_called_once_with(["u_abc"])
