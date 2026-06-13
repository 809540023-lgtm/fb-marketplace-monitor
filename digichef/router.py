from __future__ import annotations

from datetime import date, datetime
from html import escape
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from digichef.schemas import (
    IssueReportCreate,
    MarinadeBatchCreate,
    OvenTestCreate,
    PhotoAssetCreate,
    PurchaseLogCreate,
    TaskStatusUpdate,
)
from digichef.services import DigiChefCatalogService, DigiChefOperationsService
from digichef.store import DigiChefStore
from digichef.uploads import resolve_upload, save_upload

router = APIRouter(prefix="/digichef", tags=["digichef"])
store = DigiChefStore()
catalog_service = DigiChefCatalogService(store)
operations_service = DigiChefOperationsService(store)


def _money(value: float) -> str:
    return f"NT$ {value:,.0f}"


def _dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M")


def _page_shell(title: str, body: str) -> str:
    return f"""
    <!doctype html>
    <html lang="zh-Hant">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{escape(title)}</title>
        <style>
          :root {{
            --bg: #f5efe6;
            --panel: rgba(255, 250, 244, .92);
            --ink: #1f1a17;
            --muted: #64584f;
            --line: #d8cabc;
            --accent: #a44c22;
            --accent-dark: #5e6f52;
            --cream: #fff7ef;
            --warn: #c26a1b;
            --ok: #2f7a58;
          }}
          * {{ box-sizing: border-box; }}
          body {{
            margin: 0;
            color: var(--ink);
            background:
              radial-gradient(circle at top left, rgba(164, 76, 34, .14), transparent 25%),
              radial-gradient(circle at top right, rgba(94, 111, 82, .16), transparent 24%),
              linear-gradient(180deg, #f8f3eb 0%, var(--bg) 100%);
            font-family: "Avenir Next", "PingFang TC", "Noto Sans TC", sans-serif;
          }}
          h1, h2, h3 {{ font-family: "Iowan Old Style", "Palatino Linotype", "Noto Serif TC", serif; }}
          a {{ color: inherit; text-decoration: none; }}
          .wrap {{ max-width: 1240px; margin: 0 auto; padding: 28px 20px 64px; }}
          .nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            margin-bottom: 18px;
          }}
          .brand {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            font-weight: 800;
            letter-spacing: .04em;
          }}
          .brand-badge {{
            width: 38px;
            height: 38px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            color: #fff;
            background: linear-gradient(135deg, var(--accent), #d37335);
          }}
          .nav-links {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
          }}
          .nav-links a {{
            padding: 10px 14px;
            border-radius: 999px;
            border: 1px solid var(--line);
            background: rgba(255,255,255,.45);
          }}
          .hero, .section {{
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 28px;
            box-shadow: 0 18px 45px rgba(48, 29, 18, .07);
          }}
          .hero {{
            padding: 28px;
            overflow: hidden;
            position: relative;
          }}
          .hero::after {{
            content: "";
            position: absolute;
            right: -60px;
            top: -30px;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(164,76,34,.25) 0%, rgba(164,76,34,0) 70%);
          }}
          .section {{ margin-top: 18px; padding: 22px; }}
          .eyebrow {{
            color: var(--accent);
            font-size: 12px;
            letter-spacing: .12em;
            text-transform: uppercase;
            font-weight: 800;
          }}
          h1 {{ margin: 10px 0 12px; font-size: 48px; line-height: 1.02; }}
          h2 {{ margin: 0 0 12px; font-size: 28px; }}
          h3 {{ margin: 0 0 10px; font-size: 22px; }}
          p {{ color: var(--muted); line-height: 1.7; }}
          .actions {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 18px; }}
          .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 12px 16px;
            border-radius: 999px;
            font-weight: 800;
            color: #fff;
            background: var(--accent);
          }}
          .btn.alt {{ background: var(--accent-dark); }}
          .btn.ghost {{
            color: var(--ink);
            background: rgba(255,255,255,.7);
            border: 1px solid var(--line);
          }}
          .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
          }}
          .grid.two {{ grid-template-columns: repeat(2, 1fr); }}
          .card {{
            background: linear-gradient(180deg, #fffdf9 0%, #fff8f0 100%);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 18px;
          }}
          .metric {{
            padding: 18px;
            border-radius: 22px;
            border: 1px solid var(--line);
            background: var(--cream);
          }}
          .label {{
            font-size: 12px;
            letter-spacing: .08em;
            text-transform: uppercase;
            color: var(--muted);
          }}
          .value {{ margin-top: 8px; font-size: 30px; font-weight: 800; }}
          .muted {{ color: var(--muted); }}
          .meta {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-top: 12px;
          }}
          .chip {{
            display: inline-flex;
            align-items: center;
            padding: 7px 10px;
            border-radius: 999px;
            background: rgba(164, 76, 34, .10);
            color: var(--accent);
            font-size: 13px;
            font-weight: 700;
          }}
          .chip.ok {{ background: rgba(47, 122, 88, .12); color: var(--ok); }}
          .chip.warn {{ background: rgba(194, 106, 27, .12); color: var(--warn); }}
          .task-list, .form-grid {{ display: grid; gap: 14px; }}
          .task-list {{ grid-template-columns: repeat(3, 1fr); }}
          .table-wrap {{
            border: 1px solid var(--line);
            border-radius: 18px;
            overflow: hidden;
            background: #fff;
          }}
          table {{ width: 100%; border-collapse: collapse; }}
          th, td {{
            padding: 12px 14px;
            border-bottom: 1px solid #efe4d8;
            text-align: left;
            vertical-align: top;
            font-size: 14px;
          }}
          th {{ background: #fbf2e8; color: var(--muted); }}
          ul.clean {{
            margin: 0;
            padding-left: 18px;
            color: var(--muted);
          }}
          .form-grid {{ grid-template-columns: repeat(2, 1fr); }}
          form.stack {{ display: grid; gap: 10px; }}
          label.field {{
            display: grid;
            gap: 6px;
            color: var(--muted);
            font-size: 14px;
          }}
          input, select, textarea {{
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 11px 12px;
            background: #fff;
            color: var(--ink);
            font: inherit;
          }}
          textarea {{ min-height: 96px; resize: vertical; }}
          .status-todo, .status-new {{ color: var(--warn); font-weight: 800; }}
          .status-done, .status-approved, .status-active {{ color: var(--ok); font-weight: 800; }}
          .status-blocked, .status-retest {{ color: var(--accent); font-weight: 800; }}
          .footer-note {{
            margin-top: 18px;
            color: var(--muted);
            font-size: 13px;
          }}
          @media (max-width: 1000px) {{
            .grid, .grid.two, .task-list, .form-grid {{ grid-template-columns: 1fr; }}
            h1 {{ font-size: 36px; }}
          }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <nav class="nav">
            <a class="brand" href="/digichef">
              <span class="brand-badge">D</span>
              <span>猛見樂後 DigiChef</span>
            </a>
            <div class="nav-links">
              <a href="/digichef">首頁</a>
              <a href="/digichef/menu">套餐</a>
              <a href="/digichef/dashboard">營運</a>
              <a href="/digichef/sop">SOP</a>
              <a href="/digichef/system">系統</a>
            </div>
          </nav>
          {body}
        </div>
      </body>
    </html>
    """


