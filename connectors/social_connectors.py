from __future__ import annotations

from dataclasses import dataclass

from config import settings
from models import PublishedPost


@dataclass
class PublishRequest:
    platform: str
    product_title: str
    text: str


class BaseConnector:
    platform_name: str = "base"

    def is_configured(self) -> bool:
        return False

    def publish(self, request: PublishRequest, dry_run: bool) -> PublishedPost:
        if dry_run:
            return PublishedPost(
                platform=self.platform_name,  # type: ignore[arg-type]
                product_title=request.product_title,
                published=False,
                dry_run=True,
                preview_text=request.text[:280],
                error=None,
            )

        return PublishedPost(
            platform=self.platform_name,  # type: ignore[arg-type]
            product_title=request.product_title,
            published=False,
            dry_run=False,
            preview_text=request.text[:280],
            error="Connector 尚未實作正式 publish。",
        )


class FacebookConnector(BaseConnector):
    platform_name = "facebook"

    def is_configured(self) -> bool:
        return bool(settings.facebook_page_access_token and settings.facebook_page_id)


class InstagramConnector(BaseConnector):
    platform_name = "instagram"

    def is_configured(self) -> bool:
        return bool(settings.facebook_page_access_token and settings.instagram_business_account_id)


class ThreadsConnector(BaseConnector):
    platform_name = "threads"

    def is_configured(self) -> bool:
        return bool(settings.threads_access_token and settings.threads_user_id)
