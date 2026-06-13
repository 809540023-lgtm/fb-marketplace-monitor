from __future__ import annotations

import json
from collections import OrderedDict
from typing import ClassVar
from urllib.parse import quote_plus

from apify_client import ApifyClient
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from config import settings


class FBMarketplaceToolInput(BaseModel):
    query: str = Field(..., description="要在 Facebook Marketplace 搜尋的商品關鍵字")
    max_results: int = Field(default=settings.default_max_results, description="最多抓取幾筆資料")
    location_name: str = Field(default=settings.default_location_name, description="Marketplace 搜尋地區")


class FBMarketplaceTool(BaseTool):
    name: str = "fb_marketplace_scraper"
    description: str = "抓取 Facebook Marketplace 商品，回傳標題、價格、圖片連結、描述與商品網址。"
    args_schema: type[BaseModel] = FBMarketplaceToolInput

    CATERING_KEYWORD_LIBRARY: ClassVar[list[str]] = [
        "二手 餐飲 設備",
        "二手 商用 冰箱",
        "二手 四門 冰箱",
        "二手 工作台 冰箱",
        "二手 冷凍櫃",
        "二手 展示 冰箱",
        "二手 製冰機",
        "二手 封口機",
        "二手 真空包裝機",
        "二手 油炸機",
        "二手 快速爐",
        "二手 煮麵機",
        "二手 煎台",
        "二手 烤箱",
        "二手 蒸箱",
        "二手 攪拌機",
        "二手 切菜機",
        "二手 刨冰機",
        "二手 咖啡機",
        "二手 磨豆機",
        "二手 飲料封膜機",
        "二手 洗碗機",
        "二手 不鏽鋼 工作台",
        "二手 餐車 設備",
    ]

    SUPPORTED_COMMUNITY_ACTOR_IDS: ClassVar[set[str]] = {
        "scrapier/facebook-marketplace-scraper",
        "apify/facebook-marketplace-scraper",
    }
    RELEVANT_KEYWORDS: ClassVar[tuple[str, ...]] = (
        "餐飲", "生財", "商用", "廚房", "厨房", "設備", "设备", "工作台", "工作檯",
        "冰箱", "冷凍", "冷藏", "冷柜", "冷凍櫃", "冷藏櫃", "展示冰箱",
        "製冰機", "制冰机", "封口機", "封膜機", "真空包裝機", "油炸機", "炸炉",
        "快速爐", "煮麵機", "煎台", "烤箱", "蒸箱", "攪拌機", "切菜機",
        "刨冰機", "咖啡機", "磨豆機", "洗碗機", "不鏽鋼", "不锈钢", "餐車",
        "冰柜", "freezer", "refrigerator", "ice maker", "prep table", "commercial kitchen",
        "restaurant equipment", "undercounter", "work table", "sink",
    )
    LOCATION_KEYWORDS: ClassVar[tuple[str, ...]] = (
        "taipei", "new taipei", "taoyuan", "台北", "臺北", "新北", "桃園",
    )

    def _resolve_actor_id(self) -> str:
        actor_id = settings.apify_actor_id.strip()
        if actor_id in self.SUPPORTED_COMMUNITY_ACTOR_IDS:
            return "apify/facebook-marketplace-scraper"
        return actor_id or "apify/facebook-marketplace-scraper"

    def _build_start_urls(self, query_variants: list[str], location_names: list[str]) -> list[str]:
        start_urls: list[str] = []
        active_locations = location_names[:1] if settings.free_mode else location_names
        active_queries = query_variants[:1] if settings.free_mode else query_variants
        for current_location in active_locations:
            for current_query in active_queries:
                combined_query = f"{current_query} {current_location}".strip()
                url_query = quote_plus(current_query)
                location_query = quote_plus(combined_query)
                # Official Apify actor expects Marketplace URLs in startUrls.
                start_urls.append(f"https://www.facebook.com/marketplace/search/?query={location_query}")
                # Add a simpler query-only variant in case FB ignores location text in one form.
                if not settings.free_mode:
                    start_urls.append(f"https://www.facebook.com/marketplace/search/?query={url_query}")
        deduped = list(OrderedDict.fromkeys(item for item in start_urls if item))
        return deduped[:2] if settings.free_mode else deduped[:48]

    def _normalize_text(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            if isinstance(value.get("text"), str):
                return value["text"]
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _expand_queries(self, query: str) -> list[str]:
        base = query.strip()
        if not base:
            return []
        expanded = [base]
        if not settings.free_mode and any(keyword in base for keyword in ["生財", "餐飲", "器具"]):
            expanded.extend(self.CATERING_KEYWORD_LIBRARY)
        deduped = list(OrderedDict.fromkeys(item for item in expanded if item))
        return deduped[:24]

    def _is_relevant_item(self, item: dict[str, object]) -> bool:
        text = " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("description") or ""),
                str(item.get("url") or ""),
            ]
        ).lower()
        return any(keyword.lower() in text for keyword in self.RELEVANT_KEYWORDS)

    def _is_location_match(self, item: dict[str, object], requested_locations: list[str]) -> bool:
        requested = " ".join(requested_locations).lower()
        location_text = str(item.get("location") or "").lower()
        haystack = f"{requested} {location_text}"
        return any(keyword in haystack for keyword in self.LOCATION_KEYWORDS)

    def _run(self, query: str, max_results: int = settings.default_max_results, location_name: str = settings.default_location_name) -> str:
        if not settings.apify_api_token:
            raise ValueError("APIFY_API_TOKEN 尚未設定。")

        client = ApifyClient(settings.apify_api_token)
        actor_id = self._resolve_actor_id()
        query_variants = self._expand_queries(query)
        location_names = [name.strip() for name in location_name.split(",") if name.strip()]
        if not location_names:
            location_names = [settings.default_location_name]
        start_urls = self._build_start_urls(query_variants, location_names)

        deduped_results: OrderedDict[str, dict[str, object]] = OrderedDict()
        run_input = {
            "startUrls": [{"url": url} for url in start_urls],
            "resultsLimit": max_results,
            "includeListingDetails": not settings.free_mode,
        }
        run = client.actor(actor_id).call(
            run_input=run_input,
            memory_mbytes=512 if settings.free_mode else 1024,
        )

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            item_id = item.get("id")
            result = {
                "title": item.get("title") or "",
                "price": item.get("price"),
                "image": item.get("image"),
                "url": f"https://www.facebook.com/marketplace/item/{item_id}/" if item_id else item.get("url"),
                "description": self._normalize_text(item.get("description")),
                "seller_name": item.get("sellerName"),
                "location": self._normalize_text(item.get("location")),
            }
            if not self._is_relevant_item(result):
                continue
            if not self._is_location_match(result, location_names):
                continue
            dedupe_key = str(result["url"] or result["title"])
            deduped_results[dedupe_key] = result

        filtered_results = list(deduped_results.values())[:max_results]
        return json.dumps(filtered_results, ensure_ascii=False)
