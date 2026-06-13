from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.request import Request as UrlRequest, urlopen

from config import settings
from models import PipelinePayload


class SlackNotifier:
    def is_configured(self) -> bool:
        return bool(settings.slack_bot_token and settings.slack_channel_id)

    def build_summary_text(self, payload: PipelinePayload) -> str:
        summary = payload.summary
        return (
            f"run_id={payload.run_id}\n"
            f"query={payload.query}\n"
            f"status={summary.status}\n"
            f"scraped={summary.scraped_count}, enriched={summary.enriched_count}, social={summary.social_post_count}\n"
            f"risks={'; '.join(summary.risks) if summary.risks else 'none'}"
        )

    def send(self, payload: PipelinePayload) -> str:
        if not self.is_configured():
            return "略過 Slack 通知，因為尚未設定 SLACK_BOT_TOKEN 或 SLACK_CHANNEL_ID。"
        return "Slack connector 尚未實作正式送出，可先使用 build_summary_text 串接 Slack API。"


class LineNotifier:
    def is_configured(self) -> bool:
        return bool(settings.line_channel_access_token)

    def build_investment_text(
        self,
        title: str,
        summary: str,
        recommendation: str,
        plan_url: str | None = None,
    ) -> str:
        parts = [
            f"{title}",
            "",
            f"重點：{summary}",
            f"本次建議：{recommendation}",
        ]
        if plan_url:
            parts.extend(["", f"查看完整計畫：{plan_url}"])
        return "\n".join(parts)

    def send_push(self, line_user_id: str, text: str) -> str:
        if not self.is_configured():
            return "略過 LINE 推播，因為尚未設定 LINE_CHANNEL_ACCESS_TOKEN。"
        if not line_user_id:
            return "略過 LINE 推播，因為會員尚未綁定 LINE userId。"
        payload = {
            "to": line_user_id,
            "messages": [{"type": "text", "text": text[:5000]}],
        }
        request = UrlRequest(
            "https://api.line.me/v2/bot/message/push",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.line_channel_access_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                status = response.status
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            return f"LINE 推播失敗：HTTP {exc.code} {body}"
        except Exception as exc:
            return f"LINE 推播失敗：{exc}"
        return f"LINE 推播已送出：HTTP {status}"
