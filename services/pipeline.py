from __future__ import annotations

import json
import uuid

from connectors import SlackNotifier
from config import settings
from models import EnrichedItem, MarketplaceItem, MonitorSummary, PipelinePayload, PipelineRunResponse, SocialPostPack
from tools import DBMonitorTool, FBMarketplaceTool, OfficialProductResearchTool
from utils.json_parser import StructuredOutputError, dump_model_list, parse_model_list


class PipelineService:
    def __init__(self) -> None:
        self.notifier = SlackNotifier()
        self.scraper_tool = FBMarketplaceTool()
        self.research_tool = OfficialProductResearchTool()

    def run(self, query: str, location: str, max_results: int, publish: bool = False) -> PipelineRunResponse:
        run_id = uuid.uuid4().hex

        scraped_items, scrape_error = self._scrape(query=query, location=location, max_results=max_results)
        enriched_items, enrich_error, cost_metrics = self._enrich(scraped_items)
        social_posts: list[SocialPostPack] = []
        creative_error = None
        summary = self._build_summary(
            scraped_items,
            enriched_items,
            social_posts,
            scrape_error,
            enrich_error,
            creative_error,
            cost_metrics,
        )
        published_posts = []

        payload = PipelinePayload(
            run_id=run_id,
            query=query,
            scraped_items=scraped_items,
            enriched_items=enriched_items,
            social_posts=social_posts,
            published_posts=published_posts,
            summary=summary,
        )

        self._persist_payload(payload)
        self.notifier.send(payload)

        return PipelineRunResponse(
            run_id=run_id,
            query=query,
            location=location,
            max_results=max_results,
            payload=payload,
        )

    def _scrape(self, query: str, location: str, max_results: int) -> tuple[list[MarketplaceItem], str | None]:
        try:
            raw = self.scraper_tool._run(query=query, max_results=max_results, location_name=location)
            items = parse_model_list(raw, MarketplaceItem)
            return items, None
        except Exception as exc:
            return [], str(exc)

    def _enrich(self, scraped_items: list[MarketplaceItem]) -> tuple[list[EnrichedItem], str | None, dict[str, int | float]]:
        if not scraped_items:
            return [], None, {
                "ai_cost_usd": 0.0,
                "openai_input_tokens": 0,
                "openai_output_tokens": 0,
                "openai_web_search_calls": 0,
            }

        enriched_items: list[EnrichedItem] = []
        errors: list[str] = []
        ai_cost_usd = 0.0
        input_tokens = 0
        output_tokens = 0
        web_search_calls = 0

        for item in scraped_items[:8]:
            try:
                raw = self.research_tool._run(
                    title=item.title,
                    image_url=item.image,
                    description=item.description,
                )
                parsed = self._parse_research_output(raw)
                enriched_items.append(
                    EnrichedItem(
                        title=item.title,
                        marketplace_price=item.price,
                        marketplace_url=item.url,
                        image_url=item.image,
                        official_product_name=parsed.get("official_product_name"),
                        official_price=parsed.get("official_price"),
                        release_date=parsed.get("release_date"),
                        key_specs=self._list_of_str(parsed.get("key_specs")),
                        market_summary=str(parsed.get("market_summary") or ""),
                        confidence=str(parsed.get("confidence") or "medium"),
                        sources=self._list_of_str(parsed.get("sources")),
                    )
                )
                ai_cost_usd += self.research_tool.last_cost_usd
                input_tokens += self.research_tool.last_input_tokens
                output_tokens += self.research_tool.last_output_tokens
                web_search_calls += self.research_tool.last_web_search_calls
            except Exception as exc:
                errors.append(f"{item.title}: {exc}")

        return (
            enriched_items,
            "; ".join(errors) if errors else None,
            {
                "ai_cost_usd": round(ai_cost_usd, 6),
                "openai_input_tokens": input_tokens,
                "openai_output_tokens": output_tokens,
                "openai_web_search_calls": web_search_calls,
            },
        )

    def _parse_research_output(self, raw: str) -> dict[str, object]:
        text = raw.strip()
        if "```" in text:
            text = text.replace("```json", "").replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            text = text[start : end + 1]
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise StructuredOutputError("官方資料補全結果不是 JSON 物件。")
        return parsed

    def _list_of_str(self, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    def _build_summary(
        self,
        scraped_items: list[MarketplaceItem],
        enriched_items: list[EnrichedItem],
        social_posts: list[SocialPostPack],
        scrape_error: str | None,
        enrich_error: str | None,
        creative_error: str | None,
        cost_metrics: dict[str, int | float],
    ) -> MonitorSummary:
        risks: list[str] = []
        actions: list[str] = []

        if scrape_error:
            risks.append(f"scrape 階段失敗: {scrape_error}")
        if enrich_error:
            risks.append(f"enrich 階段部分失敗: {enrich_error}")
        if creative_error:
            risks.append(f"creative 階段失敗: {creative_error}")

        if not scraped_items:
            risks.append("未抓到任何 Marketplace 商品資料。")
            actions.extend(
                [
                    "檢查 Apify actor 是否仍可抓取 Facebook Marketplace。",
                    "調整搜尋地區或改用更具體的設備關鍵字。",
                ]
            )

        if scraped_items and not enriched_items:
            actions.append("已抓到商品，但官方資料補全失敗，建議檢查 OpenAI web search 配置。")
        if enriched_items:
            actions.append("目前系統已切換為資料收集模式，社群貼文生成與發送暫時停用。")

        status = "completed"
        if not scraped_items:
            status = "failed"
        elif risks:
            status = "partial_success"

        return MonitorSummary(
            scraped_count=len(scraped_items),
            enriched_count=len(enriched_items),
            social_post_count=len(social_posts),
            ai_cost_usd=float(cost_metrics.get("ai_cost_usd", 0.0) or 0.0),
            openai_input_tokens=int(cost_metrics.get("openai_input_tokens", 0) or 0),
            openai_output_tokens=int(cost_metrics.get("openai_output_tokens", 0) or 0),
            openai_web_search_calls=int(cost_metrics.get("openai_web_search_calls", 0) or 0),
            risks=risks,
            recommended_next_actions=actions,
            status=status,
        )

    def _persist_payload(self, payload: PipelinePayload) -> list[str]:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            return ["略過 Supabase 寫入，因為尚未設定資料庫環境變數。"]

        monitor_tool = DBMonitorTool()
        stage_payloads = {
            "scrape": dump_model_list(payload.scraped_items),
            "enrich": dump_model_list(payload.enriched_items),
            "social": dump_model_list(payload.social_posts),
            "publish": dump_model_list(payload.published_posts),
            "summary": payload.summary.model_dump(mode="json"),
        }

        messages: list[str] = []
        for stage_name, stage_payload in stage_payloads.items():
            message = monitor_tool._run(
                run_id=payload.run_id,
                stage=stage_name,
                query=payload.query,
                status=payload.summary.status,
                payload_json=json.dumps(stage_payload, ensure_ascii=False),
            )
            messages.append(message)
        return messages
