from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class MarketplaceItem(BaseModel):
    title: str = ""
    price: str | int | float | None = None
    image: str | None = None
    url: str | None = None
    description: str = ""
    seller_name: str | None = None
    location: str | None = None


class EnrichedItem(BaseModel):
    title: str
    marketplace_price: str | int | float | None = None
    marketplace_url: str | None = None
    image_url: str | None = None
    official_product_name: str | None = None
    official_price: str | None = None
    release_date: str | None = None
    key_specs: list[str] = Field(default_factory=list)
    market_summary: str = ""
    confidence: str = "medium"
    sources: list[str] = Field(default_factory=list)


class SocialPostPack(BaseModel):
    product_title: str
    instagram_post: str
    facebook_post: str
    threads_post: str
    hashtags: list[str] = Field(default_factory=list)


class MonitorSummary(BaseModel):
    scraped_count: int = 0
    enriched_count: int = 0
    social_post_count: int = 0
    ai_cost_usd: float = 0.0
    openai_input_tokens: int = 0
    openai_output_tokens: int = 0
    openai_web_search_calls: int = 0
    risks: list[str] = Field(default_factory=list)
    recommended_next_actions: list[str] = Field(default_factory=list)
    status: str = "completed"


class PublishedPost(BaseModel):
    platform: Literal["facebook", "instagram", "threads"]
    product_title: str
    published: bool = False
    dry_run: bool = True
    external_id: str | None = None
    preview_text: str = ""
    error: str | None = None


class PipelinePayload(BaseModel):
    run_id: str
    query: str
    scraped_items: list[MarketplaceItem] = Field(default_factory=list)
    enriched_items: list[EnrichedItem] = Field(default_factory=list)
    social_posts: list[SocialPostPack] = Field(default_factory=list)
    published_posts: list[PublishedPost] = Field(default_factory=list)
    summary: MonitorSummary = Field(default_factory=MonitorSummary)


class PipelineRunRequest(BaseModel):
    query: str = Field(..., description="Marketplace 搜尋關鍵字")
    location: str = Field(default="Taipei", description="Marketplace 搜尋地區")
    max_results: int = Field(default=3, ge=1, le=20)
    publish: bool = Field(default=False, description="是否要在跑完後實際執行平台發文")


class PipelineRunResponse(BaseModel):
    run_id: str
    query: str
    location: str
    max_results: int
    payload: PipelinePayload


class InventoryImage(BaseModel):
    image_name: str
    image_url: str
    image_order: int = 1


class InventoryMarketingAsset(BaseModel):
    listing_title: str = ""
    short_description: str = ""
    facebook_post: str = ""
    threads_post: str = ""
    hashtags: list[str] = Field(default_factory=list)
    seo_keywords: list[str] = Field(default_factory=list)


class InventoryItem(BaseModel):
    warehouse_date: str
    folder_name: str
    product_name: str = ""
    normalized_product_name: str = ""
    source_file_stem: str = ""
    brand: str = ""
    model: str = ""
    category: str = ""
    condition_summary: str = ""
    missing_parts: str = ""
    cleaning_status: str = "unknown"
    repair_status: str = "unknown"
    suggested_price: float | None = None
    min_price: float | None = None
    suggested_platforms: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    needs_review: bool = False
    source_type: str = "purchased_inventory"
    image_count: int = 0
    images: list[InventoryImage] = Field(default_factory=list)
    marketing: InventoryMarketingAsset = Field(default_factory=InventoryMarketingAsset)


class InventoryIngestSummary(BaseModel):
    folders_scanned: int = 0
    image_groups: int = 0
    items_created: int = 0
    ai_cost_usd: float = 0.0
    needs_review_count: int = 0
    status: str = "completed"
    risks: list[str] = Field(default_factory=list)


class InventoryIngestResponse(BaseModel):
    run_id: str
    folder_name: str
    items: list[InventoryItem] = Field(default_factory=list)
    summary: InventoryIngestSummary = Field(default_factory=InventoryIngestSummary)
