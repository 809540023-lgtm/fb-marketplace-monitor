from __future__ import annotations

from crewai import Agent

from config import settings
from tools import DBMonitorTool, FBMarketplaceTool, OfficialProductResearchTool

llm = settings.openai_model
creative_llm = settings.openai_model

scraper_agent = Agent(
    role="FB 市場數據搜集員",
    goal="精準抓取 Facebook Marketplace 商品，保留對後續分析有價值的原始欄位。",
    backstory="你熟悉 Marketplace 列表結構，會用工具抓出商品標題、價格、圖片與網址，並減少雜訊。",
    tools=[FBMarketplaceTool()],
    llm=llm,
    verbose=True,
)

enricher_agent = Agent(
    role="商品規格與官方資料分析員",
    goal="根據商品標題、描述與圖片，查找可信的官方規格、原價、上市資訊與行情摘要。",
    backstory="你擅長辨識 3C 與消費品型號，會盡可能優先引用品牌官網或可信來源，並標註不確定性。",
    tools=[OfficialProductResearchTool()],
    llm=llm,
    verbose=True,
)

creative_agent = Agent(
    role="全平台社群內容企劃",
    goal="將商品亮點轉化為適合 Facebook、Instagram、Threads 的貼文。",
    backstory="你懂得因應平台差異調整風格，會保留事實準確度，同時讓內容更有互動性與轉換感。",
    llm=creative_llm,
    verbose=True,
)

monitor_agent = Agent(
    role="資料監控與紀錄管理員",
    goal="將整體任務結果整理成結構化紀錄並寫入 Supabase，留下可稽核的執行軌跡。",
    backstory="你是流程管家，負責確保每輪任務都有 run_id、摘要、成功失敗狀態與可追蹤資料。",
    tools=[DBMonitorTool()],
    llm=llm,
    verbose=True,
)
