"""邮件发送工具 — 使用 smtplib 发送 HTML 邮件。"""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from backend.config import settings

logger = logging.getLogger("backend.core.email")


def send_email(to: str, subject: str, html: str) -> bool:
    """发送 HTML 邮件。

    Args:
        to: 收件人邮箱。
        subject: 邮件主题。
        html: HTML 正文。

    Returns:
        是否发送成功（开发环境无 SMTP 配置时返回 True 并打印到日志）。
    """
    if not settings.SMTP_HOST and not settings.SMTP_USER:
        logger.info(
            "SMTP 未配置，邮件打印到日志：\nTo: %s\nSubject: %s\n%s",
            to,
            subject,
            html,
        )
        return True

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        if settings.SMTP_USE_TLS:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, [to], msg.as_string())
        else:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, [to], msg.as_string())
        logger.info("密码重置邮件已发送至 %s", to)
        return True
    except Exception:
        logger.exception("发送邮件失败 to=%s", to)
        return False
