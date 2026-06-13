from __future__ import annotations

from models import PublishedPost, SocialPostPack


class SocialPublisherService:
    def __init__(self, publish_enabled: bool, dry_run: bool = True) -> None:
        self.publish_enabled = publish_enabled
        self.dry_run = dry_run

    def publish_posts(self, posts: list[SocialPostPack], publish_requested: bool) -> list[PublishedPost]:
        results: list[PublishedPost] = []

        for post in posts:
            results.append(
                self._draft(
                    platform="facebook",
                    product_title=post.product_title,
                    text=post.facebook_post,
                )
            )
            results.append(
                self._draft(
                    platform="instagram",
                    product_title=post.product_title,
                    text=f"{post.instagram_post}\n\n{' '.join(post.hashtags)}".strip(),
                )
            )
            results.append(
                self._draft(
                    platform="threads",
                    product_title=post.product_title,
                    text=post.threads_post,
                )
            )

        return results

    def _draft(self, platform: str, product_title: str, text: str) -> PublishedPost:
        return PublishedPost(
            platform=platform,  # type: ignore[arg-type]
            product_title=product_title,
            published=False,
            dry_run=True,
            preview_text=text[:280],
            error=None,
        )
