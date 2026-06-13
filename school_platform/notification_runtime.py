from __future__ import annotations

from email.message import EmailMessage
import smtplib
from typing import Any

import httpx

from school_platform.config import SchoolPlatformSettings, load_settings


class SchoolPlatformNotificationRuntime:
    def __init__(self, settings: SchoolPlatformSettings | None = None) -> None:
        self.settings = settings or load_settings()

    def status(self) -> dict[str, Any]:
        email_provider = self._active_email_provider()
        email_ready = email_provider == "mock" or (
            email_provider == "smtp" and bool(self.settings.smtp_host and self.settings.smtp_from_email)
        ) or (
            email_provider == "resend" and bool(self.settings.resend_api_key and self.settings.resend_from_email)
        )
        line_ready = bool(self.settings.line_channel_access_token)
        return {
            "email_provider": email_provider,
            "email_ready": email_ready,
            "smtp_host_present": bool(self.settings.smtp_host),
            "smtp_from_email_present": bool(self.settings.smtp_from_email),
            "resend_api_key_present": bool(self.settings.resend_api_key),
            "resend_from_email_present": bool(self.settings.resend_from_email),
            "line_ready": line_ready,
            "line_channel_access_token_present": bool(self.settings.line_channel_access_token),
            "line_channel_secret_present": bool(self.settings.line_channel_secret),
            "line_fallback_user_id_present": bool(self.settings.line_fallback_user_id),
            "message": self._status_message(email_provider, email_ready, line_ready),
        }

    def _status_message(self, email_provider: str, email_ready: bool, line_ready: bool) -> str:
        email_label = f"{email_provider}:{'ready' if email_ready else 'not_ready'}"
        line_label = f"line:{'ready' if line_ready else 'not_ready'}"
        return f"Email {email_label} / LINE {line_label}"

    def _active_email_provider(self) -> str:
        provider = self.settings.email_provider
        if provider == "auto":
            if self.settings.resend_api_key and self.settings.resend_from_email:
                return "resend"
            if self.settings.smtp_host and self.settings.smtp_from_email:
                return "smtp"
            return "mock"
        return provider

    def dispatch(
        self,
        *,
        channel: str,
        title: str,
        content: str,
        recipient: str | None,
        user_email: str | None,
    ) -> dict[str, Any]:
        if channel == "in_app":
            return {
                "status": "queued",
                "provider": "in_app",
                "provider_message_id": None,
                "error_message": None,
                "external_recipient": recipient,
            }
        if channel == "email":
            return self._dispatch_email(title=title, content=content, recipient=recipient or user_email)
        if channel == "line":
            return self._dispatch_line(title=title, content=content, recipient=recipient or self.settings.line_fallback_user_id)
        return {
            "status": "failed",
            "provider": "unsupported",
            "provider_message_id": None,
            "error_message": f"Unsupported channel: {channel}",
            "external_recipient": recipient,
        }

    def _dispatch_email(self, *, title: str, content: str, recipient: str | None) -> dict[str, Any]:
        provider = self._active_email_provider()
        if not recipient:
            return {
                "status": "failed",
                "provider": provider,
                "provider_message_id": None,
                "error_message": "Missing email recipient.",
                "external_recipient": None,
            }
        if provider == "mock":
            return {
                "status": "queued",
                "provider": "mock",
                "provider_message_id": None,
                "error_message": "Email provider is mock; no external delivery was attempted.",
                "external_recipient": recipient,
            }
        if provider == "resend":
            headers = {
                "Authorization": f"Bearer {self.settings.resend_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "from": self.settings.resend_from_email,
                "to": [recipient],
                "subject": title,
                "text": content,
            }
            response = httpx.post("https://api.resend.com/emails", headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            body = response.json()
            return {
                "status": "sent",
                "provider": "resend",
                "provider_message_id": body.get("id"),
                "error_message": None,
                "external_recipient": recipient,
            }
        if provider == "smtp":
            if not self.settings.smtp_host or not self.settings.smtp_from_email:
                return {
                    "status": "failed",
                    "provider": "smtp",
                    "provider_message_id": None,
                    "error_message": "SMTP settings are incomplete.",
                    "external_recipient": recipient,
                }
            message = EmailMessage()
            message["Subject"] = title
            message["From"] = self.settings.smtp_from_email
            message["To"] = recipient
            message.set_content(content)
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as client:
                if self.settings.smtp_use_tls:
                    client.starttls()
                if self.settings.smtp_username and self.settings.smtp_password:
                    client.login(self.settings.smtp_username, self.settings.smtp_password)
                client.send_message(message)
            return {
                "status": "sent",
                "provider": "smtp",
                "provider_message_id": None,
                "error_message": None,
                "external_recipient": recipient,
            }
        return {
            "status": "failed",
            "provider": provider,
            "provider_message_id": None,
            "error_message": f"Unknown email provider: {provider}",
            "external_recipient": recipient,
        }

    def _dispatch_line(self, *, title: str, content: str, recipient: str | None) -> dict[str, Any]:
        if not self.settings.line_channel_access_token:
            return {
                "status": "queued",
                "provider": "line",
                "provider_message_id": None,
                "error_message": "LINE channel access token is missing.",
                "external_recipient": recipient,
            }
        if not recipient:
            return {
                "status": "failed",
                "provider": "line",
                "provider_message_id": None,
                "error_message": "Missing LINE userId / external recipient.",
                "external_recipient": None,
            }
        payload = {
            "to": recipient,
            "messages": [
                {
                    "type": "text",
                    "text": f"{title}\n\n{content}"[:5000],
                }
            ],
        }
        response = httpx.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Authorization": f"Bearer {self.settings.line_channel_access_token}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        return {
            "status": "sent",
            "provider": "line",
            "provider_message_id": response.headers.get("x-line-request-id"),
            "error_message": None,
            "external_recipient": recipient,
        }
