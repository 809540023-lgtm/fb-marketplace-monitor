from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from html import escape
from html import unescape
import json
import re
from urllib.request import Request as UrlRequest, urlopen

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from config import settings
from digichef import router as digichef_router
from investment_plans import router as investment_plans_router
from school_platform.i18n import append_lang_to_url, localize_school_platform_html, normalize_ui_lang
from school_platform import router as school_platform_router

app = FastAPI(title="Marketplace Agent Team API", version="1.0.0")
app.include_router(school_platform_router)
app.include_router(digichef_router)
app.include_router(investment_plans_router)


@app.middleware("http")
async def school_platform_language_middleware(request: Request, call_next):
    response = await call_next(request)
    if not request.url.path.startswith("/school-platform"):
        return response

    lang = normalize_ui_lang(request.query_params.get("lang"))
    location = response.headers.get("location")
    if location:
        response.headers["location"] = append_lang_to_url(location, lang)

    if request.url.path.startswith("/school-platform/api"):
        return response

    content_type = response.headers.get("content-type", "").lower()
    if "text/html" not in content_type:
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    localized_html = localize_school_platform_html(body.decode("utf-8"), lang)
    headers = dict(response.headers)
    headers.pop("content-length", None)
    return HTMLResponse(content=localized_html, status_code=response.status_code, headers=headers)


def _rule_based_inventory_preview(folder_name: str, image_names: tuple[str, ...]) -> dict[str, str]:
    source = " ".join([folder_name, *image_names]).strip().lower()
    if not source:
        return {}

    rules = [
        (
            ("封口機", "seal", "sealer"),
            {
                "listing_title": "商用封口機｜最新入庫歡迎同行批發",
                "short_description": "適合飲料店與餐飲外帶封膜使用，設備外觀與配件狀態可再確認。",
                "category": "封膜封口設備",
                "brand": "待辨識",
                "model": "待辨識",
            },
        ),
        (
            ("製冰機", "ice maker", "ice machine"),
            {
                "listing_title": "商用製冰機｜最新入庫歡迎同行批發",
                "short_description": "適合飲料店、咖啡店與餐飲備冰使用，冰量與機況可進一步確認。",
                "category": "製冰冷飲設備",
                "brand": "待辨識",
                "model": "待辨識",
            },
        ),
        (
            ("開水機", "熱水機", "boiler", "water dispenser"),
            {
                "listing_title": "商用開水機｜最新入庫歡迎同行批發",
                "short_description": "適合茶飲店、早餐店與內場熱水供應，容量與加熱狀態可再確認。",
                "category": "飲水加熱設備",
                "brand": "待辨識",
                "model": "待辨識",
            },
        ),
        (
            ("orchestrale", "radiofonica", "義式機", "咖啡機", "espresso"),
            {
                "listing_title": "商用雙孔義式咖啡機｜最新入庫歡迎同行批發",
                "short_description": "義式咖啡店常用的商用咖啡設備，適合做吧台主機與整套規劃。",
                "category": "商用咖啡設備",
                "brand": "Orchestrale",
                "model": "Radiofonica 2GR",
            },
        ),
    ]

    for keywords, payload in rules:
        if any(keyword.lower() in source for keyword in keywords):
            return payload
    return {}


@lru_cache(maxsize=256)
def _image_url_to_data_url(image_url: str) -> str:
    if not image_url:
        return ""

    try:
        with urlopen(image_url) as response:
            content_type = str(response.headers.get("Content-Type") or "image/jpeg")
            raw = response.read()
    except Exception:
        return ""

    if not raw:
        return ""

    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


