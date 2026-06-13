from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class SchoolPlatformSettings:
    storage_backend: str = "json"
    json_path: str = "data/school_platform_store.json"
    postgres_dsn: str | None = None
    app_base_url: str = "http://127.0.0.1:8000"
    payment_provider: str = "mock"
    payment_currency: str = "jpy"
    stripe_secret_key: str | None = None
    stripe_publishable_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_success_url: str | None = None
    stripe_cancel_url: str | None = None
    email_provider: str = "mock"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = True
    resend_api_key: str | None = None
    resend_from_email: str | None = None
    line_channel_access_token: str | None = None
    line_channel_secret: str | None = None
    line_fallback_user_id: str | None = None


def load_settings() -> SchoolPlatformSettings:
    return SchoolPlatformSettings(
        storage_backend=os.getenv("SCHOOL_PLATFORM_STORAGE_BACKEND", "json").strip().lower(),
        json_path=os.getenv("SCHOOL_PLATFORM_JSON_PATH", "data/school_platform_store.json").strip(),
        postgres_dsn=os.getenv("SCHOOL_PLATFORM_POSTGRES_DSN"),
        app_base_url=os.getenv("SCHOOL_PLATFORM_APP_BASE_URL", os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")).strip(),
        payment_provider=os.getenv("SCHOOL_PLATFORM_PAYMENT_PROVIDER", "mock").strip().lower(),
        payment_currency=os.getenv("SCHOOL_PLATFORM_PAYMENT_CURRENCY", "jpy").strip().lower(),
        stripe_secret_key=os.getenv("SCHOOL_PLATFORM_STRIPE_SECRET_KEY"),
        stripe_publishable_key=os.getenv("SCHOOL_PLATFORM_STRIPE_PUBLISHABLE_KEY"),
        stripe_webhook_secret=os.getenv("SCHOOL_PLATFORM_STRIPE_WEBHOOK_SECRET"),
        stripe_success_url=os.getenv("SCHOOL_PLATFORM_STRIPE_SUCCESS_URL"),
        stripe_cancel_url=os.getenv("SCHOOL_PLATFORM_STRIPE_CANCEL_URL"),
        email_provider=os.getenv("SCHOOL_PLATFORM_EMAIL_PROVIDER", "mock").strip().lower(),
        smtp_host=os.getenv("SCHOOL_PLATFORM_SMTP_HOST"),
        smtp_port=int(os.getenv("SCHOOL_PLATFORM_SMTP_PORT", "587")),
        smtp_username=os.getenv("SCHOOL_PLATFORM_SMTP_USERNAME"),
        smtp_password=os.getenv("SCHOOL_PLATFORM_SMTP_PASSWORD"),
        smtp_from_email=os.getenv("SCHOOL_PLATFORM_SMTP_FROM_EMAIL"),
        smtp_use_tls=os.getenv("SCHOOL_PLATFORM_SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"},
        resend_api_key=os.getenv("SCHOOL_PLATFORM_RESEND_API_KEY"),
        resend_from_email=os.getenv("SCHOOL_PLATFORM_RESEND_FROM_EMAIL"),
        line_channel_access_token=os.getenv("SCHOOL_PLATFORM_LINE_CHANNEL_ACCESS_TOKEN", os.getenv("LINE_CHANNEL_ACCESS_TOKEN")),
        line_channel_secret=os.getenv("SCHOOL_PLATFORM_LINE_CHANNEL_SECRET", os.getenv("LINE_CHANNEL_SECRET")),
        line_fallback_user_id=os.getenv("SCHOOL_PLATFORM_LINE_FALLBACK_USER_ID"),
    )
