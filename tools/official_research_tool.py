from __future__ import annotations

import json
from typing import ClassVar

from crewai.tools import BaseTool
from openai import OpenAI
from pydantic import BaseModel, Field

from config import settings


class OfficialProductResearchInput(BaseModel):
    title: str = Field(..., description="Marketplace 商品標題")
    image_url: str | None = Field(default=None, description="商品圖片網址")
    description: str | None = Field(default=None, description="Marketplace 商品描述")


class OfficialProductResearchTool(BaseTool):
    name: str = "official_product_research"
    description: str = "分析商品標題與圖片，使用 OpenAI 網頁搜尋補充官方規格、建議售價、上市時間與參考來源。"
    args_schema: type[BaseModel] = OfficialProductResearchInput
    last_cost_usd: float = 0.0
    last_input_tokens: int = 0
    last_output_tokens: int = 0
    last_web_search_calls: int = 0

    MODEL_PRICING_PER_1M: ClassVar[dict[str, tuple[float, float]]] = {
        "gpt-4.1-mini": (0.40, 1.60),
        "gpt-4.1": (2.00, 8.00),
        "gpt-4.1-nano": (0.10, 0.40),
    }
    WEB_SEARCH_COST_PER_CALL_USD: ClassVar[float] = 0.025

    def _reset_usage(self) -> None:
        self.last_cost_usd = 0.0
        self.last_input_tokens = 0
        self.last_output_tokens = 0
        self.last_web_search_calls = 0

    def _record_usage(self, response: object, model_name: str) -> None:
        usage = getattr(response, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        input_rate, output_rate = self.MODEL_PRICING_PER_1M.get(model_name, self.MODEL_PRICING_PER_1M["gpt-4.1-mini"])
        token_cost = ((input_tokens * input_rate) + (output_tokens * output_rate)) / 1_000_000

        self.last_input_tokens = input_tokens
        self.last_output_tokens = output_tokens
        self.last_web_search_calls = 1
        self.last_cost_usd = round(token_cost + self.WEB_SEARCH_COST_PER_CALL_USD, 6)

    def _run(self, title: str, image_url: str | None = None, description: str | None = None) -> str:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY 尚未設定。")

        self._reset_usage()
        client = OpenAI(api_key=settings.openai_api_key)
        prompt = (
            "你是商品研究分析師。請根據使用者提供的 Marketplace 商品資訊，"
            "優先找出最可能對應的官方產品頁或品牌資訊，並回傳 JSON。"
            "JSON 欄位必須包含: official_product_name, official_price, release_date, key_specs, market_summary, confidence, sources。"
            "key_specs 與 sources 必須是陣列。若無法確認請明確寫 unknown。"
        )

        user_content = [
            {
                "type": "input_text",
                "text": (
                    f"商品標題: {title}\n"
                    f"商品描述: {description or '無'}\n"
                    "請將圖片與文字一起交叉判斷，避免把相似型號混淆。"
                ),
            }
        ]
        if image_url:
            user_content.append({"type": "input_image", "image_url": image_url})

        model_name = settings.openai_research_model
        response = client.responses.create(
            model=model_name,
            tools=[
                {
                    "type": "web_search_preview",
                    "search_context_size": "medium",
                    "user_location": {
                        "type": "approximate",
                        "city": "Taipei",
                        "country": "TW",
                        "timezone": "Asia/Taipei",
                    },
                }
            ],
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
            ],
        )
        self._record_usage(response, model_name)
        return response.output_text if hasattr(response, "output_text") else json.dumps({"raw": response.model_dump()}, ensure_ascii=False)
