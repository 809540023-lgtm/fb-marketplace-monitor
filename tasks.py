from __future__ import annotations

from crewai import Task

from agents import creative_agent, enricher_agent, monitor_agent, scraper_agent


def build_tasks(query: str, location_name: str, max_results: int, run_id: str) -> list[Task]:
    scrape_task = Task(
        description=(
            f"使用 fb_marketplace_scraper 搜尋 `{query}`，地區為 `{location_name}`，最多抓 `{max_results}` 筆。"
            "如果地區包含多個城市，請將它視為多區輪搜設定並彙整結果。"
            "如果關鍵字涉及生財、餐飲、器具，請理解成餐飲設備詞庫模式，工具會自動展開多個設備品項詞搜尋。"
            "請只回傳 JSON 陣列，不要加入 markdown code fence 或額外說明。"
            "每筆至少包含 title、price、image、url、description、seller_name、location。"
        ),
        expected_output="JSON 陣列格式的 Marketplace 商品清單。",
        agent=scraper_agent,
    )

    enrich_task = Task(
        description=(
            "接收前一步的 JSON 商品清單。對每一筆商品呼叫 official_product_research。"
            "請只輸出 JSON 陣列，不要加入 markdown code fence 或額外說明。"
            "請輸出 JSON 陣列，每筆包含 title、marketplace_price、marketplace_url、image_url、"
            "official_product_name、official_price、release_date、key_specs、market_summary、confidence、sources。"
            "若型號不明，請保持 unknown 並說明原因。"
        ),
        expected_output="JSON 陣列格式的官方規格補全結果。",
        agent=enricher_agent,
        context=[scrape_task],
    )

    creative_task = Task(
        description=(
            "根據前一步的補全結果，為每一件商品分別產生三種平台貼文。"
            "請只輸出 JSON 陣列，不要加入 markdown code fence 或額外說明。"
            "請輸出 JSON 陣列，每筆包含 product_title、instagram_post、facebook_post、threads_post、hashtags。"
            "Instagram 可較活潑，Facebook 要資訊完整，Threads 要自然、短而有討論感。"
        ),
        expected_output="JSON 陣列格式的多平台社群貼文。",
        agent=creative_agent,
        context=[enrich_task],
    )

    monitor_task = Task(
        description=(
            f"請整理 scrape、enrich、creative 三個階段的結果，run_id 為 `{run_id}`，query 為 `{query}`。"
            "請只輸出 JSON 物件，不要加入 markdown code fence 或額外說明。"
            "請輸出一份 JSON 物件作為 summary，至少包含 scraped_count、enriched_count、social_post_count、"
            "risks、recommended_next_actions、status。"
        ),
        expected_output="JSON 物件格式的最終監控摘要。",
        agent=monitor_agent,
        context=[scrape_task, enrich_task, creative_task],
    )

    return [scrape_task, enrich_task, creative_task, monitor_task]