@lru_cache(maxsize=128)
def _ai_inventory_preview(
    folder_name: str,
    warehouse_date: str,
    image_signature: str,
    primary_image_url: str,
    secondary_image_url: str = "",
) -> dict[str, object]:
    if not settings.openai_api_key or not primary_image_url:
        return {}

    try:
        prompt = (
            "你是二手餐飲設備辨識助手。請根據商品圖片判斷這是什麼設備，"
            "用繁體中文輸出 JSON，欄位只有：listing_title, short_description, category, brand, model。"
            "listing_title 要像批發頁標題，short_description 要短而自然。若不確定請保守描述，不要亂編。只輸出 JSON。"
        )
        primary_image_input = _image_url_to_data_url(primary_image_url) or primary_image_url
        secondary_image_input = _image_url_to_data_url(secondary_image_url) or secondary_image_url
        content: list[dict[str, object]] = [
            {
                "type": "text",
                "text": f"資料夾名稱：{folder_name}\n入庫日期：{warehouse_date}\n請辨識圖片中的商品。",
            },
            {"type": "image_url", "image_url": {"url": primary_image_input}},
        ]
        if secondary_image_input:
            content.append({"type": "image_url", "image_url": {"url": secondary_image_input}})

        payload = {
            "model": settings.openai_research_model or settings.openai_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": content},
            ],
        }
        request = UrlRequest(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8", errors="ignore"))

        text = str((((body.get("choices") or [{}])[0]).get("message") or {}).get("content") or "")
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return {}
        payload = json.loads(match.group(0))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _dashboard_rows() -> list[dict[str, str]]:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return []

    from supabase import create_client

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    response = (
        client.table("product_logs")
        .select("run_id,stage,status,query,created_at")
        .order("created_at", desc=True)
        .limit(20)
        .execute()
    )
    return response.data or []


def _inventory_latest_rows() -> list[dict[str, object]]:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return []

    from supabase import create_client

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    response = (
        client.table("inventory_items")
        .select(
            "id,warehouse_date,folder_name,product_name,normalized_product_name,brand,model,category,"
            "condition_summary,suggested_price,min_price,confidence,needs_review,created_at,"
            "inventory_item_images(image_name,image_url,image_order),"
            "inventory_marketing_assets(listing_title,short_description,facebook_post,threads_post,hashtags,seo_keywords)"
        )
        .order("created_at", desc=True)
        .limit(18)
        .execute()
    )
    return response.data or []


def _inventory_latest_state() -> tuple[list[dict[str, object]], str | None]:
    try:
        return _inventory_latest_rows(), None
    except Exception as exc:
        fallback_rows = _public_inventory_seed_rows()
        if fallback_rows:
            return fallback_rows, f"{exc}；目前已改用 Google Drive 公開資料夾內容展示。"
        return [], str(exc)


def _public_inventory_seed_rows() -> list[dict[str, object]]:
    if not settings.google_drive_root_folder_id:
        return []

    def _read_folder_html(folder_id: str) -> str:
        with urlopen(f"https://drive.google.com/embeddedfolderview?id={folder_id}#grid") as response:
            return response.read().decode("utf-8", errors="ignore")

    pattern = re.compile(
        r'<div class="flip-entry" id="entry-([^"]+)".*?<a href="([^"]+)"[^>]*>.*?<div class="flip-entry-title">(.*?)</div>',
        re.S,
    )
    thumb_pattern = re.compile(
        r'<div class="flip-entry" id="entry-([^"]+)".*?<img src="([^"]+)"[^>]*alt="[^"]*".*?<div class="flip-entry-title">(.*?)</div>',
        re.S,
    )

    try:
        html = _read_folder_html(settings.google_drive_root_folder_id)
    except Exception:
        return []

    rows: list[dict[str, object]] = []
    loose_image_rows: list[dict[str, object]] = []
    for entry_id, href, title in pattern.findall(html):
        clean_title = unescape(re.sub(r"<[^>]+>", "", title)).strip()
        if "/drive/folders/" not in href:
            if "/file/d/" in href:
                image_match = re.search(
                    rf'<div class="flip-entry" id="entry-{re.escape(entry_id)}".*?<img src="([^"]+)"[^>]*',
                    html,
                    re.S,
                )
                image_src = image_match.group(1).strip() if image_match else ""
                loose_image_rows.append(
                    {
                        "id": entry_id.strip(),
                        "warehouse_date": datetime.now().strftime("%Y%m%d"),
                        "folder_name": clean_title,
                        "product_name": clean_title,
                        "normalized_product_name": clean_title,
                        "brand": "待 AI 辨識",
                        "model": "待 AI 辨識",
                        "category": "未分類入庫照片",
                        "condition_summary": "這張照片目前直接放在 agai2_new 根目錄，已先列入待整理區。",
                        "suggested_price": None,
                        "min_price": None,
                        "confidence": 0,
                        "needs_review": True,
                        "inventory_item_images": [
                            {
                                "image_name": clean_title,
                                "image_url": image_src,
                                "image_order": 1,
                                "file_id": entry_id.strip(),
                            }
                        ]
                        if image_src
                        else [],
                        "inventory_marketing_assets": [
                            {
                                "listing_title": f"未分類新上傳照片｜{clean_title}",
                                "short_description": "新照片已上傳至根目錄，系統先顯示在待整理區，後續可再歸入對應商品。",
                                "hashtags": ["最新入庫", "待整理", "未分類照片"],
                            }
                        ],
                    }
                )
            continue
        sub_images: list[dict[str, object]] = []
        try:
            sub_html = _read_folder_html(entry_id.strip())
            for image_id, image_src, image_title in thumb_pattern.findall(sub_html):
                sub_images.append(
                    {
                        "image_name": unescape(re.sub(r"<[^>]+>", "", image_title)).strip(),
                        "image_url": image_src.strip(),
                        "image_order": len(sub_images) + 1,
                        "file_id": image_id.strip(),
                    }
                )
        except Exception:
            sub_images = []

        rows.append(
            {
                "id": entry_id.strip(),
                "warehouse_date": datetime.now().strftime("%Y%m%d"),
                "folder_name": clean_title,
                "product_name": clean_title,
                "normalized_product_name": clean_title,
                "brand": "待 AI 辨識",
                "model": "待 AI 辨識",
                "category": "待分類",
                "condition_summary": "已偵測到入庫商品資料夾，等待 AI 建檔與圖片分析。",
                "suggested_price": None,
                "min_price": None,
                "confidence": 0,
                "needs_review": False,
                "inventory_item_images": sub_images,
                "inventory_marketing_assets": [
                    {
                        "listing_title": f"{clean_title}｜最新入庫歡迎同行批發",
                        "short_description": f"商品已進入入庫流程，目前偵測到 {len(sub_images)} 張圖片，估價與辨識資料整理中。",
                        "hashtags": ["最新入庫", "同行批發", "餐飲設備"],
                    }
                ],
            }
        )
    combined_rows = rows + loose_image_rows
    for row in combined_rows[:24]:
        images = row.get("inventory_item_images") or []
        image_names = tuple(str(image.get("image_name") or "") for image in images[:4])
        primary_image = str(images[0].get("image_url") or "") if images else ""
        secondary_image = str(images[1].get("image_url") or "") if len(images) > 1 else ""
        signature = "|".join(str(image.get("image_url") or "") for image in images[:2])
        fallback_preview = _rule_based_inventory_preview(
            folder_name=str(row.get("folder_name") or ""),
            image_names=image_names,
        )
        ai_preview = _ai_inventory_preview(
            folder_name=str(row.get("folder_name") or ""),
            warehouse_date=str(row.get("warehouse_date") or ""),
            image_signature=signature,
            primary_image_url=primary_image,
            secondary_image_url=secondary_image,
        )
        preview = ai_preview or fallback_preview
        if preview:
            row["normalized_product_name"] = str(
                preview.get("listing_title")
                or row.get("normalized_product_name")
                or row.get("product_name")
                or ""
            )
            row["category"] = str(preview.get("category") or row.get("category") or "待分類")
            row["brand"] = str(preview.get("brand") or row.get("brand") or "待 AI 辨識")
            row["model"] = str(preview.get("model") or row.get("model") or "待 AI 辨識")
            marketing_rows = row.get("inventory_marketing_assets") or []
            if marketing_rows:
                marketing_rows[0]["listing_title"] = str(
                    preview.get("listing_title") or marketing_rows[0].get("listing_title") or row.get("folder_name") or ""
                )
                marketing_rows[0]["short_description"] = str(
                    preview.get("short_description") or marketing_rows[0].get("short_description") or ""
                )
    return combined_rows[:24]


def _cost_summary_6h() -> dict[str, float | int]:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return {
            "window_hours": 6,
            "run_count": 0,
            "summary_rows": 0,
            "ai_cost_usd": 0.0,
            "openai_input_tokens": 0,
            "openai_output_tokens": 0,
            "openai_web_search_calls": 0,
        }

    from supabase import create_client

    since = (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat()
    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    response = (
        client.table("product_logs")
        .select("run_id,payload,created_at")
        .eq("stage", "summary")
        .gte("created_at", since)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )
    rows = response.data or []

    total_cost = 0.0
    total_input = 0
    total_output = 0
    total_search_calls = 0
    run_ids: set[str] = set()

    for row in rows:
        payload = row.get("payload") or {}
        if not isinstance(payload, dict):
            continue
        run_id = str(row.get("run_id") or "")
        if run_id:
            run_ids.add(run_id)
        total_cost += float(payload.get("ai_cost_usd", 0.0) or 0.0)
        total_input += int(payload.get("openai_input_tokens", 0) or 0)
        total_output += int(payload.get("openai_output_tokens", 0) or 0)
        total_search_calls += int(payload.get("openai_web_search_calls", 0) or 0)

    return {
        "window_hours": 6,
        "run_count": len(run_ids),
        "summary_rows": len(rows),
        "ai_cost_usd": round(total_cost, 6),
        "openai_input_tokens": total_input,
        "openai_output_tokens": total_output,
        "openai_web_search_calls": total_search_calls,
    }


def _dashboard_state() -> tuple[list[dict[str, str]], dict[str, float | int], str | None]:
    try:
        return _dashboard_rows(), _cost_summary_6h(), None
    except Exception as exc:
        return [], {
            "window_hours": 6,
            "run_count": 0,
            "summary_rows": 0,
            "ai_cost_usd": 0.0,
            "openai_input_tokens": 0,
            "openai_output_tokens": 0,
            "openai_web_search_calls": 0,
        }, str(exc)


def _marketplace_home_html() -> str:
    rows, cost_summary, error_message = _dashboard_state()
    table_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('created_at', '')))}</td>"
        f"<td>{escape(str(row.get('run_id', '')))}</td>"
        f"<td>{escape(str(row.get('stage', '')))}</td>"
        f"<td>{escape(str(row.get('status', '')))}</td>"
        f"<td>{escape(str(row.get('query', '')))}</td>"
        "</tr>"
        for row in rows
    )
    if not table_rows:
        table_rows = "<tr><td colspan='5'>目前還沒有可顯示的紀錄，請先確認 Supabase 資料表已建立且 pipeline 有執行。</td></tr>"
    error_banner = ""
    if error_message:
        error_banner = f"<p style='margin-top:12px;color:#a44c22;font-weight:700;'>Dashboard 目前讀取資料失敗：{escape(error_message)}</p>"

    return f"""
    <!doctype html>
    <html lang=\"zh-Hant\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>CrewAI Marketplace Dashboard</title>
        <style>
          :root {{
            --bg: #f4efe8;
            --panel: #fffaf1;
            --ink: #1e1a16;
            --muted: #6c6258;
            --line: #d7c7b2;
            --accent: #a44c22;
            --accent-2: #214e34;
          }}
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: linear-gradient(180deg, #efe6d8 0%, var(--bg) 100%); color: var(--ink); }}
          .wrap {{ max-width: 1120px; margin: 0 auto; padding: 32px 20px 60px; }}
          .hero {{ background: var(--panel); border: 1px solid var(--line); border-radius: 24px; padding: 28px; box-shadow: 0 18px 50px rgba(0,0,0,.06); }}
          .eyebrow {{ color: var(--accent); font-weight: 700; letter-spacing: .08em; font-size: 12px; text-transform: uppercase; }}
          h1 {{ margin: 8px 0 10px; font-size: 40px; line-height: 1.05; }}
          p {{ color: var(--muted); font-size: 16px; line-height: 1.7; }}
          .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 18px; }}
          .card {{ background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 18px; }}
          .label {{ font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }}
          .value {{ margin-top: 8px; font-size: 22px; font-weight: 700; }}
          .table-wrap {{ margin-top: 20px; background: #fff; border: 1px solid var(--line); border-radius: 18px; overflow: hidden; }}
          table {{ width: 100%; border-collapse: collapse; }}
          th, td {{ padding: 14px 16px; border-bottom: 1px solid #eee1d2; text-align: left; vertical-align: top; font-size: 14px; }}
          th {{ background: #f8f1e7; color: var(--muted); font-weight: 700; }}
          .actions {{ display: flex; gap: 12px; margin-top: 18px; flex-wrap: wrap; }}
          .btn {{ display: inline-block; padding: 12px 16px; border-radius: 999px; text-decoration: none; color: #fff; background: var(--accent); font-weight: 700; }}
          .btn.alt {{ background: var(--accent-2); }}
          .btn.ghost {{ background: #6c6258; }}
          @media (max-width: 800px) {{ .grid {{ grid-template-columns: 1fr; }} h1 {{ font-size: 30px; }} th, td {{ font-size: 13px; }} }}
        </style>
      </head>
      <body>
        <div class=\"wrap\">
          <section class=\"hero\">
            <div class=\"eyebrow\">CrewAI Marketplace Team</div>
            <h1>二手生財餐飲器具<br />營運看板</h1>
            <p>目前系統以資料收集模式運作：A 組抓取、B 組補資料、D 組寫入 Supabase。社群文案生成與平台發送已暫時停用，先專注在資料品質與監控。</p>
            <div class=\"grid\">
              <div class=\"card\"><div class=\"label\">運作模式</div><div class=\"value\">Data Collection</div></div>
              <div class=\"card\"><div class=\"label\">主要區域</div><div class=\"value\">新北 / 台北 / 桃園</div></div>
              <div class=\"card\"><div class=\"label\">查詢預設</div><div class=\"value\">二手 生財 餐飲 器具</div></div>
              <div class=\"card\"><div class=\"label\">近 6 小時 AI 成本</div><div class=\"value\">${cost_summary['ai_cost_usd']}</div></div>
              <div class=\"card\"><div class=\"label\">近 6 小時 Run 數</div><div class=\"value\">{cost_summary['run_count']}</div></div>
              <div class=\"card\"><div class=\"label\">近 6 小時搜尋次數</div><div class=\"value\">{cost_summary['openai_web_search_calls']}</div></div>
            </div>
            <div class=\"actions\">
              <a class=\"btn\" href=\"/health\">Health</a>
              <a class=\"btn alt\" href=\"/dashboard/data\">JSON Data</a>
              <a class=\"btn alt\" href=\"/inventory/latest\">最新入庫批發頁</a>
              <a class=\"btn ghost\" href=\"/digichef\">Open DigiChef MVP</a>
            </div>
            {error_banner}
          </section>
          <section class=\"table-wrap\">
            <table>
              <thead>
                <tr>
                  <th>時間</th>
                  <th>Run ID</th>
                  <th>Stage</th>
                  <th>Status</th>
                  <th>Query</th>
                </tr>
              </thead>
              <tbody>{table_rows}</tbody>
            </table>
          </section>
        </div>
      </body>
    </html>
    """


