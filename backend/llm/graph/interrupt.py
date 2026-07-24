"""Ask rewrite HITL 打断信号。"""

from __future__ import annotations

from typing import Any


class AskInterruptSignal(Exception):
    """rewrite 调用 ask_user_interrupt 后抛出，供 ask() 转为问卷返回。"""

    def __init__(self, questions: list[dict[str, Any]]) -> None:
        self.questions = list(questions or [])
        super().__init__(f"ask interrupt n={len(self.questions)}")
