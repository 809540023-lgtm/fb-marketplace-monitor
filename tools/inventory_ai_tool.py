from __future__ import annotations

import json
from typing import ClassVar

from crewai.tools import BaseTool
from openai import OpenAI
from pydantic import BaseModel, Field

from config import settings


class InventoryVisionInput(BaseModel):
    warehouse_date: str = Field(..., description="入倉日期資料夾，例如 20260101")
    source_file_stem: str = Field(..., description="檔名主體，例如 四門冰箱")
    image_urls: list[str] = Field(default_factory=list, description="同一商品的 1-4 張圖片")


class InventoryAIVisionTool(BaseTool):
    name: str = "inventory_ai_vision"
    description: str = "根據入倉商品的檔名與多張圖片，自動辨識商品、估值並產生行銷文草稿。"
    args_schema: type[BaseModel] = InventoryVisionInput
    MODEL_PRICING_PER_1M: ClassVar[dict[str, tuple[float, float]]] = {
        "gpt-4.1-mini": (0.40, 1.60),
        "gpt-4.1": (2.00, 8.00),
        "gpt-4.1-nano": (0.10, 0.40),
    }

    last_cost_usd: float = 0.0

    def _record_cost(self, response: object, model_name: str) -> None:
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        input_rate, output_rate = self.MODEL_PRICING_PER_1M.get(model_name, self.MODEL_PRICING_PER_1M["gpt-4.1-mini"])
        self.last_cost_usd = round(((input_tokens * input_rate) + (output_tokens * output_rate)) / 1_000_000, 6)

    def _run(self, warehouse_date: str, source_file_stem: str, image_urls: list[str]) -> str:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY 尚未設定。")

        client = OpenAI(api_key=settings.openai_api_key)
        prompt = (
            "你是二手餐飲設備入倉建檔專家。請根據檔名與圖片，輸出 JSON 物件。"
            "欄位必須包含：product_name, normalized_product_name, brand, model, category, "
            "condition_summary, missing_parts, cleaning_status, repair_status, suggested_price, min_price, "
            "suggested_platforms, confidence, needs_review, marketing。"
            "marketing 內必須包含 listing_title, short_description, facebook_post, threads_post, hashtags, seo_keywords。"
            "請優先用繁體中文。若無法判定，請明確填 unknown。只輸出 JSON。"
        )

        content: list[dict[str, str]] = [
            {
                "type": "input_text",
                "text": f"入倉日期: {warehouse_date}\n檔名主體: {source_file_stem}\n請辨識這組商品圖片。",
            }
        ]
        for image_url in image_urls[:4]:
            content.append({"type": "input_image", "image_url": image_url})

        model_name = settings.openai_model
        response = client.responses.create(
            model=model_name,
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": content},
            ],
        )
        self._record_cost(response, model_name)
        return response.output_text if hasattr(response, "output_text") else json.dumps({"raw": response.model_dump()}, ensure_ascii=False)