@app.get("/", include_in_schema=False)
def home(request: Request):
    target = "/school-platform"
    query_string = request.url.query
    if query_string:
        target = f"{target}?{query_string}"
    return RedirectResponse(url=target, status_code=307)


@app.get("/marketplace", response_class=HTMLResponse)
def marketplace_home() -> str:
    return _marketplace_home_html()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "mode": "data_collection_only"}


@app.get("/dashboard/data")
def dashboard_data() -> dict[str, object]:
    rows, cost_summary, error_message = _dashboard_state()
    return {"rows": rows, "cost_summary_6h": cost_summary, "data_collection_only": True, "error": error_message}


@app.get("/inventory/latest", response_class=HTMLResponse)
def inventory_latest_page() -> str:
    rows, error_message = _inventory_latest_state()
    card_parts: list[str] = []
    for row in rows:
        image_rows = row.get("inventory_item_images") or []
        marketing_rows = row.get("inventory_marketing_assets") or []
        first_image = image_rows[0] if image_rows else {}
        marketing = marketing_rows[0] if marketing_rows else {}
        title = str(marketing.get("listing_title") or row.get("normalized_product_name") or row.get("product_name") or "未命名商品")
        description = str(marketing.get("short_description") or row.get("condition_summary") or "待補商品說明")
        hashtags = marketing.get("hashtags") or []
        hashtag_text = " ".join(f"#{escape(str(tag).lstrip('#'))}" for tag in hashtags[:4])
        image_html = (
            f"<img class='thumb' src='{escape(str(first_image.get('image_url') or ''))}' alt='{escape(title)}' />"
            if first_image.get("image_url")
            else "<div class='thumb empty-thumb'>待補商品圖片</div>"
        )
        card_parts.append(
            "<article class='inv-card'>"
            f"<div class='thumb-wrap'>{image_html}</div>"
            f"<div class='inv-date'>{escape(str(row.get('warehouse_date', '')))}</div>"
            f"<h3>{escape(title)}</h3>"
            f"<p>{escape(description)}</p>"
            f"<div class='meta'>分類：{escape(str(row.get('category') or 'unknown'))}</div>"
            f"<div class='meta'>品牌/型號：{escape(str(row.get('brand') or 'unknown'))} / {escape(str(row.get('model') or 'unknown'))}</div>"
            f"<div class='price'>建議批發價：NT${escape(str(row.get('suggested_price') or '待估'))}</div>"
            f"<div class='meta'>最低可談：NT${escape(str(row.get('min_price') or '待估'))}</div>"
            f"<div class='meta'>圖片數：{len(image_rows)} 張</div>"
            f"<div class='meta'>信心：{escape(str(row.get('confidence') or 0))}</div>"
            f"<div class='meta'>{'需人工複核' if row.get('needs_review') else '可直接整理上架'}</div>"
            f"<div class='tags'>{hashtag_text}</div>"
            "</article>"
        )
    cards = "".join(card_parts)
    if not cards:
        cards = "<p class='empty'>目前還沒有最新入庫商品，請先執行 E 組入倉建檔。</p>"
    error_banner = ""
    if error_message:
        error_banner = f"<p class='error'>讀取入庫資料失敗：{escape(error_message)}</p>"
    return f"""
    <!doctype html>
    <html lang=\"zh-Hant\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>最新入庫批發專區</title>
        <style>
          :root {{
            --bg: #f4ede1;
            --panel: #fff9f0;
            --ink: #241b14;
            --muted: #6f6357;
            --line: #ddcfbf;
            --accent: #9f4d1f;
          }}
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: radial-gradient(circle at top, #f7efe0, #efe3d0 60%, #ead7bd 100%); color: var(--ink); }}
          .wrap {{ max-width: 1180px; margin: 0 auto; padding: 28px 20px 64px; }}
          .hero {{ background: rgba(255,249,240,.92); border: 1px solid var(--line); border-radius: 28px; padding: 28px; }}
          .eyebrow {{ font-size: 12px; letter-spacing: .1em; text-transform: uppercase; color: var(--accent); font-weight: 700; }}
          h1 {{ margin: 10px 0 12px; font-size: 44px; line-height: 1.05; }}
          p {{ margin: 0; color: var(--muted); line-height: 1.8; }}
          .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; margin-top: 24px; }}
          .inv-card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 22px; padding: 20px; box-shadow: 0 14px 30px rgba(0,0,0,.05); }}
          .thumb-wrap {{ margin: -20px -20px 16px; aspect-ratio: 4 / 3; background: #eadcc8; border-bottom: 1px solid var(--line); border-radius: 22px 22px 0 0; overflow: hidden; }}
          .thumb {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
          .empty-thumb {{ display: grid; place-items: center; color: var(--muted); font-weight: 700; }}
          .inv-date {{ font-size: 12px; color: var(--accent); font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
          h3 {{ margin: 10px 0 8px; font-size: 24px; line-height: 1.2; }}
          .meta {{ margin-top: 8px; color: var(--muted); font-size: 14px; }}
          .price {{ margin-top: 12px; font-size: 22px; font-weight: 700; }}
          .tags {{ margin-top: 12px; color: var(--accent); font-size: 13px; font-weight: 700; line-height: 1.6; }}
          .footer {{ margin-top: 32px; padding-top: 20px; border-top: 1px solid var(--line); color: var(--muted); font-size: 16px; }}
          .phone {{ font-size: 28px; font-weight: 800; color: var(--accent); margin-top: 8px; }}
          .error {{ margin-top: 14px; color: #a63d26; font-weight: 700; }}
          .empty {{ margin-top: 18px; padding: 20px; background: var(--panel); border-radius: 18px; border: 1px solid var(--line); }}
        </style>
      </head>
      <body>
        <div class=\"wrap\">
          <section class=\"hero\">
            <div class=\"eyebrow\">Wholesale Inventory</div>
            <h1>最新入庫<br />歡迎同行批發</h1>
            <p>這裡顯示 E 組已完成建檔的最新入庫商品。商品資料包含 AI 辨識品名、狀況摘要、建議售價與簡短行銷文，方便快速批發詢價與整理上架。</p>
            {error_banner}
          </section>
          <section class=\"grid\">{cards}</section>
          <footer class=\"footer\">
            <div>歡迎同行批發洽詢</div>
            <div class=\"phone\">{escape(settings.inventory_contact_phone)}</div>
          </footer>
        </div>
      </body>
    </html>
    """


@app.get("/inventory/latest/data")
def inventory_latest_data() -> dict[str, object]:
    rows, error_message = _inventory_latest_state()
    return {"rows": rows, "error": error_message}


@app.post("/runs")
def run_pipeline(request: dict) -> dict:
    try:
        query = request.get("query") or settings.default_query
        location = request.get("location") or settings.default_location_name
        max_results = int(request.get("max_results") or settings.default_max_results)

        from services import PipelineService

        response = PipelineService().run(
            query=query,
            location=location,
            max_results=max_results,
            publish=False,
        )
        return response.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/inventory/ingest")
def run_inventory_pipeline(request: dict) -> dict:
    try:
        folder_name = request.get("folder_name")

        from services import InventoryPipelineService

        response = InventoryPipelineService().run(folder_name=folder_name)
        return response.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
