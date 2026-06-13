from __future__ import annotations

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from supabase import Client, create_client

from config import settings


class InventoryUpsertInput(BaseModel):
    item_payload: dict = Field(..., description="InventoryItem 的 JSON payload")


class InventorySupabaseTool(BaseTool):
    name: str = "inventory_supabase_writer"
    description: str = "將已購入商品入倉建檔資料寫入 inventory_items、inventory_item_images、inventory_marketing_assets。"
    args_schema: type[BaseModel] = InventoryUpsertInput

    def _client(self) -> Client:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError("SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY 尚未設定。")
        return create_client(settings.supabase_url, settings.supabase_service_role_key)

    def _run(self, item_payload: dict) -> str:
        client = self._client()
        images = item_payload.pop("images", [])
        marketing = item_payload.pop("marketing", {})

        item_response = client.table("inventory_items").insert(item_payload).execute()
        item_rows = item_response.data or []
        if not item_rows:
            raise ValueError("inventory_items 寫入失敗。")

        inventory_item_id = item_rows[0]["id"]
        image_rows = []
        for image in images:
            image_rows.append(
                {
                    "inventory_item_id": inventory_item_id,
                    "image_name": image.get("image_name"),
                    "image_url": image.get("image_url"),
                    "image_order": image.get("image_order", 1),
                }
            )
        if image_rows:
            client.table("inventory_item_images").insert(image_rows).execute()

        if marketing:
            marketing["inventory_item_id"] = inventory_item_id
            client.table("inventory_marketing_assets").insert(marketing).execute()

        return f"已寫入 inventory_item_id={inventory_item_id}"