def _product_cards() -> str:
    return "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>方案 {escape(item.code)}</div>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>{escape(item.description)}</p>"
        "<div class='meta'>"
        f"<span class='chip'>{escape(item.texture_style)}</span>"
        f"<span class='chip'>{item.protein_g:.1f}g 蛋白質</span>"
        f"<span class='chip'>{item.calories} kcal</span>"
        "</div>"
        f"<div class='value'>{_money(item.retail_price)}</div>"
        f"<p class='footer-note'>包月 {_money(item.subscription_price_total)} / 15 份，單份 {_money(item.subscription_unit_price)}</p>"
        f"<div class='actions'><a class='btn ghost' href='/digichef/menu/{escape(item.code)}'>查看詳情</a></div>"
        "</article>"
        for item in catalog_service.list_products()
    )


def _task_cards(dashboard) -> str:
    cards = []
    for item in dashboard.tasks:
        checklist = "".join(f"<li>{escape(step)}</li>" for step in item.checklist)
        notes = f"<p class='footer-note'>備註：{escape(item.notes)}</p>" if item.notes else ""
        decision = f"<p class='footer-note'>需決策：{escape(item.decision_needed)}</p>" if item.decision_needed else ""
        cards.append(
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.shift_label)} / {item.work_date.isoformat()}</div>"
            f"<h3>{escape(item.title)}</h3>"
            f"<div class='chip status-{escape(item.status)}'>{escape(item.status)}</div>"
            f"<ul class='clean'>{checklist}</ul>"
            f"{decision}{notes}"
            f"""
            <form class="stack" method="post" action="/digichef/dashboard/tasks/{item.id}/status">
              <label class="field">負責人<input name="owner_name" value="{escape(item.owner_name or '')}" /></label>
              <label class="field">狀態
                <select name="status">
                  <option value="todo" {"selected" if item.status == "todo" else ""}>todo</option>
                  <option value="in_progress" {"selected" if item.status == "in_progress" else ""}>in_progress</option>
                  <option value="done" {"selected" if item.status == "done" else ""}>done</option>
                  <option value="blocked" {"selected" if item.status == "blocked" else ""}>blocked</option>
                </select>
              </label>
              <label class="field">備註<textarea name="notes">{escape(item.notes or "")}</textarea></label>
              <button class="btn" type="submit">更新任務</button>
            </form>
            """
            "</article>"
        )
    return "".join(cards) or "<article class='card'><p>目前沒有待處理任務。</p></article>"


