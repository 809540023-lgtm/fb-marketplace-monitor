from __future__ import annotations

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_research_model: str = os.getenv("OPENAI_RESEARCH_MODEL", "gpt-4.1-mini")

    apify_api_token: str | None = os.getenv("APIFY_API_TOKEN")
    apify_actor_id: str = os.getenv("APIFY_ACTOR_ID", "apify/facebook-marketplace-scraper")
    free_mode: bool = _as_bool(os.getenv("FREE_MODE"), default=False)

    supabase_url: str | None = os.getenv("SUPABASE_URL")
    supabase_service_role_key: str | None = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    default_location_name: str = os.getenv("DEFAULT_LOCATION_NAME", "New Taipei City,Taipei,Taoyuan")
    default_query: str = os.getenv("DEFAULT_QUERY", "二手 生財 餐飲 器具")
    default_max_results: int = int(os.getenv("DEFAULT_MAX_RESULTS", "3"))

    publish_enabled: bool = _as_bool(os.getenv("PUBLISH_ENABLED"), default=False)
    publish_dry_run: bool = _as_bool(os.getenv("PUBLISH_DRY_RUN"), default=True)
    facebook_page_access_token: str | None = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    facebook_page_id: str | None = os.getenv("FACEBOOK_PAGE_ID")
    instagram_business_account_id: str | None = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    threads_access_token: str | None = os.getenv("THREADS_ACCESS_TOKEN")
    threads_user_id: str | None = os.getenv("THREADS_USER_ID")

    slack_bot_token: str | None = os.getenv("SLACK_BOT_TOKEN")
    slack_channel_id: str | None = os.getenv("SLACK_CHANNEL_ID")
    line_channel_access_token: str | None = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_official_account_url: str | None = os.getenv("LINE_OFFICIAL_ACCOUNT_URL")

    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    schedule_timezone: str = os.getenv("SCHEDULE_TIMEZONE", "Asia/Taipei")
    daytime_start_hour: int = int(os.getenv("DAYTIME_START_HOUR", "8"))
    nighttime_start_hour: int = int(os.getenv("NIGHTTIME_START_HOUR", "23"))
    night_run_hours: str = os.getenv("NIGHT_RUN_HOURS", "2,5")
    google_service_account_json: str | None = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    google_drive_root_folder_name: str = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_NAME", "agai2_new")
    google_drive_root_folder_id: str | None = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID", "1vi-gnzBXz_3Oo_HkrXw8x_Kp6bqajlyH")
    inventory_contact_phone: str = os.getenv("INVENTORY_CONTACT_PHONE", "0915888927")

    def timezone_info(self) -> ZoneInfo:
        return ZoneInfo(self.schedule_timezone)


settings = Settings()
