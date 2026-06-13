from __future__ import annotations

from html import escape
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from config import settings
from investment_plans.schemas import InvestmentPlanRequest, LineSubscriptionRequest, PlanReviewRequest
from investment_plans.service import InvestmentPlanStore

router = APIRouter(prefix="/investment-plans", tags=["investment-plans"])
store = InvestmentPlanStore()


def _api_payload(data: object) -> dict[str, object]:
    return {"data": data, "error": None}


def _format_money(value: float | None) -> str:
    if value is None:
        return "-"
    return f"NT$ {value:,.0f}"


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.replace("，", ",").split(",") if item.strip()]


def _parse_uuid(value: str | None) -> UUID | None:
    if not value:
        return None
    return UUID(value)


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
            --bg: #f7f8f2;
            --panel: #ffffff;
            --ink: #17201b;
            --muted: #5d6b63;
            --line: #d9dfd7;
            --accent: #25665b;
            --accent-2: #9b4f2f;
            --soft: #eef3eb;
          }}
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: var(--bg); color: var(--ink); }}
          .wrap {{ max-width: 1120px; margin: 0 auto; padding: 28px 20px 64px; }}
          .topbar {{ display: flex; justify-content: space-between; align-items: center; gap: 14px; margin-bottom: 18px; }}
          .brand {{ color: var(--accent); font-weight: 800; text-decoration: none; }}
          .hero, .section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 22px; }}
          .section {{ margin-top: 16px; }}
          .eyebrow {{ color: var(--accent-2); font-size: 12px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
          h1 {{ margin: 8px 0 10px; font-size: 36px; line-height: 1.12; }}
          h2 {{ margin: 0 0 12px; font-size: 22px; }}
          h3 {{ margin: 0 0 8px; font-size: 18px; }}
          p {{ color: var(--muted); line-height: 1.7; }}
          .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
          .grid.three {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
          .card {{ border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: #fff; }}
          .callout {{ border-left: 4px solid var(--accent); background: var(--soft); border-radius: 8px; padding: 16px; }}
          .metric {{ background: var(--soft); border-radius: 8px; padding: 14px; }}
          .label {{ color: var(--muted); font-size: 13px; }}
          .value {{ margin-top: 6px; font-size: 24px; font-weight: 800; }}
          .actions {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 16px; }}
          .btn, button {{ border: 0; border-radius: 8px; background: var(--accent); color: #fff; padding: 11px 14px; font: inherit; font-weight: 800; text-decoration: none; cursor: pointer; }}
          .btn.alt {{ background: var(--accent-2); }}
          form.stack {{ display: grid; gap: 12px; }}
          label {{ display: grid; gap: 6px; color: var(--muted); font-size: 14px; }}
          input, select, textarea {{ width: 100%; border: 1px solid var(--line); border-radius: 8px; padding: 11px 12px; font: inherit; background: #fff; color: var(--ink); }}
          textarea {{ min-height: 84px; resize: vertical; }}
          ul {{ margin: 0; padding-left: 20px; color: var(--muted); line-height: 1.7; }}
          .plan-list {{ display: grid; gap: 12px; }}
          @media (max-width: 820px) {{
            h1 {{ font-size: 30px; }}
            .grid, .grid.three {{ grid-template-columns: 1fr; }}
            .topbar {{ align-items: flex-start; flex-direction: column; }}
          }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="topbar">
            <a class="brand" href="/investment-plans">AI 單股投資計畫</a>
            <a class="btn alt" href="/investment-plans/new">建立計畫</a>
          </div>
          {body}
        </div>
      </body>
    </html>
    """


@router.get("", response_class=HTMLResponse)
def investment_plan_home(user_id: str | None = Query(default=None)) -> str:
    plans = store.list_for_user(user_id)
    cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(plan.request.plan_type)}</div>"
        f"<h3>{escape(plan.title)}</h3>"
        f"<p>{escape(plan.summary)}</p>"
        f"<div class='actions'><a class='btn' href='/investment-plans/{plan.id}'>查看計畫</a></div>"
        "</article>"
        for plan in plans[:12]
    )
    if not cards:
        cards = "<p>目前還沒有投資計畫。</p>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Single Stock Planning</div>
        <h1>完整分析 + 每月零存整付</h1>
        <p>會員可以針對單一股票建立完整分析計畫，也可以輸入每月 3,000 元、5,000 元或自訂金額，取得可追蹤的投入規則。</p>
        <div class="actions">
          <a class="btn" href="/investment-plans/new?plan_type=recurring_investment">零存整付</a>
          <a class="btn alt" href="/investment-plans/new?plan_type=full_analysis">完整分析</a>
          <a class="btn" href="/investment-plans/line-subscribe">LINE 每日推播</a>
        </div>
      </section>
      <section class="section">
        <h2>已建立計畫</h2>
        <div class="plan-list">{cards}</div>
      </section>
    """
    return _page_shell("AI 單股投資計畫", body)


@router.get("/new", response_class=HTMLResponse)
def new_investment_plan(plan_type: str = Query(default="recurring_investment")) -> str:
    recurring_selected = "selected" if plan_type == "recurring_investment" else ""
    full_selected = "selected" if plan_type == "full_analysis" else ""
    body = f"""
      <section class="hero">
        <div class="eyebrow">Create Plan</div>
        <h1>建立會員單股投資計畫</h1>
        <p>第一版先用手動輸入股價與風險條件；未來可接即時股價、財報、月營收與 AI 深度分析。</p>
      </section>
      <section class="section">
        <form class="stack" method="post" action="/investment-plans/create">
          <div class="grid">
            <label>會員 ID<input name="user_id" value="guest" required /></label>
            <label>計畫類型
              <select name="plan_type">
                <option value="recurring_investment" {recurring_selected}>零存整付投資計畫</option>
                <option value="full_analysis" {full_selected}>完整股票分析計畫</option>
              </select>
            </label>
            <label>股票代號<input name="stock_symbol" value="2408" required /></label>
            <label>股票名稱<input name="stock_name" value="南亞科" /></label>
            <label>目前股價<input type="number" step="0.01" name="current_price" value="324" required /></label>
            <label>每月投入金額<input type="number" step="1" name="monthly_amount" value="3000" /></label>
            <label>初始投入金額<input type="number" step="1" name="initial_amount" value="0" /></label>
            <label>投資年限<input type="number" step="1" name="investment_years" value="5" /></label>
            <label>風險偏好
              <select name="risk_profile">
                <option value="conservative">保守</option>
                <option value="balanced" selected>穩健</option>
                <option value="aggressive">積極</option>
              </select>
            </label>
            <label>產業屬性
              <select name="industry_cycle">
                <option value="unknown">未知</option>
                <option value="stable">穩定型</option>
                <option value="cyclical" selected>景氣循環型</option>
                <option value="growth">成長型</option>
              </select>
            </label>
            <label>估值狀態
              <select name="valuation_level">
                <option value="unknown">未知</option>
                <option value="undervalued">偏低</option>
                <option value="fair">合理</option>
                <option value="expensive" selected>偏高</option>
                <option value="overheated">過熱</option>
              </select>
            </label>
            <label>最大可承受虧損 %<input type="number" step="1" name="max_loss_percent" value="25" /></label>
            <label>目標報酬 %<input type="number" step="1" name="target_return_percent" value="50" /></label>
            <label>目前平均成本<input type="number" step="0.01" name="average_cost" /></label>
            <label>目前持有股數<input type="number" step="0.0001" name="shares_owned" value="0" /></label>
          </div>
          <label>原料/成本追蹤<textarea name="tracked_materials">DRAM, DDR4, DDR5, 矽晶圓, 光阻, 特用氣體, 封裝材料</textarea></label>
          <label>公開事件追蹤關鍵字<textarea name="public_event_keywords">台塑 日本 行程, 南亞科 日本 客戶, 台塑集團 日本 投資, DRAM 日本 供應鏈</textarea></label>
          <button type="submit">產生投資計畫</button>
        </form>
      </section>
    """
    return _page_shell("建立投資計畫", body)


@router.post("/create")
def create_investment_plan_form(
    user_id: str = Form("guest"),
    stock_symbol: str = Form(...),
    stock_name: str | None = Form(None),
    plan_type: str = Form(...),
    current_price: float = Form(...),
    monthly_amount: float | None = Form(None),
    initial_amount: float = Form(0),
    investment_years: int = Form(5),
    risk_profile: str = Form("balanced"),
    max_loss_percent: float = Form(25),
    target_return_percent: float = Form(50),
    average_cost: float | None = Form(None),
    shares_owned: float = Form(0),
    industry_cycle: str = Form("unknown"),
    valuation_level: str = Form("unknown"),
    tracked_materials: str | None = Form(None),
    public_event_keywords: str | None = Form(None),
) -> RedirectResponse:
    try:
        request = InvestmentPlanRequest(
            user_id=user_id,
            stock_symbol=stock_symbol,
            stock_name=stock_name or None,
            plan_type=plan_type,
            current_price=current_price,
            monthly_amount=monthly_amount,
            initial_amount=initial_amount,
            investment_years=investment_years,
            risk_profile=risk_profile,
            max_loss_percent=max_loss_percent,
            target_return_percent=target_return_percent,
            average_cost=average_cost,
            shares_owned=shares_owned,
            industry_cycle=industry_cycle,
            valuation_level=valuation_level,
            tracked_materials=_split_csv(tracked_materials),
            public_event_keywords=_split_csv(public_event_keywords),
        )
        plan = store.create(request)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(url=f"/investment-plans/{plan.id}", status_code=303)


@router.get("/line-subscribe", response_class=HTMLResponse)
def line_subscribe_page() -> str:
    line_url = settings.line_official_account_url or ""
    action = (
        f"<a class='btn' href='{escape(line_url)}'>加入 LINE 每日推播</a>"
        if line_url
        else "<p>尚未設定 LINE_OFFICIAL_ACCOUNT_URL。設定後，這裡會顯示一鍵加入 LINE 官方帳號的連結。</p>"
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">LINE Subscribe</div>
        <h1>每天用 LINE 收 2408 投資更新</h1>
        <p>會員只要點擊加入官方帳號，後續即可接收每日股價、原料、產業與公開事件追蹤摘要。正式推播前仍需完成 LINE userId 綁定與會員同意紀錄。</p>
        <div class="actions">{action}</div>
      </section>
      <section class="section">
        <h2>建立推播訂閱</h2>
        <form class="stack" method="post" action="/investment-plans/line-subscribe">
          <div class="grid">
            <label>會員 ID<input name="user_id" value="guest" required /></label>
            <label>計畫 ID<input name="plan_id" placeholder="可留空，或填入投資計畫 ID" /></label>
            <label>LINE userId<input name="line_user_id" placeholder="後台綁定後可填入，會員可先留空" /></label>
            <label>推播頻率
              <select name="frequency">
                <option value="daily" selected>每天</option>
                <option value="weekly">每週</option>
              </select>
            </label>
          </div>
          <button type="submit">記錄 LINE 訂閱</button>
        </form>
      </section>
      <section class="section">
        <h2>推播內容</h2>
        <ul>
          <li>2408 最新股價與本月計畫建議。</li>
          <li>DRAM、DDR4、DDR5、矽晶圓、光阻、特用氣體等成本/供應鏈訊號。</li>
          <li>台塑、南亞科、日本客戶與合作消息等公開事件追蹤。</li>
          <li>提醒會員本月應買進、加碼、暫停、停利或做風險檢查。</li>
        </ul>
      </section>
    """
    return _page_shell("LINE 每日推播訂閱", body)


@router.post("/line-subscribe")
def create_line_subscription_form(
    user_id: str = Form(...),
    plan_id: str | None = Form(None),
    line_user_id: str | None = Form(None),
    frequency: str = Form("daily"),
) -> RedirectResponse:
    try:
        request = LineSubscriptionRequest(
            user_id=user_id,
            plan_id=_parse_uuid(plan_id),
            line_user_id=line_user_id or None,
            frequency=frequency,
            consent=True,
        )
        store.create_line_subscription(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Investment plan not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(url=f"/investment-plans/line-subscribe?user_id={user_id}", status_code=303)


@router.get("/{plan_id}", response_class=HTMLResponse)
def investment_plan_detail(plan_id: UUID) -> str:
    try:
        plan = store.get(plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Investment plan not found") from exc

    metrics = f"""
      <div class="metric"><div class="label">固定投入比例</div><div class="value">{plan.allocation.fixed_buy_ratio:.0%}</div></div>
      <div class="metric"><div class="label">現金保留比例</div><div class="value">{plan.allocation.cash_reserve_ratio:.0%}</div></div>
      <div class="metric"><div class="label">每月固定投入</div><div class="value">{_format_money(plan.allocation.monthly_fixed_buy_amount)}</div></div>
    """
    bands = "".join(
        f"<article class='card'><h3>{escape(item.name)}：{_format_money(item.price)}</h3><p>{escape(item.action)}</p></article>"
        for item in plan.price_bands
    )
    rules = "".join(f"<li>{escape(item.trigger)}：{escape(item.action)}</li>" for item in plan.action_rules)
    indicators = "".join(f"<li>{escape(item)}</li>" for item in plan.tracking_indicators)
    risks = "".join(f"<li>{escape(item)}</li>" for item in plan.risk_notes)
    next_items = "".join(f"<li>{escape(item)}</li>" for item in plan.next_review_items)
    latest_review = store.latest_review(plan.id)
    latest_review_html = ""
    if latest_review:
        latest_review_html = f"""
          <section class="section callout">
            <div class="eyebrow">Latest Monthly Review</div>
            <h2>{escape(latest_review.recommendation_label)}</h2>
            <p>{escape(latest_review.summary)}</p>
            <p>價格位置：{escape(latest_review.price_position)}；建議投入：{_format_money(latest_review.suggested_action_amount)}；保留現金：{_format_money(latest_review.suggested_cash_reserve)}</p>
          </section>
        """
    body = f"""
      <section class="hero">
        <div class="eyebrow">{escape(plan.request.stock_symbol)} / {escape(plan.request.plan_type)}</div>
        <h1>{escape(plan.title)}</h1>
        <p>{escape(plan.summary)}</p>
        <div class="actions">
          <a class="btn" href="/investment-plans/{plan.id}/review">本月更新</a>
          <a class="btn alt" href="/investment-plans/api/plans/{plan.id}">JSON</a>
        </div>
      </section>
      {latest_review_html}
      <section class="section">
        <div class="grid three">{metrics}</div>
      </section>
      <section class="section">
        <h2>適合度判斷</h2>
        <p>{escape(plan.suitability)}</p>
      </section>
      <section class="section">
        <h2>價格區間</h2>
        <div class="grid">{bands}</div>
      </section>
      <section class="section grid">
        <article>
          <h2>操作規則</h2>
          <ul>{rules}</ul>
        </article>
        <article>
          <h2>每月追蹤</h2>
          <ul>{indicators}</ul>
        </article>
        <article>
          <h2>風險提醒</h2>
          <ul>{risks}</ul>
        </article>
        <article>
          <h2>下次檢查</h2>
          <ul>{next_items}</ul>
        </article>
      </section>
      <section class="section">
        <h2>試算</h2>
        <p>總計畫投入本金：{_format_money(plan.projection.invested_principal)}；目標停利參考價：{_format_money(plan.projection.target_take_profit_price)}；最大虧損檢查價：{_format_money(plan.projection.max_loss_review_price)}。</p>
        <p>{escape(plan.disclosure)}</p>
      </section>
    """
    return _page_shell(plan.title, body)


@router.get("/{plan_id}/review", response_class=HTMLResponse)
def new_plan_review(plan_id: UUID) -> str:
    try:
        plan = store.get(plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Investment plan not found") from exc
    average_cost = plan.request.average_cost or plan.request.current_price
    body = f"""
      <section class="hero">
        <div class="eyebrow">Monthly Review</div>
        <h1>{escape(plan.title)} 本月更新</h1>
        <p>輸入最新股價、可用現金與基本面趨勢，系統會判斷本月應該固定買進、加碼、暫停、停利或做風險檢查。</p>
      </section>
      <section class="section">
        <form class="stack" method="post" action="/investment-plans/{plan.id}/reviews">
          <div class="grid">
            <label>最新股價<input type="number" step="0.01" name="current_price" value="{plan.request.current_price}" required /></label>
            <label>目前平均成本<input type="number" step="0.01" name="average_cost" value="{average_cost}" /></label>
            <label>目前持有股數<input type="number" step="0.0001" name="shares_owned" value="{plan.request.shares_owned}" /></label>
            <label>可用現金<input type="number" step="1" name="available_cash" value="{plan.request.monthly_amount or 0}" /></label>
            <label>月營收趨勢
              <select name="revenue_trend">
                <option value="unknown">未知</option>
                <option value="improving">轉強</option>
                <option value="stable" selected>穩定</option>
                <option value="weakening">轉弱</option>
              </select>
            </label>
            <label>獲利趨勢
              <select name="earnings_trend">
                <option value="unknown">未知</option>
                <option value="improving">轉強</option>
                <option value="stable" selected>穩定</option>
                <option value="weakening">轉弱</option>
              </select>
            </label>
            <label>原料/成本趨勢
              <select name="material_cost_trend">
                <option value="unknown">未知</option>
                <option value="improving">成本改善</option>
                <option value="stable" selected>穩定</option>
                <option value="weakening">成本惡化</option>
              </select>
            </label>
            <label>全球同業/原料股趨勢
              <select name="global_peer_trend">
                <option value="unknown">未知</option>
                <option value="improving">轉強</option>
                <option value="stable" selected>穩定</option>
                <option value="weakening">轉弱</option>
              </select>
            </label>
            <label>公開事件訊號
              <select name="public_event_signal">
                <option value="unknown">未知</option>
                <option value="improving">正向</option>
                <option value="stable" selected>中性</option>
                <option value="weakening">負向</option>
              </select>
            </label>
            <label>估值狀態
              <select name="valuation_level">
                <option value="unknown">未知</option>
                <option value="undervalued">偏低</option>
                <option value="fair">合理</option>
                <option value="expensive" selected>偏高</option>
                <option value="overheated">過熱</option>
              </select>
            </label>
          </div>
          <label>本月備註<input name="notes" placeholder="例如：財報公布、產業報價、個人現金流變化" /></label>
          <button type="submit">產生本月建議</button>
        </form>
      </section>
    """
    return _page_shell("本月投資更新", body)


@router.post("/{plan_id}/reviews")
def create_plan_review_form(
    plan_id: UUID,
    current_price: float = Form(...),
    average_cost: float | None = Form(None),
    shares_owned: float = Form(0),
    available_cash: float = Form(0),
    revenue_trend: str = Form("unknown"),
    earnings_trend: str = Form("unknown"),
    material_cost_trend: str = Form("unknown"),
    global_peer_trend: str = Form("unknown"),
    public_event_signal: str = Form("unknown"),
    valuation_level: str = Form("unknown"),
    notes: str | None = Form(None),
) -> RedirectResponse:
    try:
        request = PlanReviewRequest(
            current_price=current_price,
            average_cost=average_cost,
            shares_owned=shares_owned,
            available_cash=available_cash,
            revenue_trend=revenue_trend,
            earnings_trend=earnings_trend,
            material_cost_trend=material_cost_trend,
            global_peer_trend=global_peer_trend,
            public_event_signal=public_event_signal,
            valuation_level=valuation_level,
            notes=notes or None,
        )
        store.create_review(plan_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Investment plan not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RedirectResponse(url=f"/investment-plans/{plan_id}", status_code=303)


@router.post("/api/plans")
def create_investment_plan_api(request: InvestmentPlanRequest) -> dict[str, object]:
    plan = store.create(request)
    return _api_payload(plan.model_dump(mode="json"))


@router.get("/api/plans")
def list_investment_plans_api(user_id: str | None = Query(default=None)) -> dict[str, object]:
    return _api_payload([plan.model_dump(mode="json") for plan in store.list_for_user(user_id)])


@router.get("/api/plans/{plan_id}")
def get_investment_plan_api(plan_id: UUID) -> dict[str, object]:
    try:
        plan = store.get(plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Investment plan not found") from exc
    return _api_payload(plan.model_dump(mode="json"))


@router.post("/api/plans/{plan_id}/reviews")
def create_plan_review_api(plan_id: UUID, request: PlanReviewRequest) -> dict[str, object]:
    try:
        review = store.create_review(plan_id, request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Investment plan not found") from exc
    return _api_payload(review.model_dump(mode="json"))


@router.get("/api/plans/{plan_id}/reviews")
def list_plan_reviews_api(plan_id: UUID) -> dict[str, object]:
    try:
        store.get(plan_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Investment plan not found") from exc
    return _api_payload([review.model_dump(mode="json") for review in store.list_reviews(plan_id)])


@router.post("/api/line-subscriptions")
def create_line_subscription_api(request: LineSubscriptionRequest) -> dict[str, object]:
    try:
        subscription = store.create_line_subscription(request)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Investment plan not found") from exc
    return _api_payload(subscription.model_dump(mode="json"))


@router.get("/api/line-subscriptions")
def list_line_subscriptions_api(user_id: str | None = Query(default=None)) -> dict[str, object]:
    return _api_payload([item.model_dump(mode="json") for item in store.list_line_subscriptions(user_id)])