def _asset_link(url: str | None, label: str = "連結") -> str:
    if not url:
        return "-"
    return f"<a href='{escape(url)}' target='_blank'>{escape(label)}</a>"


def _stored_upload_url(upload: UploadFile | None, bucket: str, preferred_name: str | None = None) -> str | None:
    if upload is None or not upload.filename:
        return None
    return save_upload(upload, bucket=bucket, preferred_name=preferred_name)


@router.get("", response_class=HTMLResponse)
def digichef_home() -> str:
    dashboard = operations_service.dashboard()
    body = f"""
      <section class="hero">
        <div class="eyebrow">Smart Meal Ops</div>
        <h1>高蛋白智能餐盒，<br />從配方到出餐都有數據。</h1>
        <p>猛見樂後 DigiChef 第一版以標準化餐盒、包月模型與遠端營運為核心。先把 A-D 四款套餐與現場 SOP 做穩，再擴成完整訂閱制與後台系統。</p>
        <div class="actions">
          <a class="btn" href="/digichef/menu">查看套餐</a>
          <a class="btn alt" href="/digichef/dashboard">打開營運看板</a>
          <a class="btn ghost" href="/digichef/api/public/products">JSON API</a>
        </div>
      </section>
      <section class="section">
        <div class="grid">
          <div class="metric"><div class="label">套餐方案</div><div class="value">{dashboard.metrics.product_count}</div><div class="muted">A 至 D 四款標準主餐</div></div>
          <div class="metric"><div class="label">包月模式</div><div class="value">15</div><div class="muted">每月需取完 15 份</div></div>
          <div class="metric"><div class="label">今日工作日</div><div class="value">{dashboard.metrics.work_date.isoformat()}</div><div class="muted">以測試與 SOP 定版為優先</div></div>
          <div class="metric"><div class="label">開放 SOP</div><div class="value">{dashboard.metrics.approved_sop_count}</div><div class="muted">目前可用標準作業流程</div></div>
        </div>
      </section>
      <section class="section">
        <h2>標準套餐</h2>
        <div class="grid">{_product_cards()}</div>
      </section>
    """
    return _page_shell("猛見樂後 DigiChef", body)


@router.get("/menu", response_class=HTMLResponse)
def digichef_menu_page() -> str:
    body = f"""
      <section class="hero">
        <div class="eyebrow">Menu</div>
        <h1>套餐總覽</h1>
        <p>每份套餐包含主食、1 顆水煮蛋與 60g 烤地瓜。第一版先把營養、成本與烤製參數整合在同一頁，方便你未來直接轉成正式商品頁。</p>
      </section>
      <section class="section">
        <div class="grid">{_product_cards()}</div>
      </section>
    """
    return _page_shell("DigiChef 套餐總覽", body)


