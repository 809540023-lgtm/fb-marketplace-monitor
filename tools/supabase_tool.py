from __future__ import annotations

import json

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from supabase import Client, create_client

from config import settings


class DBMonitorToolInput(BaseModel):
    run_id: str = Field(..., description="本次執行的唯一識別碼")
    stage: str = Field(..., description="目前寫入的階段，例如 scrape、enrich、social、summary")
    query: str = Field(..., description="原始搜尋關鍵字")
    status: str = Field(default="completed", description="目前狀態")
    payload_json: str = Field(..., description="要寫入 Supabase 的 JSON 字串")


class DBMonitorTool(BaseTool):
    name: str = "database_monitor_tool"
    description: str = "將各階段產出的商品資料、貼文與執行摘要存入 Supabase 的 product_logs 資料表。"
    args_schema: type[BaseModel] = DBMonitorToolInput

    def _client(self) -> Client:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise ValueError("SUPABASE_URL 或 SUPABASE_SERVICE_ROLE_KEY 尚未設定。")
        return create_client(settings.supabase_url, settings.supabase_service_role_key)

    def _run(self, run_id: str, stage: str, query: str, payload_json: str, status: str = "completed") -> str:
        payload = json.loads(payload_json)
        record = {
            "run_id": run_id,
            "stage": stage,
            "query": query,
            "status": status,
            "payload": payload,
        }
        self._client().table("product_logs").insert(record).execute()
        return f"已將 {stage} 階段資料寫入 Supabase。"
