from __future__ import annotations

import json
import uuid

from models import (
    InventoryImage,
    InventoryIngestResponse,
    InventoryIngestSummary,
    InventoryItem,
    InventoryMarketingAsset,
)
from tools.google_drive_inventory_tool import GoogleDriveInventoryTool
from tools.inventory_ai_tool import InventoryAIVisionTool
from tools.inventory_supabase_tool import InventorySupabaseTool
from utils.json_parser import extract_json_candidate


class InventoryPipelineService:
    def __init__(self) -> None:
        self.drive_tool = GoogleDriveInventoryTool()
        self.vision_tool = InventoryAIVisionTool()
        self.supabase_tool = InventorySupabaseTool()

    def run(self, folder_name: str | None = None) -> InventoryIngestResponse:
        run_id = uuid.uuid4().hex
        raw_scan = self.drive_tool._run(folder_name=folder_name)
        scan_payload = json.loads(raw_scan)
        groups = scan_payload.get("groups", [])

        items: list[InventoryItem] = []
        risks: list[str] = []
        ai_cost_usd = 0.0

        for group in groups:
            try:
                raw_item = self.vision_tool._run(
                    warehouse_date=str(group.get("warehouse_date") or ""),
                    source_file_stem=str(group.get("source_file_stem") or ""),
                    image_urls=[str(image.get("image_url")) for image in group.get("images", [])],
                )
                parsed = json.loads(extract_json_candidate(raw_item))
                marketing = parsed.get("marketing") or {}
                item = InventoryItem(
                    warehouse_date=str(group.get("warehouse_date") or ""),
                    folder_name=str(group.get("folder_name") or ""),
                    source_file_stem=str(group.get("source_file_stem") or ""),
                    product_name=str(parsed.get("product_name") or ""),
                    normalized_product_name=str(parsed.get("normalized_product_name") or ""),
                    brand=str(parsed.get("brand") or ""),
                    model=str(parsed.get("model") or ""),
                    category=str(parsed.get("category") or ""),
                    condition_summary=str(parsed.get("condition_summary") or ""),
                    missing_parts=str(parsed.get("missing_parts") or ""),
                    cleaning_status=str(parsed.get("cleaning_status") or "unknown"),
                    repair_status=str(parsed.get("repair_status") or "unknown"),
                    suggested_price=float(parsed.get("suggested_price")) if parsed.get("suggested_price") is not None else None,
                    min_price=float(parsed.get("min_price")) if parsed.get("min_price") is not None else None,
                    suggested_platforms=[str(value) for value in parsed.get("suggested_platforms", [])],
                    confidence=float(parsed.get("confidence") or 0.0),
                    needs_review=bool(parsed.get("needs_review", False)),
                    image_count=int(group.get("image_count") or 0),
                    images=[
                        InventoryImage(
                            image_name=str(image.get("image_name") or ""),
                            image_url=str(image.get("image_url") or ""),
                            image_order=int(image.get("image_order") or 1),
                        )
                        for image in group.get("images", [])
                    ],
                    marketing=InventoryMarketingAsset(
                        listing_title=str(marketing.get("listing_title") or ""),
                        short_description=str(marketing.get("short_description") or ""),
                        facebook_post=str(marketing.get("facebook_post") or ""),
                        threads_post=str(marketing.get("threads_post") or ""),
                        hashtags=[str(value) for value in marketing.get("hashtags", [])],
                        seo_keywords=[str(value) for value in marketing.get("seo_keywords", [])],
                    ),
                )
                items.append(item)
                ai_cost_usd += self.vision_tool.last_cost_usd
                self.supabase_tool._run(item_payload=item.model_dump(mode="json"))
            except Exception as exc:
                risks.append(f"{group.get('source_file_stem')}: {exc}")

        summary = InventoryIngestSummary(
            folders_scanned=1 if scan_payload.get("folder_name") else 0,
            image_groups=len(groups),
            items_created=len(items),
            ai_cost_usd=round(ai_cost_usd, 6),
            needs_review_count=sum(1 for item in items if item.needs_review),
            status="partial_success" if risks else "completed",
            risks=risks,
        )
        return InventoryIngestResponse(
            run_id=run_id,
            folder_name=str(scan_payload.get("folder_name") or folder_name or ""),
            items=items,
            summary=summary,
        )