@router.get("/menu/{product_code}", response_class=HTMLResponse)
def digichef_product_detail_page(product_code: str) -> str:
    try:
        product = catalog_service.get_product(product_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Product not found") from exc
    profile = product.cooking_profile
    body = f"""
      <section class="hero">
        <div class="eyebrow">方案 {escape(product.code)}</div>
        <h1>{escape(product.name)}</h1>
        <p>{escape(product.description)}</p>
        <div class="meta">
          <span class="chip">{escape(product.texture_style)}</span>
          <span class="chip">{product.calories} kcal</span>
          <span class="chip">{product.protein_g:.1f}g 蛋白質</span>
          <span class="chip">{_money(product.retail_price)}</span>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h3>產品規格</h3>
            <p>主肉：{escape(product.protein_source)} / 原肉 {product.raw_weight_g}g</p>
            <p>配方：{escape(product.marinade_note)}</p>
            <p>主食成本：{_money(product.main_cost)} / 套餐綜合成本：{_money(product.combo_cost)}</p>
            <p>包月：{_money(product.subscription_price_total)}（單份 {_money(product.subscription_unit_price)}）</p>
          </article>
          <article class="card">
            <h3>烤製設定</h3>
            <p>模式：{escape(profile.mode)}</p>
            <p>溫度：{profile.temperature_c}°C / 濕度：{profile.humidity_pct}% / 風速：{profile.fan_speed}</p>
            <p>目標芯溫：{profile.target_core_temp_c}°C</p>
            <p>烤盤：{escape(profile.tray_type)}</p>
            <p>{escape(profile.finish_note)}</p>
          </article>
        </div>
      </section>
    """
    return _page_shell(product.name, body)


@router.get("/dashboard", response_class=HTMLResponse)
def digichef_dashboard_page() -> str:
    dashboard = operations_service.dashboard()
    tests_rows = "".join(
        "<tr>"
        f"<td>{escape(item.test_date.isoformat())}</td>"
        f"<td>{escape(item.test_code)}</td>"
        f"<td>{escape(item.product_code)}</td>"
        f"<td>{escape(item.oven_mode)}</td>"
        f"<td>{escape(item.decision)}</td>"
        f"<td>{item.actual_core_temp_c if item.actual_core_temp_c is not None else '-'}</td>"
        f"<td>{item.weight_loss_pct if item.weight_loss_pct is not None else '-'}</td>"
        f"<td>{_asset_link(item.photo_url, '照片')}</td>"
        f"<td>{escape(item.recorded_by)}</td>"
        "</tr>"
        for item in dashboard.recent_tests
    ) or "<tr><td colspan='9'>目前還沒有測試紀錄。</td></tr>"
    issue_rows = "".join(
        "<tr>"
        f"<td>{_dt(item.reported_at)}</td>"
        f"<td>{escape(item.category)}</td>"
        f"<td>{escape(item.title)}</td>"
        f"<td>{escape(item.severity)}</td>"
        f"<td>{escape(item.status)}</td>"
        f"<td>{_asset_link(item.attachment_url, '附件')}</td>"
        f"<td>{escape(item.reported_by)}</td>"
        "</tr>"
        for item in dashboard.open_issues
    ) or "<tr><td colspan='7'>目前沒有待處理異常。</td></tr>"
    photo_rows = "".join(
        (
            "<tr>"
            f"<td>{escape(item.captured_on.isoformat())}</td>"
            f"<td>{escape(item.product_code)}</td>"
            f"<td>{escape(item.stage)}</td>"
            f"<td>{escape(item.file_name)}</td>"
            + f"<td>{_asset_link(item.drive_url, '查看')}</td>"
            + f"<td>{escape(item.review_status)}</td>"
            + "</tr>"
        )
        for item in dashboard.recent_photos
    ) or "<tr><td colspan='6'>目前還沒有照片資產。</td></tr>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Operations Dashboard</div>
        <h1>遠端營運看板</h1>
        <p>今天先把測試、紀錄與 SOP 跑穩。這一版已支援建立進貨、醃製批次、烤製測試、照片紀錄與問題回報。</p>
        <div class="actions">
          <a class="btn" href="/digichef/api/admin/dashboard">Dashboard JSON</a>
          <a class="btn alt" href="/digichef/sop">查看 SOP</a>
        </div>
      </section>
      <section class="section">
        <div class="grid">
          <div class="metric"><div class="label">工作日</div><div class="value">{dashboard.metrics.work_date.isoformat()}</div><div class="muted">預設顯示最近待執行日</div></div>
          <div class="metric"><div class="label">任務完成</div><div class="value">{dashboard.metrics.task_completed}/{dashboard.metrics.task_total}</div><div class="muted">blocked: {dashboard.metrics.task_blocked}</div></div>
          <div class="metric"><div class="label">當日測試</div><div class="value">{dashboard.metrics.test_count}</div><div class="muted">approved: {dashboard.metrics.approved_test_count}</div></div>
          <div class="metric"><div class="label">待處理問題</div><div class="value">{dashboard.metrics.open_issue_count}</div><div class="muted">優先盯住會卡出餐的異常</div></div>
        </div>
      </section>
      <section class="section">
        <h2>今日任務</h2>
        <div class="task-list">{_task_cards(dashboard)}</div>
      </section>
      <section class="section" id="forms">
        <h2>快速建檔</h2>
        <p>現場員工可直接用手機開這頁，點「直接拍照上傳」後用相機拍照，不需要先存到別的平台。</p>
        <div class="form-grid">
          <article class="card">
            <h3>新增進貨紀錄</h3>
            <form class="stack" method="post" action="/digichef/dashboard/forms/purchases" enctype="multipart/form-data">
              <label class="field">日期<input type="date" name="purchase_date" required /></label>
              <label class="field">供應商<input name="supplier_name" required /></label>
              <label class="field">品項<input name="item_name" required /></label>
              <label class="field">規格<input name="item_spec" required /></label>
              <label class="field">數量<input type="number" step="0.01" name="quantity" required /></label>
              <label class="field">單位<input name="unit" value="kg" required /></label>
              <label class="field">單價<input type="number" step="0.01" name="unit_cost" required /></label>
              <label class="field">存放位置<input name="storage_location" value="冷藏" required /></label>
              <label class="field">檢查結果
                <select name="check_result">
                  <option value="pass">pass</option>
                  <option value="watch">watch</option>
                  <option value="reject">reject</option>
                </select>
              </label>
              <label class="field">照片連結<input name="photo_url" /></label>
              <label class="field">直接拍照上傳<input type="file" name="photo_file" accept="image/*" capture="environment" /></label>
              <label class="field">記錄人<input name="recorded_by" required /></label>
              <label class="field">備註<textarea name="notes"></textarea></label>
              <button class="btn" type="submit">建立進貨紀錄</button>
            </form>
          </article>
          <article class="card">
            <h3>新增醃製批次</h3>
            <form class="stack" method="post" action="/digichef/dashboard/forms/batches" enctype="multipart/form-data">
              <label class="field">批次編號<input name="batch_code" required /></label>
              <label class="field">方案
                <select name="product_code">
                  <option value="A">A</option>
                  <option value="B">B</option>
                  <option value="C">C</option>
                  <option value="D">D</option>
                </select>
              </label>
              <label class="field">肉品<input name="protein_source" required /></label>
              <label class="field">原肉重量(g)<input type="number" step="0.01" name="raw_weight_g" required /></label>
              <label class="field">份數<input type="number" name="portion_count" required /></label>
              <label class="field">米酒(cc)<input type="number" step="0.01" name="rice_wine_cc" value="0" required /></label>
              <label class="field">蘋果醋(cc)<input type="number" step="0.01" name="apple_vinegar_cc" value="0" required /></label>
              <label class="field">日清粉(g)<input type="number" step="0.01" name="flour_g" value="0" required /></label>
              <label class="field">開始時間<input type="datetime-local" name="marinade_started_at" required /></label>
              <label class="field">預計出爐日<input type="date" name="planned_cook_date" required /></label>
              <label class="field">狀態
                <select name="status">
                  <option value="planned">planned</option>
                  <option value="marinating">marinating</option>
                  <option value="ready_for_test">ready_for_test</option>
                </select>
              </label>
              <label class="field">負責人<input name="handled_by" required /></label>
              <label class="field">備註<textarea name="notes"></textarea></label>
              <button class="btn" type="submit">建立批次</button>
            </form>
          </article>
          <article class="card">
            <h3>新增測試紀錄</h3>
            <form class="stack" method="post" action="/digichef/dashboard/forms/tests" enctype="multipart/form-data">
              <label class="field">測試編號<input name="test_code" required /></label>
              <label class="field">日期<input type="date" name="test_date" required /></label>
              <label class="field">方案<input name="product_code" required /></label>
              <label class="field">口感路徑<input name="texture_style" required /></label>
              <label class="field">烤箱模式<input name="oven_mode" required /></label>
              <label class="field">溫度(°C)<input type="number" name="temperature_c" required /></label>
              <label class="field">濕度(%)<input type="number" name="humidity_pct" required /></label>
              <label class="field">風速<input type="number" name="fan_speed" required /></label>
              <label class="field">目標芯溫<input type="number" name="target_core_temp_c" required /></label>
              <label class="field">實測芯溫<input type="number" step="0.1" name="actual_core_temp_c" /></label>
              <label class="field">烤前重量(g)<input type="number" step="0.01" name="raw_weight_g" required /></label>
              <label class="field">烤後重量(g)<input type="number" step="0.01" name="cooked_weight_g" /></label>
              <label class="field">外觀評分<input type="number" min="1" max="5" name="appearance_score" /></label>
              <label class="field">口感評分<input type="number" min="1" max="5" name="taste_score" /></label>
              <label class="field">多汁度評分<input type="number" min="1" max="5" name="juiciness_score" /></label>
              <label class="field">照片連結<input name="photo_url" /></label>
              <label class="field">直接拍照上傳<input type="file" name="photo_file" accept="image/*" capture="environment" /></label>
              <label class="field">結論<textarea name="notes"></textarea></label>
              <label class="field">決策
                <select name="decision">
                  <option value="pending">pending</option>
                  <option value="approved">approved</option>
                  <option value="retest">retest</option>
                </select>
              </label>
              <label class="field">記錄人<input name="recorded_by" required /></label>
              <button class="btn" type="submit">建立測試紀錄</button>
            </form>
          </article>
          <article class="card">
            <h3>新增問題回報</h3>
            <form class="stack" method="post" action="/digichef/dashboard/forms/issues" enctype="multipart/form-data">
              <label class="field">發生時間<input type="datetime-local" name="reported_at" required /></label>
              <label class="field">分類<input name="category" required /></label>
              <label class="field">標題<input name="title" required /></label>
              <label class="field">描述<textarea name="description" required></textarea></label>
              <label class="field">當下處理<textarea name="action_taken" required></textarea></label>
              <label class="field">嚴重度
                <select name="severity">
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </label>
              <label class="field">是否卡服務
                <select name="blocks_service">
                  <option value="false">false</option>
                  <option value="true">true</option>
                </select>
              </label>
              <label class="field">需老闆決策
                <select name="needs_owner_decision">
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
              </label>
              <label class="field">現場照片上傳<input type="file" name="attachment_file" accept="image/*" capture="environment" /></label>
              <label class="field">回報人<input name="reported_by" required /></label>
              <button class="btn" type="submit">建立問題回報</button>
            </form>
          </article>
          <article class="card">
            <h3>新增成品照片</h3>
            <form class="stack" method="post" action="/digichef/dashboard/forms/photos" enctype="multipart/form-data">
              <label class="field">拍攝日<input type="date" name="captured_on" required /></label>
              <label class="field">方案<input name="product_code" required /></label>
              <label class="field">階段<input name="stage" placeholder="oven / cut / box" required /></label>
              <label class="field">檔名<input name="file_name" placeholder="可留空，自動帶入檔名" /></label>
              <label class="field">外部連結<input name="drive_url" placeholder="可留空，改用直接上傳" /></label>
              <label class="field">直接拍照上傳<input type="file" name="photo_file" accept="image/*" capture="environment" /></label>
              <label class="field">用途<input name="purpose" value="測試紀錄" required /></label>
              <label class="field">拍攝人<input name="captured_by" required /></label>
              <label class="field">審核狀態
                <select name="review_status">
                  <option value="pending">pending</option>
                  <option value="approved">approved</option>
                  <option value="reshoot">reshoot</option>
                </select>
              </label>
              <label class="field">備註<textarea name="notes"></textarea></label>
              <button class="btn" type="submit">建立照片紀錄</button>
            </form>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>最新測試</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>日期</th><th>編號</th><th>方案</th><th>模式</th><th>決策</th><th>芯溫</th><th>失重率</th><th>照片</th><th>記錄人</th></tr></thead>
            <tbody>{tests_rows}</tbody>
          </table>
        </div>
      </section>
      <section class="section">
        <h2>待處理問題</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>時間</th><th>分類</th><th>標題</th><th>嚴重度</th><th>狀態</th><th>附件</th><th>回報人</th></tr></thead>
            <tbody>{issue_rows}</tbody>
          </table>
        </div>
      </section>
      <section class="section">
        <h2>最近照片</h2>
        <div class="table-wrap">
          <table>
            <thead><tr><th>日期</th><th>方案</th><th>階段</th><th>檔名</th><th>連結</th><th>狀態</th></tr></thead>
            <tbody>{photo_rows}</tbody>
          </table>
        </div>
      </section>
    """
    return _page_shell("DigiChef 營運看板", body)


@router.get("/sop", response_class=HTMLResponse)
def digichef_sop_page() -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(item.code)}</td>"
        f"<td>{escape(item.category)}</td>"
        f"<td>{escape(item.title)}</td>"
        f"<td>{escape(item.version)}</td>"
        f"<td>{escape(item.status)}</td>"
        f"<td>{escape(item.completion_standard)}</td>"
        "</tr>"
        for item in operations_service.list_sops()
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">SOP Registry</div>
        <h1>SOP 主表</h1>
        <p>第一版把開工、進貨、醃製、測試、拍照、日結集中管理，後續可再加入版本控管與核准流程。</p>
      </section>
      <section class="section">
        <div class="table-wrap">
          <table>
            <thead><tr><th>編號</th><th>分類</th><th>名稱</th><th>版本</th><th>狀態</th><th>完成標準</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
      </section>
    """
    return _page_shell("DigiChef SOP", body)


@router.get("/system", response_class=HTMLResponse)
def digichef_system_page() -> str:
    readiness = store.repository.readiness()
    dashboard = operations_service.dashboard()
    body = f"""
      <section class="hero">
        <div class="eyebrow">System</div>
        <h1>系統狀態</h1>
        <p>目前 DigiChef 採用 JSON snapshot 持久化，方便你先把資料流跑順，再往資料庫與正式權限升級。</p>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h3>Storage</h3>
            <p>backend: {escape(readiness["backend"])}</p>
            <p>mode: {escape(readiness["repository_mode"])}</p>
            <p>path: {escape(readiness["json_path"])}</p>
          </article>
          <article class="card">
            <h3>資料量</h3>
            <p>products: {dashboard.metrics.product_count}</p>
            <p>tests: {len(operations_service.list_oven_tests())}</p>
            <p>issues: {len(operations_service.list_issues())}</p>
            <p>photos: {len(operations_service.list_photo_assets())}</p>
          </article>
        </div>
      </section>
    """
    return _page_shell("DigiChef 系統狀態", body)


@router.get("/uploads/{file_path:path}")
def digichef_uploaded_asset(file_path: str) -> FileResponse:
    try:
        target = resolve_upload(file_path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Upload not found") from exc
    return FileResponse(target)


@router.get("/api/public/products")
def digichef_products_api() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in catalog_service.list_products()]}


@router.get("/api/public/products/{product_code}")
def digichef_product_api(product_code: str) -> dict[str, object]:
    try:
        product = catalog_service.get_product(product_code)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Product not found") from exc
    return {"data": product.model_dump(mode="json")}


@router.get("/api/admin/dashboard")
def digichef_dashboard_api() -> dict[str, object]:
    return {"data": operations_service.dashboard().model_dump(mode="json")}


@router.get("/api/admin/purchases")
def digichef_purchases_api() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in operations_service.list_purchases()]}


@router.post("/api/admin/purchases")
def digichef_create_purchase_api(payload: PurchaseLogCreate) -> dict[str, object]:
    return {"data": operations_service.create_purchase(payload).model_dump(mode="json")}


@router.get("/api/admin/batches")
def digichef_batches_api() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in operations_service.list_batches()]}


@router.post("/api/admin/batches")
def digichef_create_batch_api(payload: MarinadeBatchCreate) -> dict[str, object]:
    return {"data": operations_service.create_batch(payload).model_dump(mode="json")}


@router.get("/api/admin/tests")
def digichef_tests_api() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in operations_service.list_oven_tests()]}


@router.post("/api/admin/tests")
def digichef_create_test_api(payload: OvenTestCreate) -> dict[str, object]:
    return {"data": operations_service.create_oven_test(payload).model_dump(mode="json")}


@router.get("/api/admin/photos")
def digichef_photos_api() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in operations_service.list_photo_assets()]}


@router.post("/api/admin/photos")
def digichef_create_photo_api(payload: PhotoAssetCreate) -> dict[str, object]:
    return {"data": operations_service.create_photo_asset(payload).model_dump(mode="json")}


@router.post("/api/admin/uploads")
def digichef_upload_api(
    bucket: str = Form(default="misc"),
    preferred_name: str | None = Form(default=None),
    file: UploadFile = File(...),
) -> dict[str, object]:
    asset_url = save_upload(file, bucket=bucket, preferred_name=preferred_name)
    return {"data": {"url": asset_url, "bucket": bucket}}


@router.get("/api/admin/issues")
def digichef_issues_api() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in operations_service.list_issues()]}


@router.post("/api/admin/issues")
def digichef_create_issue_api(payload: IssueReportCreate) -> dict[str, object]:
    return {"data": operations_service.create_issue(payload).model_dump(mode="json")}


@router.get("/api/admin/sops")
def digichef_sops_api() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in operations_service.list_sops()]}


@router.post("/api/admin/tasks/{task_id}/status")
def digichef_update_task_status_api(task_id: UUID, payload: TaskStatusUpdate) -> dict[str, object]:
    try:
        task = operations_service.update_task_status(task_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    return {"data": task.model_dump(mode="json")}


@router.post("/dashboard/tasks/{task_id}/status")
def digichef_update_task_status_form(
    task_id: UUID,
    status: str = Form(...),
    owner_name: str | None = Form(default=None),
    notes: str | None = Form(default=None),
) -> RedirectResponse:
    operations_service.update_task_status(task_id, TaskStatusUpdate(status=status, owner_name=owner_name, notes=notes))
    return RedirectResponse(url="/digichef/dashboard", status_code=303)


@router.post("/dashboard/forms/purchases")
def digichef_create_purchase_form(
    purchase_date: date = Form(...),
    supplier_name: str = Form(...),
    item_name: str = Form(...),
    item_spec: str = Form(...),
    quantity: float = Form(...),
    unit: str = Form(...),
    unit_cost: float = Form(...),
    storage_location: str = Form(...),
    check_result: str = Form(...),
    photo_url: str | None = Form(default=None),
    photo_file: UploadFile | None = File(default=None),
    recorded_by: str = Form(...),
    notes: str | None = Form(default=None),
) -> RedirectResponse:
    stored_photo_url = _stored_upload_url(photo_file, bucket="purchases", preferred_name=item_name)
    operations_service.create_purchase(
        PurchaseLogCreate(
            purchase_date=purchase_date,
            supplier_name=supplier_name,
            item_name=item_name,
            item_spec=item_spec,
            quantity=quantity,
            unit=unit,
            unit_cost=unit_cost,
            storage_location=storage_location,
            check_result=check_result,
            photo_url=stored_photo_url or photo_url,
            recorded_by=recorded_by,
            notes=notes,
        )
    )
    return RedirectResponse(url="/digichef/dashboard#forms", status_code=303)


@router.post("/dashboard/forms/batches")
def digichef_create_batch_form(
    batch_code: str = Form(...),
    product_code: str = Form(...),
    protein_source: str = Form(...),
    raw_weight_g: float = Form(...),
    portion_count: int = Form(...),
    rice_wine_cc: float = Form(...),
    apple_vinegar_cc: float = Form(...),
    flour_g: float = Form(...),
    marinade_started_at: datetime = Form(...),
    planned_cook_date: date = Form(...),
    status: str = Form(...),
    handled_by: str = Form(...),
    notes: str | None = Form(default=None),
) -> RedirectResponse:
    operations_service.create_batch(
        MarinadeBatchCreate(
            batch_code=batch_code,
            product_code=product_code,
            protein_source=protein_source,
            raw_weight_g=raw_weight_g,
            portion_count=portion_count,
            rice_wine_cc=rice_wine_cc,
            apple_vinegar_cc=apple_vinegar_cc,
            flour_g=flour_g,
            marinade_started_at=marinade_started_at,
            planned_cook_date=planned_cook_date,
            status=status,
            handled_by=handled_by,
            notes=notes,
        )
    )
    return RedirectResponse(url="/digichef/dashboard#forms", status_code=303)


@router.post("/dashboard/forms/tests")
def digichef_create_test_form(
    test_code: str = Form(...),
    test_date: date = Form(...),
    product_code: str = Form(...),
    texture_style: str = Form(...),
    oven_mode: str = Form(...),
    temperature_c: int = Form(...),
    humidity_pct: int = Form(...),
    fan_speed: int = Form(...),
    target_core_temp_c: int = Form(...),
    actual_core_temp_c: float | None = Form(default=None),
    raw_weight_g: float = Form(...),
    cooked_weight_g: float | None = Form(default=None),
    appearance_score: int | None = Form(default=None),
    taste_score: int | None = Form(default=None),
    juiciness_score: int | None = Form(default=None),
    photo_url: str | None = Form(default=None),
    photo_file: UploadFile | None = File(default=None),
    notes: str | None = Form(default=None),
    decision: str = Form(...),
    recorded_by: str = Form(...),
) -> RedirectResponse:
    stored_photo_url = _stored_upload_url(photo_file, bucket="tests", preferred_name=test_code)
    operations_service.create_oven_test(
        OvenTestCreate(
            test_code=test_code,
            test_date=test_date,
            product_code=product_code,
            texture_style=texture_style,
            oven_mode=oven_mode,
            temperature_c=temperature_c,
            humidity_pct=humidity_pct,
            fan_speed=fan_speed,
            target_core_temp_c=target_core_temp_c,
            actual_core_temp_c=actual_core_temp_c,
            raw_weight_g=raw_weight_g,
            cooked_weight_g=cooked_weight_g,
            appearance_score=appearance_score,
            taste_score=taste_score,
            juiciness_score=juiciness_score,
            photo_url=stored_photo_url or photo_url,
            notes=notes,
            decision=decision,
            recorded_by=recorded_by,
        )
    )
    return RedirectResponse(url="/digichef/dashboard#forms", status_code=303)


@router.post("/dashboard/forms/issues")
def digichef_create_issue_form(
    reported_at: datetime = Form(...),
    category: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    action_taken: str = Form(...),
    severity: str = Form(...),
    blocks_service: str = Form(...),
    needs_owner_decision: str = Form(...),
    attachment_file: UploadFile | None = File(default=None),
    reported_by: str = Form(...),
) -> RedirectResponse:
    attachment_url = _stored_upload_url(attachment_file, bucket="issues", preferred_name=title)
    operations_service.create_issue(
        IssueReportCreate(
            reported_at=reported_at,
            category=category,
            title=title,
            description=description,
            action_taken=action_taken,
            severity=severity,
            blocks_service=blocks_service == "true",
            needs_owner_decision=needs_owner_decision == "true",
            reported_by=reported_by,
            attachment_url=attachment_url,
        )
    )
    return RedirectResponse(url="/digichef/dashboard#forms", status_code=303)


@router.post("/dashboard/forms/photos")
def digichef_create_photo_form(
    captured_on: date = Form(...),
    product_code: str = Form(...),
    stage: str = Form(...),
    file_name: str | None = Form(default=None),
    drive_url: str | None = Form(default=None),
    photo_file: UploadFile | None = File(default=None),
    purpose: str = Form(...),
    captured_by: str = Form(...),
    review_status: str = Form(...),
    notes: str | None = Form(default=None),
) -> RedirectResponse:
    uploaded_photo_url = _stored_upload_url(photo_file, bucket="photos", preferred_name=file_name or f"{product_code}-{stage}")
    resolved_file_name = file_name or (photo_file.filename if photo_file and photo_file.filename else f"{product_code}_{captured_on.isoformat()}_{stage}.jpg")
    operations_service.create_photo_asset(
        PhotoAssetCreate(
            captured_on=captured_on,
            product_code=product_code,
            stage=stage,
            file_name=resolved_file_name,
            drive_url=uploaded_photo_url or drive_url,
            purpose=purpose,
            captured_by=captured_by,
            review_status=review_status,
            notes=notes,
        )
    )
    return RedirectResponse(url="/digichef/dashboard#forms", status_code=303)
