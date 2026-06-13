from __future__ import annotations

from datetime import date, datetime, time
from html import escape
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, ValidationError

from school_platform.ai_runtime import SchoolPlatformAiRuntime
from school_platform.auth import auth_service, current_token, get_current_user, require_roles
from school_platform.schemas import (
    ApplicantStatusUpdateRequest,
    AssignmentCreateRequest,
    AssignmentSubmissionCreateRequest,
    AttendanceMarkRequest,
    AuthLoginRequest,
    BroadcastMessageRequest,
    ClassUpsertRequest,
    CourseUpsertRequest,
    EnrollmentCreate,
    ExamCreateRequest,
    ExamSubmissionCreateRequest,
    InterviewCreateRequest,
    InterviewUpdateRequest,
    JobPositionCreateRequest,
    LessonPlanDraftRequest,
    LeadAssignmentRequest,
    LeadStatusChangeRequest,
    NotificationCreate,
    NotificationStatusUpdateRequest,
    OnboardingUpsertRequest,
    PaymentIntentCreate,
    PaymentWebhookPayload,
    ApplicantCreateRequest,
    SubmissionGradeRequest,
    SupportReplyRequest,
    TeachingSessionReviewRequest,
    TeachingSessionUpsertRequest,
    TrialBookingCreate,
)
from school_platform.services import (
    AdmissionsService,
    AiAssistantService,
    AnalyticsService,
    CatalogService,
    ConsultantWorkspaceService,
    CurriculumAdminService,
    ExecutiveDashboardService,
    FinanceService,
    LeadWorkflowService,
    NotificationService,
    PlatformStatusService,
    PublicAdmissionsService,
    RecruitingService,
    SchedulingService,
    StaffOpsService,
    StudentAdminService,
    TeacherWorkspaceService,
    TeachingOpsService,
    StudentSupportService,
    StudentPortalService,
)
from school_platform.store import store

router = APIRouter(prefix="/school-platform", tags=["school-platform"])
api_router = APIRouter(prefix="/api")
catalog_service = CatalogService(store)
admissions_service = AdmissionsService(store)
student_portal_service = StudentPortalService(store, catalog_service, admissions_service)
platform_status_service = PlatformStatusService(store)
finance_service = FinanceService(store)
teaching_ops_service = TeachingOpsService(store, catalog_service, student_portal_service)
teacher_workspace_service = TeacherWorkspaceService(catalog_service, teaching_ops_service, store)
lead_workflow_service = LeadWorkflowService(store, admissions_service)
curriculum_admin_service = CurriculumAdminService(store)
notification_service = NotificationService(store)
public_admissions_service = PublicAdmissionsService(store, catalog_service)
school_platform_ai_runtime = SchoolPlatformAiRuntime()
ai_assistant_service = AiAssistantService(store, admissions_service, catalog_service, student_portal_service, school_platform_ai_runtime)
student_support_service = StudentSupportService(student_portal_service, notification_service)
student_admin_service = StudentAdminService(student_portal_service)
recruiting_service = RecruitingService(store)
analytics_service = AnalyticsService(store, recruiting_service, school_platform_ai_runtime)
staff_ops_service = StaffOpsService(admissions_service, catalog_service, teaching_ops_service, teacher_workspace_service)
consultant_workspace_service = ConsultantWorkspaceService(admissions_service)
scheduling_service = SchedulingService(catalog_service)
executive_dashboard_service = ExecutiveDashboardService(
    admissions_service,
    catalog_service,
    finance_service,
    teaching_ops_service,
    staff_ops_service,
    student_admin_service,
    recruiting_service,
    analytics_service,
)


class LeadLogCreate(BaseModel):
    staff_name: str
    contact_method: str
    content: str
    next_action: str | None = None


def _format_jpy(amount: float) -> str:
    return f"JPY {amount:,.0f}"


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
            --bg: #f4efe5;
            --paper: #fffdf8;
            --ink: #1b2320;
            --muted: #5b6762;
            --line: #ddd4c4;
            --accent: #b44a2b;
            --accent-dark: #204b40;
            --ok: #1b7f57;
            --warn: #b86c1e;
          }}
          * {{ box-sizing: border-box; }}
          body {{
            margin: 0;
            font-family: ui-sans-serif, system-ui, sans-serif;
            background:
              radial-gradient(circle at top left, rgba(180,74,43,.10), transparent 25%),
              linear-gradient(180deg, #f9f5ed, var(--bg));
            color: var(--ink);
          }}
          a {{ color: var(--accent); text-decoration: none; }}
          .wrap {{ max-width: 1180px; margin: 0 auto; padding: 28px 20px 64px; }}
          .topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 16px;
          }}
          .brand-link {{
            color: var(--accent-dark);
            font-size: 13px;
            font-weight: 800;
            letter-spacing: .06em;
            text-transform: uppercase;
          }}
          .lang-switcher {{
            display: inline-flex;
            gap: 8px;
            align-items: center;
            flex-wrap: wrap;
          }}
          .lang-label {{
            font-size: 12px;
            color: var(--muted);
            font-weight: 700;
          }}
          .lang-pill {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 8px 12px;
            border-radius: 999px;
            border: 1px solid var(--line);
            background: #fff;
            color: var(--accent-dark);
            font-size: 14px;
            font-weight: 700;
          }}
          .lang-pill.active {{
            color: var(--accent);
            background: rgba(180,74,43,.10);
            border-color: rgba(180,74,43,.25);
          }}
          .hero, .section {{
            background: var(--paper);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 24px;
            box-shadow: 0 16px 48px rgba(0,0,0,.05);
          }}
          .section {{ margin-top: 18px; }}
          .eyebrow {{
            font-size: 12px;
            letter-spacing: .08em;
            text-transform: uppercase;
            color: var(--accent);
            font-weight: 800;
          }}
          h1 {{ margin: 10px 0; font-size: 40px; line-height: 1.05; }}
          h2 {{ margin: 0 0 10px; font-size: 24px; }}
          h3 {{ margin: 8px 0; font-size: 22px; }}
          p {{ color: var(--muted); line-height: 1.7; }}
          code {{ background: #f2ebdf; padding: 3px 8px; border-radius: 10px; }}
          .actions {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 18px; }}
          .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            padding: 12px 16px;
            border-radius: 999px;
            background: var(--accent);
            color: #fff;
            font-weight: 700;
          }}
          .btn.alt {{ background: var(--accent-dark); }}
          .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
          .grid.two {{ grid-template-columns: repeat(2, 1fr); }}
          .card {{
            background: #fff;
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 18px;
          }}
          .meta {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; }}
          .chip {{
            display: inline-flex;
            align-items: center;
            padding: 7px 10px;
            border-radius: 999px;
            background: rgba(180,74,43,.10);
            color: var(--accent);
            font-size: 13px;
            font-weight: 700;
          }}
          .stat-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }}
          .stat {{
            background: #fff;
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 16px;
          }}
          .label {{ font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }}
          .value {{ margin-top: 8px; font-size: 28px; font-weight: 800; }}
          ul.clean {{ margin: 0; padding-left: 20px; color: var(--muted); }}
          .list {{ display: grid; gap: 12px; }}
          .status-paid {{ color: var(--ok); font-weight: 800; }}
          .status-pending {{ color: var(--warn); font-weight: 800; }}
          form.stack {{ display: grid; gap: 12px; }}
          label.field {{ display: grid; gap: 6px; color: var(--muted); font-size: 14px; }}
          input, select, textarea {{
            width: 100%;
            border: 1px solid var(--line);
            border-radius: 14px;
            padding: 12px 14px;
            background: #fff;
            color: var(--ink);
            font: inherit;
          }}
          textarea {{ min-height: 100px; resize: vertical; }}
          @media (max-width: 900px) {{
            h1 {{ font-size: 32px; }}
            .grid, .grid.two, .stat-grid {{ grid-template-columns: 1fr; }}
            .topbar {{ align-items: flex-start; flex-direction: column; }}
          }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="topbar">
            <a class="brand-link" href="/school-platform">Japan Life Language School OS</a>
            <div class="lang-switcher" aria-label="language-switcher">
              <span class="lang-label">語言切換</span>
              <a id="lang-hant-link" class="lang-pill" href="#">繁體中文</a>
              <a id="lang-hans-link" class="lang-pill" href="#">簡體中文</a>
            </div>
          </div>
          {body}
        </div>
        <script>
          (() => {{
            const currentUrl = new URL(window.location.href);
            const currentLang = currentUrl.searchParams.get("lang") === "zh-Hans" ? "zh-Hans" : "zh-Hant";
            const normalizeSchoolPlatformUrl = (rawUrl) => {{
              if (!rawUrl || !rawUrl.startsWith("/school-platform")) {{
                return rawUrl;
              }}
              const target = new URL(rawUrl, window.location.origin);
              if (currentLang === "zh-Hans") {{
                target.searchParams.set("lang", "zh-Hans");
              }} else {{
                target.searchParams.delete("lang");
              }}
              return `${{target.pathname}}${{target.search}}${{target.hash}}`;
            }};

            const hantUrl = new URL(window.location.href);
            hantUrl.searchParams.delete("lang");
            const hansUrl = new URL(window.location.href);
            hansUrl.searchParams.set("lang", "zh-Hans");

            const hantLink = document.getElementById("lang-hant-link");
            const hansLink = document.getElementById("lang-hans-link");
            if (hantLink) {{
              hantLink.setAttribute("href", `${{hantUrl.pathname}}${{hantUrl.search}}${{hantUrl.hash}}`);
              hantLink.classList.toggle("active", currentLang === "zh-Hant");
            }}
            if (hansLink) {{
              hansLink.setAttribute("href", `${{hansUrl.pathname}}${{hansUrl.search}}${{hansUrl.hash}}`);
              hansLink.classList.toggle("active", currentLang === "zh-Hans");
            }}

            document.querySelectorAll('a[href^="/school-platform"]').forEach((node) => {{
              if (node.id === "lang-hant-link" || node.id === "lang-hans-link") {{
                return;
              }}
              node.setAttribute("href", normalizeSchoolPlatformUrl(node.getAttribute("href")));
            }});

            document.querySelectorAll('form[action^="/school-platform"]').forEach((node) => {{
              node.setAttribute("action", normalizeSchoolPlatformUrl(node.getAttribute("action")));
            }});

            document.documentElement.setAttribute("lang", currentLang);
          }})();
        </script>
      </body>
    </html>
    """


@router.get("", response_class=HTMLResponse)
def school_platform_home() -> str:
    home = catalog_service.home_payload()
    cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(course.course_type)} / {escape(course.level)}</div>"
        f"<h3>{escape(course.name)}</h3>"
        f"<p>{escape(course.short_description)}</p>"
        f"<div class='price'>{_format_jpy(course.price)}</div>"
        "</article>"
        for course in home.featured_courses
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">{escape(home.brand_name)}</div>
        <h1>{escape(home.hero_title)}</h1>
        <p>{escape(home.hero_subtitle)}</p>
        <p>目前已提供可跑的 MVP API 骨架：前台課程、試聽預約、報名建單、招生 CRM、AI 跟進草稿與管理 dashboard。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/courses">中文課程頁</a>
          <a class="btn alt" href="/school-platform/trial-booking">預約試聽</a>
          <a class="btn alt" href="/school-platform/enrollment">正式報名</a>
          <a class="btn alt" href="/school-platform/jobs">加入團隊</a>
          <a class="btn alt" href="/school-platform/progress">開發進度頁</a>
        </div>
      </section>
      <section class="section">
        <h2>熱門課程</h2>
        <div class="grid">{cards}</div>
      </section>
      <section class="section">
        <div class="eyebrow">API Base</div>
        <p><code>/school-platform/api</code></p>
      </section>
    """
    return _page_shell("AI 日語補習班營運平台 MVP", body)


@router.get("/courses", response_class=HTMLResponse)
def school_platform_courses_page() -> str:
    courses = catalog_service.list_courses()
    cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(course.course_type)} / {escape(course.level)}</div>"
        f"<h3>{escape(course.name)}</h3>"
        f"<p>{escape(course.short_description)}</p>"
        "<div class='meta'>"
        f"<span class='chip'>{_format_jpy(course.price)}</span>"
        f"<span class='chip'>{escape(course.delivery_mode)}</span>"
        "</div>"
        f"<div class='actions'><a class='btn' href='/school-platform/courses/{escape(course.slug)}'>查看課程詳情</a></div>"
        "</article>"
        for course in courses
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">Course Catalog</div>
        <h1>課程總覽</h1>
        <p>這裡把目前可招生的日語課程整理成中文網頁介面，方便你直接看產品是不是已經開始成形。</p>
        <div class="actions">
          <a class="btn" href="/school-platform">回平台首頁</a>
          <a class="btn alt" href="/school-platform/api/public/courses">查看課程 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid">{cards}</div>
      </section>
    """
    return _page_shell("課程總覽", body)


@router.get("/courses/{slug}", response_class=HTMLResponse)
def school_platform_course_detail_page(slug: str) -> str:
    try:
        course = catalog_service.get_course(slug)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc
    classes = catalog_service.classes_for_course(slug)
    class_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(class_item.name)}</h3>"
        f"<p>老師：{escape(class_item.teacher_name)} / 上課：{escape(class_item.weekday)} {escape(class_item.start_time.strftime('%H:%M'))}-{escape(class_item.end_time.strftime('%H:%M'))}</p>"
        f"<p>期間：{escape(class_item.start_date.isoformat())} 至 {escape(class_item.end_date.isoformat())}</p>"
        f"<div class='meta'><span class='chip'>名額 {class_item.enrolled_count}/{class_item.capacity}</span><span class='chip'>{escape(class_item.location_label)}</span></div>"
        "</article>"
        for class_item in classes
    ) or "<article class='card'><h3>尚無開放班級</h3><p>這門課已建檔，但目前沒有可報名班級。</p></article>"
    objectives = "".join(f"<li>{escape(item)}</li>" for item in course.objectives)
    highlights = "".join(f"<li>{escape(item)}</li>" for item in course.highlights)
    modules = "".join(f"<li>{escape(item)}</li>" for item in course.modules)
    body = f"""
      <section class="hero">
        <div class="eyebrow">{escape(course.course_type)} / {escape(course.level)}</div>
        <h1>{escape(course.name)}</h1>
        <p>{escape(course.short_description)}</p>
        <div class="meta">
          <span class="chip">{_format_jpy(course.price)}</span>
          <span class="chip">{escape(course.delivery_mode)}</span>
          <span class="chip">教師：{escape(", ".join(course.teacher_names) or "待定")}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/courses">回課程總覽</a>
          <a class="btn alt" href="/school-platform/trial-booking?course_slug={escape(course.slug)}">預約這門課試聽</a>
          <a class="btn alt" href="/school-platform/enrollment?course_slug={escape(course.slug)}">直接報名這門課</a>
          <a class="btn alt" href="/school-platform/api/public/courses/{escape(course.slug)}">查看課程 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>課程目標</h2>
            <ul class="clean">{objectives}</ul>
          </article>
          <article class="card">
            <h2>課程亮點</h2>
            <ul class="clean">{highlights}</ul>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>章節規劃</h2>
        <article class="card">
          <ul class="clean">{modules}</ul>
        </article>
      </section>
      <section class="section">
        <h2>目前可報名班級</h2>
        <div class="grid two">{class_cards}</div>
      </section>
    """
    return _page_shell(course.name, body)


@router.get("/trial-booking", response_class=HTMLResponse)
def school_platform_trial_booking_page(course_slug: str | None = Query(default=None)) -> str:
    courses = catalog_service.list_courses()
    slots = public_admissions_service.trial_slots(course_slug)
    course_options = "".join(
        f"<option value='{escape(item.slug)}' {'selected' if item.slug == course_slug else ''}>{escape(item.name)} ({escape(item.level)})</option>"
        for item in courses
    )
    slot_options = "".join(
        f"<option value='{item.starts_at.isoformat()}'>{escape(item.label)} / {escape(item.starts_at.strftime('%Y-%m-%d %H:%M'))}</option>"
        for item in slots
    )
    if not slot_options:
        slot_options = "<option value=''>目前沒有可預約時段</option>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Trial Booking</div>
        <h1>免費試聽預約</h1>
        <p>這裡把試聽預約流程做成中文網頁表單，填完就會直接建立 lead、指派顧問並排入提醒。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/courses">回課程總覽</a>
          <a class="btn alt" href="/school-platform/api/public/trial-slots">查看時段 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>試聽預約表單</h2>
            <form class="stack" method="post" action="/school-platform/trial-booking/create">
              <label class="field">姓名
                <input type="text" name="name" placeholder="例如：王小美" />
              </label>
              <label class="field">Email
                <input type="email" name="email" placeholder="you@example.com" />
              </label>
              <label class="field">電話
                <input type="text" name="phone" placeholder="09xxxxxxxx" />
              </label>
              <label class="field">LINE ID
                <input type="text" name="line_id" placeholder="選填" />
              </label>
              <label class="field">想試聽的課程
                <select name="course_slug">{course_options}</select>
              </label>
              <label class="field">可預約時段
                <select name="slot_start_at">{slot_options}</select>
              </label>
              <label class="field">目前程度
                <select name="japanese_level">
                  <option value="beginner">beginner</option>
                  <option value="N5">N5</option>
                  <option value="N4">N4</option>
                  <option value="N3">N3</option>
                </select>
              </label>
              <label class="field">學習目標
                <textarea name="study_goal" placeholder="例如：赴日前想先學租屋、看病、購物會話"></textarea>
              </label>
              <button class="btn" type="submit">送出試聽預約</button>
            </form>
          </article>
          <article class="card">
            <h2>送出後系統會做什麼</h2>
            <ul class="clean">
              <li>建立 lead 名單並標記為 <code>trial_booked</code></li>
              <li>自動指派招生顧問</li>
              <li>新增 CRM 跟進紀錄</li>
              <li>排入試聽前一天提醒通知</li>
            </ul>
          </article>
        </div>
      </section>
    """
    return _page_shell("免費試聽預約", body)


@router.post("/trial-booking/create")
def school_platform_trial_booking_submit(
    name: str = Form(...),
    email: str = Form(default=""),
    phone: str = Form(default=""),
    line_id: str = Form(default=""),
    course_slug: str = Form(...),
    slot_start_at: str = Form(...),
    japanese_level: str = Form(default=""),
    study_goal: str = Form(default=""),
):
    payload = TrialBookingCreate(
        name=name,
        email=email or None,
        phone=phone or None,
        line_id=line_id or None,
        course_slug=course_slug,
        slot_start_at=datetime.fromisoformat(slot_start_at),
        japanese_level=japanese_level or None,
        study_goal=study_goal or None,
    )
    booking = public_admissions_service.create_trial_booking(payload)
    query = urlencode(
        {
            "booking_id": str(booking.booking_id),
            "lead_id": str(booking.lead_id),
            "staff": booking.assigned_staff_name,
            "next_follow_up_at": booking.next_follow_up_at.isoformat(),
        }
    )
    return RedirectResponse(url=f"/school-platform/trial-booking/success?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/trial-booking/success", response_class=HTMLResponse)
def school_platform_trial_booking_success_page(
    booking_id: str = Query(...),
    lead_id: str = Query(...),
    staff: str = Query(...),
    next_follow_up_at: str = Query(...),
) -> str:
    body = f"""
      <section class="hero">
        <div class="eyebrow">Trial Booking Success</div>
        <h1>試聽預約已送出</h1>
        <p>系統已替你建立試聽預約、CRM 名單與顧問指派，後續會依照設定時間自動提醒。</p>
        <div class="meta">
          <span class="chip">booking_id: {escape(booking_id)}</span>
          <span class="chip">lead_id: {escape(lead_id)}</span>
          <span class="chip">顧問：{escape(staff)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/trial-booking">再預約一筆</a>
          <a class="btn alt" href="/school-platform/admin/leads">查看招生名單</a>
        </div>
      </section>
      <section class="section">
        <article class="card">
          <h2>下一步</h2>
          <p>預計下次跟進時間：<code>{escape(next_follow_up_at)}</code></p>
          <p>這一筆資料已經進入招生 CRM，顧問可直接在後台查看與更新。</p>
        </article>
      </section>
    """
    return _page_shell("試聽預約成功", body)


@router.get("/enrollment", response_class=HTMLResponse)
def school_platform_enrollment_page(course_slug: str | None = Query(default=None)) -> str:
    classes = catalog_service.open_classes()
    if course_slug:
        classes = [item for item in classes if item.course_slug == course_slug]
    class_options = "".join(
        f"<option value='{item.id}'>{escape(item.name)} / {escape(item.course_slug)} / {escape(item.weekday)} / {escape(item.location_label)}</option>"
        for item in classes
    )
    if not class_options:
        class_options = "<option value=''>目前沒有可報名班級</option>"
    course_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>{escape(item.course_slug)} / {escape(item.weekday)} / {escape(item.location_label)}</p>"
        f"<div class='meta'><span class='chip'>名額 {item.enrolled_count}/{item.capacity}</span><span class='chip'>{escape(item.start_date.isoformat())}</span></div>"
        "</article>"
        for item in classes[:4]
    ) or "<article class='card'><h3>目前沒有班級</h3><p>請先回課程頁選擇其他課程或之後再試。</p></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Enrollment</div>
        <h1>正式報名</h1>
        <p>這裡會直接建立學員、報名紀錄、付款訂單與通知，讓前台招生主流程可以從網頁直接走完。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/courses">回課程總覽</a>
          <a class="btn alt" href="/school-platform/trial-booking">先預約試聽</a>
          <a class="btn alt" href="/school-platform/api/public/classes/open">查看開放班級 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>報名表單</h2>
            <form class="stack" method="post" action="/school-platform/enrollment/create">
              <label class="field">中文姓名
                <input type="text" name="chinese_name" placeholder="例如：林小雅" />
              </label>
              <label class="field">Email
                <input type="email" name="email" placeholder="you@example.com" />
              </label>
              <label class="field">電話
                <input type="text" name="phone" placeholder="09xxxxxxxx" />
              </label>
              <label class="field">班級
                <select name="class_id">{class_options}</select>
              </label>
              <label class="field">日語程度
                <select name="japanese_level">
                  <option value="beginner">beginner</option>
                  <option value="N5">N5</option>
                  <option value="N4">N4</option>
                  <option value="N3">N3</option>
                </select>
              </label>
              <label class="field">學習目標
                <textarea name="study_goal" placeholder="例如：赴日前先完成生活與工作面試會話"></textarea>
              </label>
              <label class="field">付款方式
                <select name="payment_method">
                  <option value="card">card</option>
                  <option value="transfer">transfer</option>
                  <option value="cash">cash</option>
                </select>
              </label>
              <button class="btn" type="submit">建立報名與付款單</button>
            </form>
          </article>
          <article class="card">
            <h2>目前可報名班級</h2>
            <div class="list">{course_cards}</div>
          </article>
        </div>
      </section>
    """
    return _page_shell("正式報名", body)


@router.post("/enrollment/create")
def school_platform_enrollment_submit(
    chinese_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(default=""),
    class_id: str = Form(...),
    japanese_level: str = Form(default=""),
    study_goal: str = Form(default=""),
    payment_method: str = Form(default="card"),
):
    enrollment = finance_service.create_enrollment(
        EnrollmentCreate(
            chinese_name=chinese_name,
            email=email,
            phone=phone or None,
            class_id=UUID(class_id),
            japanese_level=japanese_level or None,
            study_goal=study_goal or None,
            payment_method=payment_method,
        )
    )
    query = urlencode(
        {
            "student_email": email,
            "order_no": enrollment.order_no,
            "status": enrollment.status,
            "payment_status": enrollment.payment_status,
        }
    )
    return RedirectResponse(url=f"/school-platform/enrollment/success?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/enrollment/success", response_class=HTMLResponse)
def school_platform_enrollment_success_page(
    student_email: str = Query(...),
    order_no: str = Query(...),
    status_value: str = Query(..., alias="status"),
    payment_status: str = Query(...),
) -> str:
    body = f"""
      <section class="hero">
        <div class="eyebrow">Enrollment Success</div>
        <h1>報名申請已建立</h1>
        <p>系統已建立學員、報名紀錄與付款訂單，下一步可以直接進學員中心查看資料。</p>
        <div class="meta">
          <span class="chip">學員：{escape(student_email)}</span>
          <span class="chip">訂單：{escape(order_no)}</span>
          <span class="chip">報名狀態：{escape(status_value)}</span>
          <span class="chip">付款狀態：{escape(payment_status)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/payment?email={escape(student_email)}&order_no={escape(order_no)}">前往付款中心</a>
          <a class="btn" href="/school-platform/student-portal?email={escape(student_email)}">打開學員中心</a>
          <a class="btn alt" href="/school-platform/admin">回營運後台</a>
        </div>
      </section>
      <section class="section">
        <article class="card">
          <h2>下一步</h2>
          <p>這筆報名已經同步建立通知與付款資料，後續可透過付款 API 或 webhook 把狀態推進到 <code>paid</code>。</p>
        </article>
      </section>
    """
    return _page_shell("報名成功", body)


@router.get("/jobs", response_class=HTMLResponse)
def school_platform_jobs_page(position_id: UUID | None = Query(default=None)) -> str:
    jobs = recruiting_service.list_jobs(status="open")
    selected_id = position_id or (jobs[0].id if jobs else None)
    selected_job = next((item for item in jobs if item.id == selected_id), jobs[0] if jobs else None)
    job_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.department)} / {escape(item.employment_type)}</div>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>{escape(item.summary)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.location_label)}</span><span class='chip'>{escape(item.salary_range)}</span></div>"
        f"<div class='actions'><a class='btn' href='/school-platform/jobs?position_id={item.id}'>應徵這個職缺</a></div>"
        "</article>"
        for item in jobs
    ) or "<article class='card'><h3>目前沒有開放職缺</h3></article>"
    requirement_list = "".join(f"<li>{escape(item)}</li>" for item in (selected_job.requirements if selected_job else []))
    apply_block = (
        f"""
        <article class="card">
          <h2>投遞履歷</h2>
          <p>目前選擇職缺：<code>{escape(selected_job.title)}</code></p>
          <form class="stack" method="post" action="/school-platform/jobs/apply">
            <input type="hidden" name="position_id" value="{selected_job.id}" />
            <label class="field">姓名
              <input type="text" name="name" />
            </label>
            <label class="field">Email
              <input type="email" name="email" />
            </label>
            <label class="field">電話
              <input type="text" name="phone" />
            </label>
            <label class="field">履歷連結
              <input type="text" name="resume_link" placeholder="Google Drive / Notion / PDF link" />
            </label>
            <label class="field">補充說明
              <textarea name="note" placeholder="簡單說明你的教學或招生經驗"></textarea>
            </label>
            <button class="btn" type="submit">送出應徵</button>
          </form>
        </article>
        <article class="card">
          <h2>需求條件</h2>
          <ul class="clean">{requirement_list}</ul>
        </article>
        """
        if selected_job
        else "<article class='card'><h2>投遞履歷</h2><p>目前沒有可投遞的職缺。</p></article>"
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">Recruiting</div>
        <h1>加入 AI 日語補習班團隊</h1>
        <p>這裡提供公開職缺與線上投遞表單，後台會同步進入招聘看板與面試流程。</p>
        <div class="actions">
          <a class="btn" href="/school-platform">回平台首頁</a>
          <a class="btn alt" href="/school-platform/api/public/jobs">查看職缺 JSON</a>
        </div>
      </section>
      <section class="section">
        <h2>開放職缺</h2>
        <div class="grid two">{job_cards}</div>
      </section>
      <section class="section">
        <div class="grid two">{apply_block}</div>
      </section>
    """
    return _page_shell("招聘頁", body)


@router.post("/jobs/apply")
def school_platform_jobs_apply_submit(
    position_id: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(default=""),
    resume_link: str = Form(default=""),
    note: str = Form(default=""),
):
    applicant = recruiting_service.create_applicant(
        ApplicantCreateRequest(
            position_id=UUID(position_id),
            name=name,
            email=email,
            phone=phone or None,
            resume_link=resume_link or None,
            note=note or None,
        )
    )
    query = urlencode({"applicant_id": str(applicant.id), "email": email})
    return RedirectResponse(url=f"/school-platform/jobs/success?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/jobs/success", response_class=HTMLResponse)
def school_platform_jobs_success_page(applicant_id: UUID = Query(...), email: str = Query(...)) -> str:
    body = f"""
      <section class="hero">
        <div class="eyebrow">Application Submitted</div>
        <h1>應徵資料已送出</h1>
        <p>系統已建立應徵者資料並同步通知招聘後台，下一步可由主管安排面試。</p>
        <div class="meta">
          <span class="chip">Applicant ID：{applicant_id}</span>
          <span class="chip">{escape(email)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/jobs">回招聘頁</a>
          <a class="btn alt" href="/school-platform/admin/recruiting">查看招聘看板</a>
        </div>
      </section>
    """
    return _page_shell("應徵成功", body)


@router.get("/payment", response_class=HTMLResponse)
def school_platform_payment_page(
    email: str = Query(...),
    order_no: str = Query(...),
    client_token: str | None = Query(default=None),
    checkout_url: str | None = Query(default=None),
    reminder_sent: str | None = Query(default=None),
    payment_result: str | None = Query(default=None),
    payment_error: str | None = Query(default=None),
) -> str:
    try:
        payments = student_portal_service.student_payments(email)
        notifications = student_portal_service.student_notifications(email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    payment = next((item for item in payments if item.order_no == order_no), None)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment_notifications = [
        item for item in notifications if order_no in item.content or item.type in {"enrollment_created", "payment_status_updated"}
    ][:4]
    payment_provider_status = finance_service.payment_provider_status()
    effective_client_token = client_token or payment.client_token
    effective_checkout_url = checkout_url or payment.checkout_url
    notification_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>{escape(item.content)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.channel)}</span><span class='chip'>{escape(item.status)}</span><span class='chip'>{escape(item.provider or 'internal')}</span></div>"
        "</article>"
        for item in payment_notifications
    ) or "<article class='card'><h3>尚無付款通知</h3></article>"
    token_block = (
        (
            "<article class='card'>"
            "<h3>Stripe Checkout 已建立</h3>"
            f"<p><code>{escape(effective_client_token or '')}</code></p>"
            f"<p><a class='btn' href='{escape(effective_checkout_url or '#')}' target='_blank' rel='noreferrer'>前往 Stripe 付款頁</a></p>"
            "<p>這是正式外部金流 checkout session；完成付款後會回到本頁並透過 webhook 回寫狀態。</p>"
            "</article>"
        )
        if effective_checkout_url
        else (
            f"<article class='card'><h3>最新 client token</h3><p><code>{escape(effective_client_token)}</code></p><p>這是目前使用中的 payment intent token。</p></article>"
            if effective_client_token
            else "<article class='card'><h3>尚未建立 payment intent</h3><p>可先點下面按鈕建立付款 session 或 mock token。</p></article>"
        )
    )
    reminder_block = (
        "<article class='card'><h3>付款提醒已寄出</h3><p>系統已新增一筆付款提醒通知，學員可回到通知中心查看。</p></article>"
        if reminder_sent
        else ""
    )
    payment_result_block = (
        "<article class='card'><h3>付款已完成返回</h3><p>若 webhook 已成功抵達，訂單狀態會更新為 paid；若狀態還沒變更，可稍候重新整理本頁。</p></article>"
        if payment_result == "success"
        else (
            "<article class='card'><h3>付款流程已取消</h3><p>本次外部付款未完成，你可以重新建立 checkout session 再次付款。</p></article>"
            if payment_result == "cancel"
            else (
                f"<article class='card'><h3>付款 session 建立失敗</h3><p>{escape(payment_error)}</p></article>"
                if payment_error
                else ""
            )
        )
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">Payment Center</div>
        <h1>付款中心</h1>
        <p>這頁把報名後的付款流程做成可操作的中文介面，現在可以直接查訂單、建立正式 Stripe Checkout 或 mock intent，並查看 webhook 回寫結果。</p>
        <div class="meta">
          <span class="chip">學員：{escape(email)}</span>
          <span class="chip">訂單：{escape(payment.order_no)}</span>
          <span class="chip">方式：{escape(payment.payment_method)}</span>
          <span class="chip">狀態：{escape(payment.status)}</span>
          <span class="chip">provider：{escape(payment.provider or 'mock')}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/admin">回營運後台</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>訂單摘要</h2>
            <p>金額：{_format_jpy(payment.amount)}</p>
            <p>建立時間：{escape(payment.created_at.isoformat())}</p>
            <p>已付款時間：{escape(payment.paid_at.isoformat()) if payment.paid_at else '尚未付款'}</p>
            <p>provider_status：{escape(payment.provider_status or payment.status)}</p>
          </article>
          {token_block}
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>金流 readiness</h2>
            <p>provider：<code>{escape(str(payment_provider_status['provider']))}</code></p>
            <p>ready：<code>{escape(str(payment_provider_status['ready']).lower())}</code></p>
            <p>currency：<code>{escape(str(payment_provider_status['currency']))}</code></p>
            <p>message：{escape(str(payment_provider_status['message']))}</p>
          </article>
          {payment_result_block or "<article class='card'><h3>付款流程回傳</h3><p>尚未從外部金流返回。</p></article>"}
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>建立付款 Session</h2>
            <form class="stack" method="post" action="/school-platform/payment/intent">
              <input type="hidden" name="email" value="{escape(email)}" />
              <input type="hidden" name="order_no" value="{escape(payment.order_no)}" />
              <input type="hidden" name="enrollment_id" value="{payment.enrollment_id}" />
              <input type="hidden" name="payment_method" value="{escape(payment.payment_method)}" />
              <button class="btn" type="submit">建立付款 session</button>
            </form>
          </article>
          <article class="card">
            <h2>模擬付款狀態更新</h2>
            <form class="stack" method="post" action="/school-platform/payment/update">
              <input type="hidden" name="email" value="{escape(email)}" />
              <input type="hidden" name="order_no" value="{escape(payment.order_no)}" />
              <label class="field">更新狀態
                <select name="payment_status">
                  <option value="paid">paid</option>
                  <option value="failed">failed</option>
                  <option value="refunded">refunded</option>
                </select>
              </label>
              <button class="btn" type="submit">送出 webhook 模擬</button>
            </form>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>重新寄送付款提醒</h2>
            <form class="stack" method="post" action="/school-platform/payment/remind">
              <input type="hidden" name="email" value="{escape(email)}" />
              <input type="hidden" name="order_no" value="{escape(payment.order_no)}" />
              <button class="btn" type="submit">寄送付款提醒</button>
            </form>
          </article>
          {reminder_block or "<article class='card'><h3>提醒狀態</h3><p>尚未重新寄送提醒。</p></article>"}
        </div>
      </section>
      <section class="section">
        <h2>相關通知</h2>
        <div class="grid two">{notification_cards}</div>
      </section>
    """
    return _page_shell("付款中心", body)


@router.post("/payment/intent")
def school_platform_payment_intent_submit(
    email: str = Form(...),
    order_no: str = Form(...),
    enrollment_id: str = Form(...),
    payment_method: str = Form(...),
):
    try:
        intent = finance_service.create_payment_intent(
            PaymentIntentCreate(
                enrollment_id=UUID(enrollment_id),
                payment_method=payment_method,
            )
        )
    except RuntimeError as exc:
        query = urlencode({"email": email, "order_no": order_no, "payment_error": str(exc)})
        return RedirectResponse(url=f"/school-platform/payment?{query}", status_code=status.HTTP_303_SEE_OTHER)
    if intent.checkout_url and intent.provider != "mock":
        return RedirectResponse(url=intent.checkout_url, status_code=status.HTTP_303_SEE_OTHER)
    query = urlencode({"email": email, "order_no": order_no, "client_token": intent.client_token})
    return RedirectResponse(url=f"/school-platform/payment?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/payment/update")
def school_platform_payment_update_submit(
    email: str = Form(...),
    order_no: str = Form(...),
    payment_status: str = Form(...),
):
    finance_service.apply_payment_webhook(PaymentWebhookPayload(order_no=order_no, status=payment_status))
    query = urlencode({"email": email, "order_no": order_no})
    return RedirectResponse(url=f"/school-platform/payment?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/payment/remind")
def school_platform_payment_remind_submit(
    email: str = Form(...),
    order_no: str = Form(...),
):
    student_support_service.send_payment_reminder(email, order_no)
    query = urlencode({"email": email, "order_no": order_no, "reminder_sent": "1"})
    return RedirectResponse(url=f"/school-platform/payment?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/student-portal", response_class=HTMLResponse)
def school_platform_student_portal_page(email: str = Query(...)) -> str:
    try:
        dashboard = student_portal_service.student_dashboard(email)
        classes = student_portal_service.student_classes(email)
        payments = student_portal_service.student_payments(email)
        notifications = student_portal_service.student_notifications(email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    class_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>{escape(item.course_slug)} / {escape(item.weekday)} / {escape(item.location_label)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.start_date.isoformat())}</span><span class='chip'>{escape(item.teacher_name)}</span></div>"
        "</article>"
        for item in classes
    ) or "<article class='card'><h3>目前沒有課程</h3><p>這位學員目前沒有綁定班級。</p></article>"
    payment_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(item.order_no)}</h3>"
        f"<p>付款方式：{escape(item.payment_method)} / 金額：{_format_jpy(item.amount)}</p>"
        f"<p class='status-{'paid' if item.status == 'paid' else 'pending'}'>狀態：{escape(item.status)}</p>"
        "</article>"
        for item in payments
    ) or "<article class='card'><h3>尚無付款資料</h3></article>"
    notification_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>{escape(item.content)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.channel)}</span><span class='chip'>{escape(item.status)}</span></div>"
        "</article>"
        for item in notifications[:6]
    ) or "<article class='card'><h3>尚無通知</h3></article>"
    payment_action = (
        f"<a class='btn alt' href='/school-platform/payment?email={escape(email)}&order_no={escape(payments[0].order_no)}'>付款中心</a>"
        if payments
        else ""
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">Student Portal</div>
        <h1>學員中心總覽</h1>
        <p>這是目前學員端的中文頁面骨架，會顯示已報名班級、付款狀態與通知。</p>
        <div class="meta">
          <span class="chip">{escape(dashboard.student.chinese_name)}</span>
          <span class="chip">{escape(dashboard.student.email)}</span>
          <span class="chip">{escape(dashboard.student.status)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/my-schedule?email={escape(email)}">我的課表</a>
          <a class="btn alt" href="/school-platform/my-assignments?email={escape(email)}">作業中心</a>
          <a class="btn alt" href="/school-platform/my-exams?email={escape(email)}">測驗中心</a>
          <a class="btn alt" href="/school-platform/my-progress?email={escape(email)}">學習進度</a>
          <a class="btn alt" href="/school-platform/ai-practice?email={escape(email)}">AI 練習區</a>
          <a class="btn alt" href="/school-platform/my-attendance?email={escape(email)}">出缺勤</a>
          <a class="btn alt" href="/school-platform/notifications-center?email={escape(email)}">通知中心</a>
          {payment_action}
          <a class="btn alt" href="/school-platform/my-history?email={escape(email)}">我的歷程</a>
          <a class="btn alt" href="/school-platform/help-center?email={escape(email)}">客服需求</a>
        </div>
      </section>
      <section class="section">
        <h2>學員摘要</h2>
        <div class="stat-grid">
          <div class="stat"><div class="label">進行中課程</div><div class="value">{len(dashboard.active_courses)}</div></div>
          <div class="stat"><div class="label">付款紀錄</div><div class="value">{len(payments)}</div></div>
          <div class="stat"><div class="label">通知數量</div><div class="value">{dashboard.notification_count}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>我的課程</h2>
        <div class="grid two">{class_cards}</div>
      </section>
      <section class="section">
        <h2>我的付款</h2>
        <div class="grid two">{payment_cards}</div>
      </section>
      <section class="section">
        <h2>最新通知</h2>
        <div class="grid two">{notification_cards}</div>
      </section>
    """
    return _page_shell("學員中心", body)


@router.get("/ai-practice", response_class=HTMLResponse)
def school_platform_ai_practice_page(
    email: str = Query(...),
    theme: str = Query(default="藥局與購物生活會話"),
) -> str:
    try:
        student = student_portal_service.get_student_by_email(email)
        practice = ai_assistant_service.practice_conversation(email, theme)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    goal_items = "".join(f"<li>{escape(item)}</li>" for item in practice.goals)
    phrase_items = "".join(f"<li>{escape(item)}</li>" for item in practice.key_phrases)
    hint_items = "".join(f"<li>{escape(item)}</li>" for item in practice.hints)
    review_items = "".join(f"<li>{escape(item)}</li>" for item in practice.review_checklist)
    body = f"""
      <section class="hero">
        <div class="eyebrow">AI Practice Zone</div>
        <h1>AI 練習區</h1>
        <p>這裡會依照學員程度與主題，快速生成一段可直接開口練習的日語情境對話草稿。</p>
        <div class="meta">
          <span class="chip">{escape(practice.student_name)}</span>
          <span class="chip">{escape(practice.student_email)}</span>
          <span class="chip">{escape(practice.level)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/api/student/ai-practice?email={escape(email)}&theme={escape(theme)}">查看練習 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>重新生成主題</h2>
            <form class="stack" method="get" action="/school-platform/ai-practice">
              <input type="hidden" name="email" value="{escape(email)}" />
              <label class="field">主題
                <input type="text" name="theme" value="{escape(theme)}" />
              </label>
              <button class="btn" type="submit">更新練習主題</button>
            </form>
          </article>
          <article class="card">
            <h2>情境摘要</h2>
            <p>標題：{escape(practice.scenario_title)}</p>
            <p>情境：{escape(practice.situation)}</p>
            <p>AI 開場：{escape(practice.ai_opening)}</p>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>本次練習目標</h2>
            <ul class="clean">{goal_items}</ul>
          </article>
          <article class="card">
            <h2>關鍵句型</h2>
            <ul class="clean">{phrase_items}</ul>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>練習提示</h2>
            <ul class="clean">{hint_items}</ul>
          </article>
          <article class="card">
            <h2>自我檢查</h2>
            <ul class="clean">{review_items}</ul>
          </article>
        </div>
      </section>
    """
    return _page_shell("AI 練習區", body)


@router.get("/my-progress", response_class=HTMLResponse)
def school_platform_student_progress_page(email: str = Query(...)) -> str:
    try:
        snapshot = teaching_ops_service.student_progress(email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    assignment_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.class_name)} / {escape(item.status)}</div>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>截止時間：{escape(item.due_at.isoformat())}</p>"
        + (
            f"<p><code>分數：{item.score:g} / 評語：{escape(item.feedback or '待補')}</code></p>"
            if item.score is not None
            else "<p><code>目前尚未評分</code></p>"
        )
        + "</article>"
        for item in snapshot.assignments[:6]
    ) or "<article class='card'><h3>目前沒有作業紀錄</h3></article>"
    exam_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.class_name)} / {escape(item.exam_type)} / {escape(item.status)}</div>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>總分：{item.total_score:g} / 截止時間：{escape(item.due_at.isoformat())}</p>"
        + (
            f"<p><code>分數：{item.score:g} / 評語：{escape(item.feedback or '待補')}</code></p>"
            if item.score is not None
            else "<p><code>目前尚未評分</code></p>"
        )
        + "</article>"
        for item in snapshot.exams[:6]
    ) or "<article class='card'><h3>目前沒有測驗紀錄</h3></article>"
    attendance_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.class_name)}</div>"
        f"<h3>{escape(item.status)}</h3>"
        f"<p>上課日期：{escape(item.class_date.isoformat())}</p>"
        f"<p>{escape(item.note or '無備註')}</p>"
        "</article>"
        for item in snapshot.attendance[:6]
    ) or "<article class='card'><h3>目前沒有出缺勤紀錄</h3></article>"
    score_block = f"{snapshot.summary.overall_score:g}" if snapshot.summary.overall_score is not None else "N/A"
    assignment_avg_block = f"{snapshot.summary.assignment_average:g}" if snapshot.summary.assignment_average is not None else "N/A"
    exam_avg_block = f"{snapshot.summary.exam_average:g}" if snapshot.summary.exam_average is not None else "N/A"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Learning Progress</div>
        <h1>學習進度中心</h1>
        <p>這裡把作業、測驗、出缺勤與目前風險整合成一個學員可直接看的學習面板。</p>
        <div class="meta">
          <span class="chip">{escape(snapshot.student.chinese_name)}</span>
          <span class="chip">{escape(snapshot.student.email)}</span>
          <span class="chip">風險：{escape(snapshot.summary.risk_level)}</span>
          <span class="chip">弱點：{escape(snapshot.summary.weak_spot)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/my-assignments?email={escape(email)}">作業中心</a>
          <a class="btn alt" href="/school-platform/my-exams?email={escape(email)}">測驗中心</a>
          <a class="btn alt" href="/school-platform/my-attendance?email={escape(email)}">出缺勤</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">整體學習評估</div><div class="value">{score_block}</div></div>
          <div class="stat"><div class="label">作業平均</div><div class="value">{assignment_avg_block}</div></div>
          <div class="stat"><div class="label">測驗平均</div><div class="value">{exam_avg_block}</div></div>
          <div class="stat"><div class="label">出席率</div><div class="value">{snapshot.summary.attendance_rate:g}%</div></div>
          <div class="stat"><div class="label">待補作業</div><div class="value">{snapshot.summary.assignment_total - snapshot.summary.assignment_submitted}</div></div>
          <div class="stat"><div class="label">待補測驗</div><div class="value">{snapshot.summary.exam_total - snapshot.summary.exam_submitted}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>系統建議</h2>
        <p>{escape(snapshot.summary.recommended_action)}</p>
      </section>
      <section class="section">
        <h2>作業進度</h2>
        <div class="grid two">{assignment_cards}</div>
      </section>
      <section class="section">
        <h2>測驗進度</h2>
        <div class="grid two">{exam_cards}</div>
      </section>
      <section class="section">
        <h2>最近出缺勤</h2>
        <div class="grid two">{attendance_cards}</div>
      </section>
    """
    return _page_shell("學習進度中心", body)


@router.get("/my-assignments", response_class=HTMLResponse)
def school_platform_student_assignments_page(email: str = Query(...)) -> str:
    student = student_portal_service.get_student_by_email(email)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    assignments = teaching_ops_service.student_assignments(email)
    summary = teaching_ops_service.assignment_submission_summary(email)
    submissions = {item.assignment_id: item for item in teaching_ops_service.student_assignment_submissions(email)}
    cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.due_at.isoformat())}</div>"
            f"<h3>{escape(item.title)}</h3>"
            f"<p>{escape(item.content)}</p>"
            f"<div class='meta'><span class='chip'>{'已提交' if item.id in submissions else '待提交'}</span></div>"
            + (
                f"<p><code>提交時間：{escape(submissions[item.id].submitted_at.isoformat())}</code></p>"
                if item.id in submissions
                else (
                    f"<form class='stack' method='post' action='/school-platform/my-assignments/{item.id}/submit'>"
                    f"<input type='hidden' name='email' value='{escape(email)}' />"
                    "<label class='field'>作業內容"
                    "<textarea name='content' placeholder='輸入你的作業內容'></textarea>"
                    "</label>"
                    "<button class='btn' type='submit'>提交作業</button>"
                    "</form>"
                )
            )
            + "</article>"
        )
        for item in assignments
    ) or "<article class='card'><h3>目前沒有作業</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Assignments Center</div>
        <h1>作業中心</h1>
        <p>這裡集中顯示學員目前的作業、截止時間與提交狀態。</p>
        <div class="meta">
          <span class="chip">{escape(student.chinese_name)}</span>
          <span class="chip">{escape(student.email)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/my-attendance?email={escape(email)}">出缺勤</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">作業總數</div><div class="value">{summary['total']}</div></div>
          <div class="stat"><div class="label">已提交</div><div class="value">{summary['submitted']}</div></div>
          <div class="stat"><div class="label">待提交</div><div class="value">{summary['pending']}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("作業中心", body)


@router.post("/my-assignments/{assignment_id}/submit")
def school_platform_assignment_submit(
    assignment_id: UUID,
    email: str = Form(...),
    content: str = Form(...),
):
    try:
        teaching_ops_service.submit_assignment(assignment_id, AssignmentSubmissionCreateRequest(email=email, content=content))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Assignment or student not found") from exc
    query = urlencode({"email": email})
    return RedirectResponse(url=f"/school-platform/my-assignments?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/my-exams", response_class=HTMLResponse)
def school_platform_student_exams_page(email: str = Query(...)) -> str:
    student = student_portal_service.get_student_by_email(email)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    exams = teaching_ops_service.student_exams(email)
    summary = teaching_ops_service.exam_submission_summary(email)
    submissions = {item.exam_id: item for item in teaching_ops_service.student_exam_submissions(email)}
    cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.exam_type)} / {escape(item.due_at.isoformat())}</div>"
            f"<h3>{escape(item.title)}</h3>"
            f"<p>{escape(item.instructions)}</p>"
            f"<div class='meta'><span class='chip'>總分 {item.total_score:g}</span><span class='chip'>{'已提交' if item.id in submissions else '待提交'}</span></div>"
            + (
                f"<p><code>提交時間：{escape(submissions[item.id].submitted_at.isoformat())}</code></p>"
                + (
                    f"<p><code>分數：{submissions[item.id].score:g} / 評語：{escape(submissions[item.id].feedback or '待補')}</code></p>"
                    if submissions[item.id].score is not None
                    else ""
                )
                if item.id in submissions
                else (
                    f"<form class='stack' method='post' action='/school-platform/my-exams/{item.id}/submit'>"
                    f"<input type='hidden' name='email' value='{escape(email)}' />"
                    "<label class='field'>測驗答案"
                    "<textarea name='content' placeholder='輸入你的測驗答案或口說稿'></textarea>"
                    "</label>"
                    "<button class='btn' type='submit'>提交測驗</button>"
                    "</form>"
                )
            )
            + "</article>"
        )
        for item in exams
    ) or "<article class='card'><h3>目前沒有測驗</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Exams Center</div>
        <h1>測驗中心</h1>
        <p>這裡集中顯示學員目前的測驗、截止時間、提交狀態與老師評分結果。</p>
        <div class="meta">
          <span class="chip">{escape(student.chinese_name)}</span>
          <span class="chip">{escape(student.email)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/my-assignments?email={escape(email)}">作業中心</a>
          <a class="btn alt" href="/school-platform/my-attendance?email={escape(email)}">出缺勤</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">測驗總數</div><div class="value">{summary['total']}</div></div>
          <div class="stat"><div class="label">已提交</div><div class="value">{summary['submitted']}</div></div>
          <div class="stat"><div class="label">待提交</div><div class="value">{summary['pending']}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("測驗中心", body)


@router.post("/my-exams/{exam_id}/submit")
def school_platform_exam_submit(
    exam_id: UUID,
    email: str = Form(...),
    content: str = Form(...),
):
    try:
        teaching_ops_service.submit_exam(exam_id, ExamSubmissionCreateRequest(email=email, content=content))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Exam or student not found") from exc
    query = urlencode({"email": email})
    return RedirectResponse(url=f"/school-platform/my-exams?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/my-attendance", response_class=HTMLResponse)
def school_platform_student_attendance_page(email: str = Query(...)) -> str:
    student = student_portal_service.get_student_by_email(email)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    records = teaching_ops_service.student_attendance(email)
    summary = teaching_ops_service.attendance_summary(email)
    cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.class_date.isoformat())}</div>"
        f"<h3>{escape(item.status)}</h3>"
        f"<p>{escape(item.note or '無備註')}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.marked_by)}</span></div>"
        "</article>"
        for item in records
    ) or "<article class='card'><h3>目前沒有出缺勤紀錄</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Attendance Center</div>
        <h1>出缺勤</h1>
        <p>這裡顯示學員目前的點名紀錄，方便快速確認出席狀態。</p>
        <div class="meta">
          <span class="chip">{escape(student.chinese_name)}</span>
          <span class="chip">{escape(student.email)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/my-assignments?email={escape(email)}">作業中心</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">總紀錄</div><div class="value">{summary['total']}</div></div>
          <div class="stat"><div class="label">出席</div><div class="value">{summary['present']}</div></div>
          <div class="stat"><div class="label">缺席</div><div class="value">{summary['absent']}</div></div>
          <div class="stat"><div class="label">遲到</div><div class="value">{summary['late']}</div></div>
          <div class="stat"><div class="label">請假</div><div class="value">{summary['leave']}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("出缺勤", body)


@router.get("/my-history", response_class=HTMLResponse)
def school_platform_student_history_page(email: str = Query(...)) -> str:
    student = student_portal_service.get_student_by_email(email)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    history = student_portal_service.student_history(email)
    cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.kind)}</div>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>{escape(item.detail)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.at.isoformat())}</span></div>"
        "</article>"
        for item in history
    ) or "<article class='card'><h3>尚無歷程</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Student History</div>
        <h1>我的歷程</h1>
        <p>這裡會把報名、付款、通知等重要事件整理成時間線，方便學員自己回看。</p>
        <div class="meta">
          <span class="chip">{escape(student.chinese_name)}</span>
          <span class="chip">{escape(student.email)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/notifications-center?email={escape(email)}">通知中心</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("我的歷程", body)


@router.get("/help-center", response_class=HTMLResponse)
def school_platform_help_center_page(email: str = Query(...)) -> str:
    student = student_portal_service.get_student_by_email(email)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    notifications = student_portal_service.student_notifications(email)[:4]
    recent_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>{escape(item.content)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.channel)}</span><span class='chip'>{escape(item.status)}</span></div>"
        "</article>"
        for item in notifications
    ) or "<article class='card'><h3>尚無通知紀錄</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Help Center</div>
        <h1>客服需求中心</h1>
        <p>學員可以在這裡提交需求，系統會自動建立內部通知並回送確認通知。</p>
        <div class="meta">
          <span class="chip">{escape(student.chinese_name)}</span>
          <span class="chip">{escape(student.email)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/notifications-center?email={escape(email)}">通知中心</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>提交需求</h2>
            <form class="stack" method="post" action="/school-platform/help-center/submit">
              <input type="hidden" name="email" value="{escape(email)}" />
              <label class="field">主題
                <select name="topic">
                  <option value="排課問題">排課問題</option>
                  <option value="付款問題">付款問題</option>
                  <option value="請假需求">請假需求</option>
                  <option value="教材需求">教材需求</option>
                </select>
              </label>
              <label class="field">偏好聯絡方式
                <select name="preferred_channel">
                  <option value="email">email</option>
                  <option value="line">line</option>
                  <option value="in_app">in_app</option>
                </select>
              </label>
              <label class="field">需求內容
                <textarea name="message" placeholder="輸入你的需求或想請客服協助的內容"></textarea>
              </label>
              <button class="btn" type="submit">送出客服需求</button>
            </form>
          </article>
          <article class="card">
            <h2>最近通知</h2>
            <div class="list">{recent_cards}</div>
          </article>
        </div>
      </section>
    """
    return _page_shell("客服需求中心", body)


@router.post("/help-center/submit")
def school_platform_help_center_submit(
    email: str = Form(...),
    topic: str = Form(...),
    preferred_channel: str = Form(default="email"),
    message: str = Form(...),
):
    result = student_support_service.create_support_request(email, topic, message, preferred_channel)
    query = urlencode(
        {
            "email": email,
            "request_id": str(result["request"].id),
            "topic": topic,
        }
    )
    return RedirectResponse(url=f"/school-platform/help-center/success?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/help-center/success", response_class=HTMLResponse)
def school_platform_help_center_success_page(
    email: str = Query(...),
    request_id: str = Query(...),
    topic: str = Query(...),
) -> str:
    body = f"""
      <section class="hero">
        <div class="eyebrow">Support Request Sent</div>
        <h1>客服需求已送出</h1>
        <p>系統已建立內部通知並回送確認給學員，後續可在通知中心查看。</p>
        <div class="meta">
          <span class="chip">{escape(email)}</span>
          <span class="chip">request_id: {escape(request_id)}</span>
          <span class="chip">主題：{escape(topic)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/notifications-center?email={escape(email)}">查看通知中心</a>
          <a class="btn alt" href="/school-platform/help-center?email={escape(email)}">再送一筆需求</a>
        </div>
      </section>
    """
    return _page_shell("客服需求已送出", body)


@router.get("/my-schedule", response_class=HTMLResponse)
def school_platform_student_schedule_page(email: str = Query(...)) -> str:
    try:
        student = student_portal_service.get_student_by_email(email)
        schedule = student_portal_service.student_schedule(email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.course_slug)}</div>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>日期：{escape(item.start_date.isoformat())} 至 {escape(item.end_date.isoformat())}</p>"
        f"<p>時間：{escape(item.weekday)} / {escape(item.start_time.strftime('%H:%M'))}-{escape(item.end_time.strftime('%H:%M'))}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.location_label)}</span><span class='chip'>{escape(item.teacher_name)}</span></div>"
        "</article>"
        for item in schedule
    ) or "<article class='card'><h3>目前沒有排課</h3><p>這位學員還沒有綁定任何班級。</p></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Student Schedule</div>
        <h1>我的課表</h1>
        <p>這頁集中顯示學員目前已綁定的班級與上課時段，方便從總覽直接進來查看。</p>
        <div class="meta">
          <span class="chip">{escape(student.chinese_name)}</span>
          <span class="chip">{escape(student.email)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/notifications-center?email={escape(email)}">通知中心</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("我的課表", body)


@router.get("/notifications-center", response_class=HTMLResponse)
def school_platform_notifications_center_page(email: str = Query(...)) -> str:
    try:
        student = student_portal_service.get_student_by_email(email)
        notifications = student_portal_service.student_notifications(email)
        summary = student_portal_service.student_notification_summary(email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.type)}</div>"
            f"<h3>{escape(item.title)}</h3>"
            f"<p>{escape(item.content)}</p>"
            f"<div class='meta'><span class='chip'>{escape(item.channel)}</span><span class='chip'>{escape(item.status)}</span><span class='chip'>{escape(item.created_at.isoformat())}</span></div>"
            + (
                f"<form class='stack' method='post' action='/school-platform/notifications-center/{item.id}/read'>"
                f"<input type='hidden' name='email' value='{escape(email)}' />"
                "<button class='btn' type='submit'>標記已讀</button>"
                "</form>"
                if item.status != "read"
                else "<p><code>已讀</code></p>"
            )
            + "</article>"
        )
        for item in notifications
    ) or "<article class='card'><h3>尚無通知</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Notifications Center</div>
        <h1>通知中心</h1>
        <p>這頁整理學員收到的報名、付款與系統通知，方便從學員端集中查看。</p>
        <div class="meta">
          <span class="chip">{escape(student.chinese_name)}</span>
          <span class="chip">{escape(student.email)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/student-portal?email={escape(email)}">回學員中心</a>
          <a class="btn alt" href="/school-platform/my-schedule?email={escape(email)}">我的課表</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">通知總數</div><div class="value">{summary['total']}</div></div>
          <div class="stat"><div class="label">待發送</div><div class="value">{summary['queued']}</div></div>
          <div class="stat"><div class="label">Email 通知</div><div class="value">{summary['email']}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("通知中心", body)


@router.post("/notifications-center/{notification_id}/read")
def school_platform_notification_mark_read_submit(
    notification_id: UUID,
    email: str = Form(...),
):
    try:
        student_support_service.mark_notification_read(email, notification_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Notification not found") from exc
    query = urlencode({"email": email})
    return RedirectResponse(url=f"/school-platform/notifications-center?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin", response_class=HTMLResponse)
def school_platform_admin_preview_page() -> str:
    metrics = admissions_service.dashboard_metrics()
    body = f"""
      <section class="hero">
        <div class="eyebrow">Admin Preview</div>
        <h1>營運後台總覽</h1>
        <p>這是目前管理端的中文預覽頁面，先把招生、報名、營收與待跟進重點可視化。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin/leads">查看招生名單</a>
          <a class="btn alt" href="/school-platform/consultant-portal?staff_name=Mika%20Chen">打開顧問工作台</a>
          <a class="btn alt" href="/school-platform/admin/staff">查看員工績效</a>
          <a class="btn alt" href="/school-platform/admin/students">查看學員管理</a>
          <a class="btn alt" href="/school-platform/admin/executive">打開主管工作台</a>
          <a class="btn alt" href="/school-platform/admin/finance">查看財務中心</a>
          <a class="btn alt" href="/school-platform/admin/schedule">查看排課中心</a>
          <a class="btn alt" href="/school-platform/admin/messages">查看訊息中心</a>
          <a class="btn alt" href="/school-platform/admin/classes">查看班級管理</a>
          <a class="btn alt" href="/school-platform/admin/courses">查看課程管理</a>
          <a class="btn alt" href="/school-platform/admin/teaching">查看教務管理</a>
          <a class="btn alt" href="/school-platform/admin/student-progress">查看學習進度</a>
          <a class="btn alt" href="/school-platform/admin/teachers">查看教師管理</a>
          <a class="btn alt" href="/school-platform/admin/recruiting">查看招聘管理</a>
          <a class="btn alt" href="/school-platform/admin/reports">查看報表中心</a>
          <a class="btn alt" href="/school-platform/admin/ai-center">查看 AI 助理中心</a>
          <a class="btn alt" href="/school-platform/admin/support-inbox">查看客服收件箱</a>
        </div>
      </section>
      <section class="section">
        <h2>今日與本週重點</h2>
        <div class="stat-grid">
          <div class="stat"><div class="label">今日新名單</div><div class="value">{metrics.today_new_leads}</div></div>
          <div class="stat"><div class="label">本週試聽</div><div class="value">{metrics.this_week_trial_bookings}</div></div>
          <div class="stat"><div class="label">本週報名</div><div class="value">{metrics.this_week_enrollments}</div></div>
          <div class="stat"><div class="label">已收營收</div><div class="value">{_format_jpy(metrics.paid_revenue_total)}</div></div>
          <div class="stat"><div class="label">待跟進</div><div class="value">{metrics.pending_follow_ups}</div></div>
          <div class="stat"><div class="label">開放班級</div><div class="value">{metrics.active_classes}</div></div>
        </div>
      </section>
    """
    return _page_shell("營運後台總覽", body)


@router.get("/admin/teaching", response_class=HTMLResponse)
def school_platform_admin_teaching_page() -> str:
    classes = catalog_service.open_classes()
    assignments = teaching_ops_service.list_assignments()
    exams = teaching_ops_service.list_exams()
    session_records = teaching_ops_service.list_teaching_session_records()
    pending_session_records = [item for item in session_records if item.approval_status == "submitted"]
    class_options = "".join(
        f"<option value='{item.id}'>{escape(item.name)} / {escape(item.course_slug)}</option>"
        for item in classes
    )
    assignment_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.created_by)}</div>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>{escape(item.content)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.due_at.isoformat())}</span></div>"
        "</article>"
        for item in assignments[:6]
    ) or "<article class='card'><h3>目前沒有作業</h3></article>"
    exam_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.exam_type)} / {escape(item.created_by)}</div>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>{escape(item.instructions)}</p>"
        f"<div class='meta'><span class='chip'>總分 {item.total_score:g}</span><span class='chip'>{escape(item.due_at.isoformat())}</span></div>"
        "</article>"
        for item in exams[:6]
    ) or "<article class='card'><h3>目前沒有測驗</h3></article>"
    pending_session_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.teacher_name)} / {escape(item.class_date.isoformat())}</div>"
        f"<h3>{escape(next((class_item.name for class_item in classes if class_item.id == item.class_id), '未知班級'))}</h3>"
        f"<p>{escape(item.summary)}</p>"
        f"<p>作業：{escape(item.homework_summary or '尚未填寫')}</p>"
        f"<p>高風險學員：{escape(' / '.join(item.student_risk_notes) or '無')}</p>"
        f"<form class='stack' method='post' action='/school-platform/admin/teaching/session-records/{item.id}/review'>"
        "<label class='field'>審核結果"
        "<select name='approval_status_value'>"
        "<option value='approved'>approved</option>"
        "<option value='revision_requested'>revision_requested</option>"
        "</select>"
        "</label>"
        "<label class='field'>主管回覆<textarea name='review_note' placeholder='例如：請補上弱勢學員追蹤與教材連結'></textarea></label>"
        "<label class='field'>審核者<input type='text' name='reviewed_by' value='Yuki Wang' /></label>"
        "<button class='btn' type='submit'>送出審核</button>"
        "</form>"
        "</article>"
        for item in pending_session_records[:6]
    ) or "<article class='card'><h3>目前沒有待審核課後紀錄</h3></article>"
    session_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.approval_status)} / {escape(item.class_date.isoformat())}</div>"
        f"<h3>{escape(next((class_item.name for class_item in classes if class_item.id == item.class_id), '未知班級'))}</h3>"
        f"<p>{escape(item.summary)}</p>"
        f"<p>主管回覆：{escape(item.review_note or '尚未回覆')}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.teacher_name)}</span><span class='chip'>{escape(item.reviewed_by or '待審核')}</span></div>"
        "</article>"
        for item in session_records[:6]
    ) or "<article class='card'><h3>目前沒有課後紀錄</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Teaching Ops</div>
        <h1>教務管理</h1>
        <p>這裡先把作業、測驗、評分、出缺勤點名與教師課後紀錄審核做成後台可操作頁。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/assignments">查看作業 JSON</a>
          <a class="btn alt" href="/school-platform/api/exams">查看測驗 JSON</a>
          <a class="btn alt" href="/school-platform/admin/student-progress">查看學習進度</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>發布作業</h2>
            <form class="stack" method="post" action="/school-platform/admin/teaching/assignments/create">
              <label class="field">班級
                <select name="class_id">{class_options}</select>
              </label>
              <label class="field">作業標題
                <input type="text" name="title" />
              </label>
              <label class="field">作業內容
                <textarea name="content"></textarea>
              </label>
              <label class="field">截止時間
                <input type="datetime-local" name="due_at" />
              </label>
              <label class="field">發布者
                <input type="text" name="created_by" value="Yuki Wang" />
              </label>
              <button class="btn" type="submit">建立作業</button>
            </form>
          </article>
          <article class="card">
            <h2>建立測驗</h2>
            <form class="stack" method="post" action="/school-platform/admin/teaching/exams/create">
              <label class="field">班級
                <select name="class_id">{class_options}</select>
              </label>
              <label class="field">測驗標題
                <input type="text" name="title" />
              </label>
              <label class="field">測驗類型
                <select name="exam_type">
                  <option value="quiz">quiz</option>
                  <option value="speaking_quiz">speaking_quiz</option>
                  <option value="mock_interview">mock_interview</option>
                </select>
              </label>
              <label class="field">說明
                <textarea name="instructions"></textarea>
              </label>
              <label class="field">總分
                <input type="number" step="1" name="total_score" value="100" />
              </label>
              <label class="field">截止時間
                <input type="datetime-local" name="due_at" />
              </label>
              <label class="field">建立者
                <input type="text" name="created_by" value="Aki Mori" />
              </label>
              <button class="btn" type="submit">建立測驗</button>
            </form>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>點名</h2>
            <form class="stack" method="post" action="/school-platform/admin/teaching/attendance/mark">
              <label class="field">班級
                <select name="class_id">{class_options}</select>
              </label>
              <label class="field">學生 Email
                <input type="email" name="student_email" />
              </label>
              <label class="field">上課日期
                <input type="date" name="class_date" />
              </label>
              <label class="field">狀態
                <select name="status_value">
                  <option value="present">present</option>
                  <option value="absent">absent</option>
                  <option value="late">late</option>
                  <option value="leave">leave</option>
                </select>
              </label>
              <label class="field">備註
                <textarea name="note"></textarea>
              </label>
              <label class="field">點名者
                <input type="text" name="marked_by" value="Yuki Wang" />
              </label>
              <button class="btn" type="submit">送出點名</button>
            </form>
          </article>
          <article class="card">
            <h2>教師工作台入口</h2>
            <p>從這裡可以進到教師自己的待評分區，查看哪些作業與測驗還沒批改。</p>
            <div class="actions">
              <a class="btn" href="/school-platform/teacher-portal?teacher_name=Aki%20Mori">打開 Aki Mori 工作台</a>
            </div>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>最新作業</h2>
        <div class="grid two">{assignment_cards}</div>
      </section>
      <section class="section">
        <h2>最新測驗</h2>
        <div class="grid two">{exam_cards}</div>
      </section>
      <section class="section">
        <h2>待審核課後紀錄</h2>
        <div class="grid two">{pending_session_cards}</div>
      </section>
      <section class="section">
        <h2>最近課後紀錄</h2>
        <div class="grid two">{session_cards}</div>
      </section>
    """
    return _page_shell("教務管理", body)


@router.get("/admin/student-progress", response_class=HTMLResponse)
def school_platform_admin_student_progress_page() -> str:
    items = teaching_ops_service.student_progress_overview()
    cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.risk_level)} / {escape(item.weak_spot)}</div>"
            f"<h3>{escape(item.chinese_name)}</h3>"
            f"<p>{escape(item.email)}</p>"
            f"<div class='meta'><span class='chip'>整體評估 {(f'{item.overall_score:g}' if item.overall_score is not None else 'N/A')}</span><span class='chip'>出席率 {item.attendance_rate:g}%</span></div>"
            f"<div class='meta'><span class='chip'>待補作業 {item.pending_assignments}</span><span class='chip'>待補測驗 {item.pending_exams}</span></div>"
            f"<div class='actions'><a class='btn' href='/school-platform/my-progress?email={escape(item.email)}'>查看學員進度</a></div>"
            "</article>"
        )
        for item in items
    ) or "<article class='card'><h3>目前沒有學員資料</h3></article>"
    high_risk = sum(1 for item in items if item.risk_level == "high")
    medium_risk = sum(1 for item in items if item.risk_level == "medium")
    average_score_items = [item.overall_score for item in items if item.overall_score is not None]
    average_score = f"{(sum(average_score_items) / len(average_score_items)):.1f}" if average_score_items else "N/A"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Learning Progress Admin</div>
        <h1>學習進度總覽</h1>
        <p>這裡讓教務、老師與主管快速看到目前學員的整體進度、缺交風險與出席狀況。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/admin/teaching">回教務管理</a>
          <a class="btn alt" href="/school-platform/api/admin/student-progress">查看進度 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">學員數</div><div class="value">{len(items)}</div></div>
          <div class="stat"><div class="label">高風險</div><div class="value">{high_risk}</div></div>
          <div class="stat"><div class="label">中風險</div><div class="value">{medium_risk}</div></div>
          <div class="stat"><div class="label">平均整體評估</div><div class="value">{average_score}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("學習進度總覽", body)


@router.get("/admin/students", response_class=HTMLResponse)
def school_platform_admin_students_page() -> str:
    snapshot = student_admin_service.overview()
    summary = snapshot.summary
    cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.student.status)} / {escape(item.student.japanese_level or 'unassigned')}</div>"
            f"<h3>{escape(item.student.chinese_name)}</h3>"
            f"<p>{escape(item.student.email)}</p>"
            f"<div class='meta'><span class='chip'>進行中課程 {item.active_course_count}</span><span class='chip'>報名 {item.enrollment_count}</span><span class='chip'>付款 {item.payment_count}</span></div>"
            f"<div class='meta'><span class='chip'>待付款 {item.pending_payment_count}</span><span class='chip'>通知 {item.notification_count}</span><span class='chip'>待處理 {item.queued_notification_count}</span></div>"
            f"<div class='actions'><a class='btn' href='/school-platform/admin/students/detail?{urlencode({'email': item.student.email})}'>查看學員檔案</a><a class='btn alt' href='/school-platform/my-progress?{urlencode({'email': item.student.email})}'>查看學員進度</a></div>"
            "</article>"
        )
        for item in snapshot.items
    ) or "<article class='card'><h3>目前沒有學員資料</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Student Admin</div>
        <h1>學員管理</h1>
        <p>這裡把學員名單、付款狀態、通知與最近活動整合成營運後台可直接查閱的工作頁。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/admin/students">查看學員 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">學員總數</div><div class="value">{summary.total_students}</div></div>
          <div class="stat"><div class="label">進行中學員</div><div class="value">{summary.active_students}</div></div>
          <div class="stat"><div class="label">待付款學員</div><div class="value">{summary.pending_payment_students}</div></div>
          <div class="stat"><div class="label">待處理通知</div><div class="value">{summary.queued_notification_students}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>學員名單</h2>
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("學員管理", body)


@router.get("/admin/students/detail", response_class=HTMLResponse)
def school_platform_admin_student_detail_page(email: str = Query(...)) -> str:
    try:
        snapshot = student_admin_service.detail(email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    item = snapshot.item
    class_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(class_item.course_slug)} / {escape(class_item.teacher_name)}</div>"
            f"<h3>{escape(class_item.name)}</h3>"
            f"<p>{escape(class_item.weekday)} {escape(class_item.start_time.strftime('%H:%M'))}-{escape(class_item.end_time.strftime('%H:%M'))}</p>"
            f"<div class='meta'><span class='chip'>{escape(class_item.location_label)}</span><span class='chip'>{escape(class_item.status)}</span></div>"
            "</article>"
        )
        for class_item in snapshot.classes
    ) or "<article class='card'><h3>目前沒有進行中課程</h3></article>"
    payment_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(payment.status)} / {escape(payment.payment_method)}</div>"
            f"<h3>{escape(payment.order_no)}</h3>"
            f"<p>金額 {_format_jpy(payment.amount)}</p>"
            f"<div class='meta'><span class='chip'>{escape((payment.paid_at or payment.created_at).isoformat())}</span></div>"
            "</article>"
        )
        for payment in snapshot.payments[:6]
    ) or "<article class='card'><h3>目前沒有付款紀錄</h3></article>"
    history_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(event.kind)}</div>"
            f"<h3>{escape(event.title)}</h3>"
            f"<p>{escape(event.detail)}</p>"
            f"<div class='meta'><span class='chip'>{escape(event.at.isoformat())}</span></div>"
            "</article>"
        )
        for event in snapshot.history[:8]
    ) or "<article class='card'><h3>尚無歷程</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Student Profile</div>
        <h1>學員檔案</h1>
        <p>可直接查看學員的課程、付款、通知與最近歷程，讓顧問、客服與主管共用同一份學員視圖。</p>
        <div class="meta">
          <span class="chip">{escape(item.student.chinese_name)}</span>
          <span class="chip">{escape(item.student.email)}</span>
          <span class="chip">{escape(item.student.japanese_level or 'unassigned')}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/admin/students">回學員管理</a>
          <a class="btn alt" href="/school-platform/admin/messages">前往訊息中心</a>
          <a class="btn alt" href="/school-platform/api/admin/students/detail?{urlencode({'email': item.student.email})}">查看學員詳情 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">報名數</div><div class="value">{item.enrollment_count}</div></div>
          <div class="stat"><div class="label">進行中課程</div><div class="value">{item.active_course_count}</div></div>
          <div class="stat"><div class="label">付款數</div><div class="value">{item.payment_count}</div></div>
          <div class="stat"><div class="label">通知數</div><div class="value">{item.notification_count}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>目前課程</h2>
        <div class="grid two">{class_cards}</div>
      </section>
      <section class="section">
        <h2>最近付款</h2>
        <div class="grid two">{payment_cards}</div>
      </section>
      <section class="section">
        <h2>最近歷程</h2>
        <div class="grid two">{history_cards}</div>
      </section>
    """
    return _page_shell("學員檔案", body)


@router.get("/admin/staff", response_class=HTMLResponse)
def school_platform_admin_staff_page() -> str:
    overview = staff_ops_service.performance_overview()
    summary = overview["summary"]
    items = overview["items"]
    cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.role)} / {escape(item.department)}</div>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>{escape(item.title)}</p>"
        f"<div class='meta'><span class='chip'>指派名單 {item.assigned_leads}</span><span class='chip'>成交 {item.enrolled_leads}</span><span class='chip'>待跟進 {item.pending_follow_ups}</span></div>"
        f"<div class='meta'><span class='chip'>授課班級 {item.active_classes}</span><span class='chip'>作業 {item.assignments_created}</span><span class='chip'>測驗 {item.exams_created}</span><span class='chip'>待評分 {item.pending_reviews}</span></div>"
        + (
            f"<div class='actions'><a class='btn' href='/school-platform/teacher-portal?teacher_name={escape(item.name)}'>查看教師工作台</a></div>"
            if item.role == "teacher"
            else (
                f"<div class='actions'><a class='btn' href='/school-platform/consultant-portal?staff_name={escape(item.name)}'>查看顧問工作台</a></div>"
                if item.role == "consultant"
                else ""
            )
        )
        + "</article>"
        for item in items
    ) or "<article class='card'><h3>目前沒有員工資料</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Staff Performance</div>
        <h1>員工績效中心</h1>
        <p>這裡把招生顧問、教師與主管目前的工作量與待處理事項整合成主管可以直接看的管理頁。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/admin/staff-performance">查看績效 JSON</a>
          <a class="btn alt" href="/school-platform/admin/teachers">查看教師管理</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">員工總數</div><div class="value">{summary.total_staff}</div></div>
          <div class="stat"><div class="label">招生顧問</div><div class="value">{summary.consultants}</div></div>
          <div class="stat"><div class="label">教師</div><div class="value">{summary.teachers}</div></div>
          <div class="stat"><div class="label">主管</div><div class="value">{summary.managers}</div></div>
          <div class="stat"><div class="label">待跟進總數</div><div class="value">{summary.pending_follow_ups}</div></div>
          <div class="stat"><div class="label">待評分總數</div><div class="value">{summary.pending_reviews}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("員工績效中心", body)


@router.get("/consultant-portal", response_class=HTMLResponse)
def school_platform_consultant_portal_page(staff_name: str = Query(default="Mika Chen")) -> str:
    snapshot = consultant_workspace_service.dashboard(staff_name)
    summary = snapshot.summary

    def render_lead_card(item) -> str:
        due_label = item.next_follow_up_at.isoformat() if item.next_follow_up_at else "尚未安排"
        latest_log = escape(item.latest_log_summary or "尚未留下跟進紀錄")
        return (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.status)} / {escape(item.interested_course_slug or '未指定課程')}</div>"
            f"<h3>{escape(item.name)}</h3>"
            f"<p>{latest_log}</p>"
            f"<div class='meta'><span class='chip'>熱度 {item.intent_score:g}</span><span class='chip'>成交率 {item.win_probability:g}%</span></div>"
            f"<p><code>下次跟進：{escape(due_label)}</code></p>"
            f"<div class='actions'><a class='btn' href='/school-platform/consultant-portal/leads/{item.lead_id}?staff_name={escape(summary.consultant_name)}'>打開案件詳情</a></div>"
            "</article>"
        )

    hot_cards = "".join(render_lead_card(item) for item in snapshot.hot_leads) or "<article class='card'><h3>目前沒有高意向名單</h3></article>"
    queue_cards = "".join(render_lead_card(item) for item in snapshot.follow_up_queue) or "<article class='card'><h3>目前沒有待跟進名單</h3></article>"
    recent_cards = "".join(render_lead_card(item) for item in snapshot.recently_updated) or "<article class='card'><h3>目前沒有最近更新名單</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Consultant Workspace</div>
        <h1>招生顧問工作台</h1>
        <p>這裡把顧問最常用的名單熱度、今日待跟進與最近更新集中成一個工作台，不用一直在 leads 列表來回切換。</p>
        <div class="meta">
          <span class="chip">{escape(summary.consultant_name)}</span>
          <span class="chip">已指派 {summary.assigned_leads}</span>
          <span class="chip">高意向 {summary.high_intent_leads}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/admin/leads">回招生名單</a>
          <a class="btn alt" href="/school-platform/admin/staff">回員工績效中心</a>
          <a class="btn alt" href="/school-platform/api/consultant/dashboard?staff_name={escape(summary.consultant_name)}">查看工作台 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">已指派名單</div><div class="value">{summary.assigned_leads}</div></div>
          <div class="stat"><div class="label">逾期待跟進</div><div class="value">{summary.overdue_follow_ups}</div></div>
          <div class="stat"><div class="label">今日要跟進</div><div class="value">{summary.due_today}</div></div>
          <div class="stat"><div class="label">高意向名單</div><div class="value">{summary.high_intent_leads}</div></div>
          <div class="stat"><div class="label">試聽進行中</div><div class="value">{summary.trial_booked_leads}</div></div>
          <div class="stat"><div class="label">已成交</div><div class="value">{summary.enrolled_leads}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>高意向名單</h2>
        <div class="grid two">{hot_cards}</div>
      </section>
      <section class="section">
        <h2>待跟進隊列</h2>
        <div class="grid two">{queue_cards}</div>
      </section>
      <section class="section">
        <h2>最近更新</h2>
        <div class="grid two">{recent_cards}</div>
      </section>
    """
    return _page_shell("招生顧問工作台", body)


@router.get("/consultant-portal/leads/{lead_id}", response_class=HTMLResponse)
def school_platform_consultant_lead_detail_page(lead_id: UUID, staff_name: str = Query(...)) -> str:
    try:
        snapshot = consultant_workspace_service.lead_detail(staff_name, lead_id)
        snapshot = snapshot.model_copy(update={"followup_draft": ai_assistant_service.followup_draft(lead_id)})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Consultant lead not found") from exc

    lead = snapshot.lead
    draft = snapshot.followup_draft
    log_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.contact_method)}</div>"
        f"<h3>{escape(item.staff_name)}</h3>"
        f"<p>{escape(item.content)}</p>"
        f"<p>下一步：{escape(item.next_action or '待補')}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.created_at.isoformat())}</span></div>"
        "</article>"
        for item in snapshot.logs
    ) or "<article class='card'><h3>尚無跟進紀錄</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Consultant Lead Detail</div>
        <h1>顧問案件詳情</h1>
        <p>這裡集中顯示顧問自己的招生案件、歷次跟進與 AI 話術草稿，方便直接接續下一步。</p>
        <div class="meta">
          <span class="chip">{escape(staff_name)}</span>
          <span class="chip">{escape(lead.name)}</span>
          <span class="chip">{escape(lead.status)}</span>
          <span class="chip">熱度 {lead.intent_score:.0f}</span>
          <span class="chip">成交率 {lead.win_probability:.0f}%</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/consultant-portal?staff_name={escape(staff_name)}">回顧問工作台</a>
          <a class="btn alt" href="/school-platform/api/consultant/leads/{lead.id}?staff_name={escape(staff_name)}">查看案件 JSON</a>
          <a class="btn alt" href="/school-platform/api/ai/leads/{lead.id}/followup-draft">查看 AI 草稿 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>案件摘要</h2>
            <p>Email：{escape(lead.email or '未填寫')}</p>
            <p>電話：{escape(lead.phone or '未填寫')}</p>
            <p>LINE：{escape(lead.line_id or '未綁定')}</p>
            <p>課程意向：{escape(lead.interested_course_slug or '未指定')}</p>
            <p>程度：{escape(lead.japanese_level or '未填寫')}</p>
            <p>目標：{escape(lead.study_goal or '未填寫')}</p>
          </article>
          <article class="card">
            <h2>AI 跟進草稿</h2>
            <p>建議渠道：<code>{escape(draft.recommended_channel if draft else 'n/a')}</code></p>
            <p>建議下一步：{escape(draft.next_step if draft else '尚無')}</p>
            <p>LINE 話術草稿：{escape(draft.line_message if draft else '尚無')}</p>
            <p>Email 主旨：{escape(draft.email_subject if draft else '尚無')}</p>
            <p>Email 內容：{escape(draft.email_message if draft else '尚無')}</p>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>跟進紀錄</h2>
        <div class="grid two">{log_cards}</div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>更新狀態</h2>
            <form class="stack" method="post" action="/school-platform/consultant-portal/leads/{lead.id}/status">
              <input type="hidden" name="staff_name" value="{escape(staff_name)}" />
              <label class="field">狀態
                <select name="status_value">
                  <option value="new">new</option>
                  <option value="contacted" {'selected' if lead.status == 'contacted' else ''}>contacted</option>
                  <option value="replied" {'selected' if lead.status == 'replied' else ''}>replied</option>
                  <option value="trial_booked" {'selected' if lead.status == 'trial_booked' else ''}>trial_booked</option>
                  <option value="trial_completed" {'selected' if lead.status == 'trial_completed' else ''}>trial_completed</option>
                  <option value="considering" {'selected' if lead.status == 'considering' else ''}>considering</option>
                  <option value="enrolled" {'selected' if lead.status == 'enrolled' else ''}>enrolled</option>
                  <option value="waitlisted" {'selected' if lead.status == 'waitlisted' else ''}>waitlisted</option>
                  <option value="lost" {'selected' if lead.status == 'lost' else ''}>lost</option>
                  <option value="blacklisted" {'selected' if lead.status == 'blacklisted' else ''}>blacklisted</option>
                </select>
              </label>
              <label class="field">下次跟進時間
                <input type="datetime-local" name="next_follow_up_at" />
              </label>
              <label class="field">備註
                <textarea name="note" placeholder="例如：先發 LINE，明天下午再電話追蹤"></textarea>
              </label>
              <button class="btn" type="submit">送出狀態更新</button>
            </form>
          </article>
          <article class="card">
            <h2>新增跟進</h2>
            <form class="stack" method="post" action="/school-platform/consultant-portal/leads/{lead.id}/logs">
              <input type="hidden" name="staff_name" value="{escape(staff_name)}" />
              <label class="field">聯繫方式
                <select name="contact_method">
                  <option value="line">line</option>
                  <option value="call">call</option>
                  <option value="email">email</option>
                  <option value="system">system</option>
                </select>
              </label>
              <label class="field">紀錄內容
                <textarea name="content" placeholder="輸入這次跟進的內容"></textarea>
              </label>
              <label class="field">下一步
                <input type="text" name="next_action" placeholder="例如：後天再確認是否預約試聽" />
              </label>
              <button class="btn" type="submit">新增跟進紀錄</button>
            </form>
          </article>
        </div>
      </section>
    """
    return _page_shell(f"顧問案件詳情 - {lead.name}", body)


@router.post("/consultant-portal/leads/{lead_id}/status")
def school_platform_consultant_lead_status_submit(
    lead_id: UUID,
    staff_name: str = Form(...),
    status_value: str = Form(...),
    next_follow_up_at: str = Form(default=""),
    note: str = Form(default=""),
):
    next_follow_up = datetime.fromisoformat(next_follow_up_at) if next_follow_up_at else None
    payload = LeadStatusChangeRequest(status=status_value, next_follow_up_at=next_follow_up, note=note or None)
    lead_workflow_service.change_status(lead_id, payload)
    query = urlencode({"staff_name": staff_name})
    return RedirectResponse(url=f"/school-platform/consultant-portal/leads/{lead_id}?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/consultant-portal/leads/{lead_id}/logs")
def school_platform_consultant_lead_log_submit(
    lead_id: UUID,
    staff_name: str = Form(...),
    contact_method: str = Form(...),
    content: str = Form(...),
    next_action: str = Form(default=""),
):
    lead_workflow_service.add_log(lead_id, staff_name, contact_method, content, next_action or None)
    query = urlencode({"staff_name": staff_name})
    return RedirectResponse(url=f"/school-platform/consultant-portal/leads/{lead_id}?{query}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/finance", response_class=HTMLResponse)
def school_platform_admin_finance_page() -> str:
    snapshot = finance_service.overview()
    summary = snapshot.summary
    enrollment_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.status)} / {escape(item.payment_status)}</div>"
            f"<h3>{escape(str(item.id)[:8])}</h3>"
            f"<p>班級 ID：{escape(str(item.class_id))}</p>"
            f"<div class='meta'><span class='chip'>定價 {_format_jpy(item.list_price)}</span><span class='chip'>實收 {_format_jpy(item.paid_amount)}</span></div>"
            f"<p><code>建立時間：{escape(item.created_at.isoformat())}</code></p>"
            "</article>"
        )
        for item in snapshot.recent_enrollments
    ) or "<article class='card'><h3>目前沒有報名資料</h3></article>"
    payment_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.status)} / {escape(item.payment_method)}</div>"
            f"<h3>{escape(item.order_no)}</h3>"
            f"<p>付款單號：{escape(str(item.id)[:8])}</p>"
            f"<div class='meta'><span class='chip'>{_format_jpy(item.amount)}</span></div>"
            f"<p><code>建立時間：{escape(item.created_at.isoformat())}</code></p>"
            + (f"<p><code>付款時間：{escape(item.paid_at.isoformat())}</code></p>" if item.paid_at else "")
            + "</article>"
        )
        for item in snapshot.recent_payments
    ) or "<article class='card'><h3>目前沒有付款資料</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Finance Center</div>
        <h1>財務中心</h1>
        <p>這裡把報名、付款、待收款與退款狀態整理成主管可直接看的財務入口。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/finance/overview">查看財務 JSON</a>
          <a class="btn alt" href="/school-platform/payment?email=portal@example.com">查看學員付款中心範例</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">報名總數</div><div class="value">{summary.enrollment_total}</div></div>
          <div class="stat"><div class="label">待確認報名</div><div class="value">{summary.pending_enrollments}</div></div>
          <div class="stat"><div class="label">已付款筆數</div><div class="value">{summary.paid_payments}</div></div>
          <div class="stat"><div class="label">待付款筆數</div><div class="value">{summary.pending_payments}</div></div>
          <div class="stat"><div class="label">已收款</div><div class="value">{_format_jpy(summary.paid_revenue)}</div></div>
          <div class="stat"><div class="label">待收款</div><div class="value">{_format_jpy(summary.pending_revenue)}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>最近報名</h2>
        <div class="grid two">{enrollment_cards}</div>
      </section>
      <section class="section">
        <h2>最近付款</h2>
        <div class="grid two">{payment_cards}</div>
      </section>
    """
    return _page_shell("財務中心", body)


@router.get("/admin/messages", response_class=HTMLResponse)
def school_platform_admin_messages_page() -> str:
    summary = notification_service.summary()
    provider_status = notification_service.provider_status()
    recent_notifications = admissions_service.list_notifications()[:12]
    notification_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.type)} / {escape(item.channel)}</div>"
            f"<h3>{escape(item.title)}</h3>"
            f"<p>{escape(item.content)}</p>"
            f"<div class='meta'><span class='chip'>{escape(item.user_email or 'broadcast')}</span><span class='chip'>{escape(item.status)}</span><span class='chip'>{escape(item.provider or 'internal')}</span><span class='chip'>{escape(item.created_at.isoformat())}</span></div>"
            "</article>"
        )
        for item in recent_notifications
    ) or "<article class='card'><h3>目前沒有通知紀錄</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Message Center</div>
        <h1>訊息中心</h1>
        <p>這裡集中處理站內 / Email / LINE 類型通知，支援單一學員或全體學員廣播，方便行政與客服直接操作。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/messages/overview">查看訊息總覽 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">通知總數</div><div class="value">{summary.total_notifications}</div></div>
          <div class="stat"><div class="label">待送出</div><div class="value">{summary.queued_notifications}</div></div>
          <div class="stat"><div class="label">已送達</div><div class="value">{summary.sent_notifications}</div></div>
          <div class="stat"><div class="label">送達失敗</div><div class="value">{summary.failed_notifications}</div></div>
          <div class="stat"><div class="label">已讀</div><div class="value">{summary.read_notifications}</div></div>
          <div class="stat"><div class="label">Email</div><div class="value">{summary.email_notifications}</div></div>
          <div class="stat"><div class="label">LINE</div><div class="value">{summary.line_notifications}</div></div>
          <div class="stat"><div class="label">站內通知</div><div class="value">{summary.in_app_notifications}</div></div>
          <div class="stat"><div class="label">廣播訊息</div><div class="value">{summary.broadcast_notifications}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>發送訊息</h2>
            <form class="stack" method="post" action="/school-platform/admin/messages/send">
              <label class="field">對象
                <select name="audience">
                  <option value="single_student">單一學員</option>
                  <option value="active_students">進行中學員</option>
                  <option value="all_students">全部學員</option>
                  <option value="staff_admin">管理團隊</option>
                </select>
              </label>
              <label class="field">指定 Email（單一學員時使用）
                <input type="email" name="target_email" placeholder="student@example.com" />
              </label>
              <label class="field">渠道
                <select name="channel">
                  <option value="email">email</option>
                  <option value="in_app">in_app</option>
                  <option value="line">line</option>
                </select>
              </label>
              <label class="field">標題
                <input type="text" name="title" />
              </label>
              <label class="field">內容
                <textarea name="content"></textarea>
              </label>
              <button class="btn" type="submit">發送訊息</button>
            </form>
          </article>
          <article class="card">
            <h2>常用模板</h2>
            <ul class="clean">
              <li>開課提醒：提醒學員確認開課時間、教材與上課連結。</li>
              <li>補課通知：提醒學員因課程異動需重新確認上課安排。</li>
              <li>付款提醒：通知待付款學員在截止日前完成付款。</li>
              <li>試聽提醒：提醒試聽學員在指定時間前準備進入教室或 Zoom。</li>
            </ul>
            <p>Email provider：<code>{escape(str(provider_status['email_provider']))}</code></p>
            <p>Email ready：<code>{escape(str(provider_status['email_ready']).lower())}</code></p>
            <p>LINE ready：<code>{escape(str(provider_status['line_ready']).lower())}</code></p>
            <div class="actions">
              <form method="post" action="/school-platform/admin/messages/drain">
                <button class="btn alt" type="submit">重送 queued 通知</button>
              </form>
            </div>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>最近通知紀錄</h2>
        <div class="grid two">{notification_cards}</div>
      </section>
    """
    return _page_shell("訊息中心", body)


@router.post("/admin/messages/send")
def school_platform_admin_messages_send_submit(
    audience: str = Form(...),
    channel: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    target_email: str | None = Form(default=None),
):
    try:
        notification_service.broadcast(
            BroadcastMessageRequest(
                audience=audience,
                channel=channel,
                title=title,
                content=content,
                target_email=target_email or None,
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="Target email required for single student") from exc
    return RedirectResponse(url="/school-platform/admin/messages", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/messages/drain")
def school_platform_admin_messages_drain_submit():
    notification_service.drain_queued_notifications()
    return RedirectResponse(url="/school-platform/admin/messages", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/schedule", response_class=HTMLResponse)
def school_platform_admin_schedule_page() -> str:
    snapshot = scheduling_service.overview()
    summary = snapshot.summary
    teacher_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.teacher_name)}</div>"
            f"<h3>授課班級 {item.class_count}</h3>"
            f"<div class='meta'><span class='chip'>每週堂數 {item.weekly_sessions}</span><span class='chip'>每週工時 {item.weekly_hours:g}</span></div>"
            "</article>"
        )
        for item in snapshot.teacher_loads
    ) or "<article class='card'><h3>目前沒有教師排課資料</h3></article>"
    class_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.teacher_name)} / {escape(item.course_slug)}</div>"
            f"<h3>{escape(item.name)}</h3>"
            f"<p>{escape(item.weekday)} {escape(item.start_time.strftime('%H:%M'))}-{escape(item.end_time.strftime('%H:%M'))}</p>"
            f"<div class='meta'><span class='chip'>{escape(item.location_label)}</span><span class='chip'>名額 {item.enrolled_count}/{item.capacity}</span></div>"
            "</article>"
        )
        for item in snapshot.classes[:12]
    ) or "<article class='card'><h3>目前沒有班級資料</h3></article>"
    conflict_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.teacher_name)} / {escape(item.weekday)}</div>"
            f"<h3>{escape(' / '.join(item.class_names))}</h3>"
            f"<p>{escape(item.time_range)}</p>"
            f"<p>{escape(item.overlap_note)}</p>"
            "</article>"
        )
        for item in snapshot.conflicts
    ) or "<article class='card'><h3>目前未偵測到衝堂</h3><p>現有班級安排沒有教師時段重疊。</p></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Scheduling Center</div>
        <h1>排課中心</h1>
        <p>這裡把目前所有開課班級、教師排課負載與衝堂風險集中整理，方便主管直接檢查排課品質。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/admin/classes">回班級管理</a>
          <a class="btn alt" href="/school-platform/api/admin/schedule">查看排課 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">開放班級</div><div class="value">{summary.total_open_classes}</div></div>
          <div class="stat"><div class="label">已排教師</div><div class="value">{summary.teachers_scheduled}</div></div>
          <div class="stat"><div class="label">線上班級</div><div class="value">{summary.online_classes}</div></div>
          <div class="stat"><div class="label">實體班級</div><div class="value">{summary.onsite_classes}</div></div>
          <div class="stat"><div class="label">衝堂數</div><div class="value">{summary.detected_conflicts}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>教師排課負載</h2>
        <div class="grid two">{teacher_cards}</div>
      </section>
      <section class="section">
        <h2>排課衝堂檢查</h2>
        <div class="grid two">{conflict_cards}</div>
      </section>
      <section class="section">
        <h2>班級時段總覽</h2>
        <div class="grid two">{class_cards}</div>
      </section>
    """
    return _page_shell("排課中心", body)


@router.post("/admin/teaching/assignments/create")
def school_platform_admin_assignment_create_submit(
    class_id: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    due_at: str = Form(...),
    created_by: str = Form(default="Yuki Wang"),
):
    teaching_ops_service.create_assignment(
        AssignmentCreateRequest(
            class_id=UUID(class_id),
            title=title,
            content=content,
            due_at=datetime.fromisoformat(due_at),
            created_by=created_by or "Yuki Wang",
        )
    )
    return RedirectResponse(url="/school-platform/admin/teaching", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/teaching/exams/create")
def school_platform_admin_exam_create_submit(
    class_id: str = Form(...),
    title: str = Form(...),
    exam_type: str = Form(...),
    instructions: str = Form(...),
    total_score: float = Form(default=100),
    due_at: str = Form(...),
    created_by: str = Form(default="Aki Mori"),
):
    teaching_ops_service.create_exam(
        ExamCreateRequest(
            class_id=UUID(class_id),
            title=title,
            exam_type=exam_type,
            instructions=instructions,
            total_score=total_score,
            due_at=datetime.fromisoformat(due_at),
            created_by=created_by or "Aki Mori",
        )
    )
    return RedirectResponse(url="/school-platform/admin/teaching", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/teaching/attendance/mark")
def school_platform_admin_attendance_mark_submit(
    class_id: str = Form(...),
    student_email: str = Form(...),
    class_date: str = Form(...),
    status_value: str = Form(...),
    note: str = Form(default=""),
    marked_by: str = Form(default="Yuki Wang"),
):
    try:
        teaching_ops_service.mark_attendance(
            AttendanceMarkRequest(
                class_id=UUID(class_id),
                student_email=student_email,
                class_date=date.fromisoformat(class_date),
                status=status_value,
                note=note or None,
                marked_by=marked_by or "Yuki Wang",
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    return RedirectResponse(url="/school-platform/admin/teaching", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/teaching/session-records/{record_id}/review")
def school_platform_admin_teaching_session_review_submit(
    record_id: UUID,
    approval_status_value: str = Form(...),
    review_note: str = Form(default=""),
    reviewed_by: str = Form(default="Yuki Wang"),
):
    try:
        teaching_ops_service.review_teaching_session_record(
            record_id,
            TeachingSessionReviewRequest(
                approval_status=approval_status_value,
                review_note=review_note or None,
                reviewed_by=reviewed_by or "Yuki Wang",
            ),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Teaching session record not found") from exc
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="Invalid teaching session review payload") from exc
    return RedirectResponse(url="/school-platform/admin/teaching", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/leads", response_class=HTMLResponse)
def school_platform_admin_leads_page() -> str:
    leads = admissions_service.list_leads()
    lead_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.status)}</div>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>課程意向：{escape(item.interested_course_slug or '未指定')}</p>"
        f"<p>程度：{escape(item.japanese_level or '未填寫')} / 來源：{escape(item.source_channel)}</p>"
        f"<div class='meta'>"
        f"<span class='chip'>熱度 {item.intent_score:.0f}</span>"
        f"<span class='chip'>成交率 {item.win_probability:.0f}%</span>"
        f"<span class='chip'>{escape(item.assigned_staff_name or '未指派')}</span>"
        "</div>"
        f"<div class='actions'><a class='btn' href='/school-platform/admin/leads/{item.id}'>查看名單詳情</a></div>"
        "</article>"
        for item in leads
    ) or "<article class='card'><h3>目前沒有名單</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Admissions CRM</div>
        <h1>招生名單管理</h1>
        <p>這裡先把名單列表做成可視化頁面，下一步會接 lead 詳頁與跟進紀錄操作。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/leads">查看 leads JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{lead_cards}</div>
      </section>
    """
    return _page_shell("招生名單管理", body)


@router.get("/admin/leads/{lead_id}", response_class=HTMLResponse)
def school_platform_admin_lead_detail_page(lead_id: UUID) -> str:
    try:
        lead = admissions_service.get_lead(lead_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc
    logs = admissions_service.logs_for_lead(lead_id)
    staff_options = "".join(
        f"<option value='{item.id}' {'selected' if item.name == lead.assigned_staff_name else ''}>{escape(item.name)} / {escape(item.title)}</option>"
        for item in admissions_service.list_staff()
        if item.role in {"consultant", "manager"}
    )
    log_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.contact_method)}</div>"
        f"<h3>{escape(item.staff_name)}</h3>"
        f"<p>{escape(item.content)}</p>"
        f"<p>下一步：{escape(item.next_action or '待補')}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.created_at.isoformat())}</span></div>"
        "</article>"
        for item in logs
    ) or "<article class='card'><h3>尚無跟進紀錄</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Lead Detail</div>
        <h1>{escape(lead.name)}</h1>
        <p>這頁會集中顯示名單狀態、熱度、顧問與歷次跟進，方便下一步接真實操作。</p>
        <div class="meta">
          <span class="chip">{escape(lead.status)}</span>
          <span class="chip">熱度 {lead.intent_score:.0f}</span>
          <span class="chip">成交率 {lead.win_probability:.0f}%</span>
          <span class="chip">{escape(lead.assigned_staff_name or '未指派')}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/admin/leads">回名單列表</a>
          <a class="btn alt" href="/school-platform/api/leads/{lead.id}">查看 lead JSON</a>
        </div>
      </section>
      <section class="section">
        <h2>名單摘要</h2>
        <div class="grid two">
          <article class="card">
            <h3>聯絡資訊</h3>
            <p>Email：{escape(lead.email or '未填寫')}</p>
            <p>電話：{escape(lead.phone or '未填寫')}</p>
            <p>LINE：{escape(lead.line_id or '未綁定')}</p>
          </article>
          <article class="card">
            <h3>學習背景</h3>
            <p>課程意向：{escape(lead.interested_course_slug or '未指定')}</p>
            <p>程度：{escape(lead.japanese_level or '未填寫')}</p>
            <p>目標：{escape(lead.study_goal or '未填寫')}</p>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>跟進紀錄</h2>
        <div class="grid two">{log_cards}</div>
      </section>
      <section class="section">
        <h2>操作區塊</h2>
        <div class="grid two">
          <article class="card">
            <h3>重新指派顧問</h3>
            <form class="stack" method="post" action="/school-platform/admin/leads/{lead.id}/assign">
              <label class="field">顧問
                <select name="staff_id">{staff_options}</select>
              </label>
              <button class="btn" type="submit">送出指派</button>
            </form>
          </article>
          <article class="card">
            <h3>更新狀態</h3>
            <form class="stack" method="post" action="/school-platform/admin/leads/{lead.id}/status">
              <label class="field">狀態
                <select name="status_value">
                  <option value="new">new</option>
                  <option value="contacted">contacted</option>
                  <option value="replied">replied</option>
                  <option value="trial_booked" selected>trial_booked</option>
                  <option value="trial_completed">trial_completed</option>
                  <option value="considering">considering</option>
                  <option value="enrolled">enrolled</option>
                  <option value="waitlisted">waitlisted</option>
                  <option value="lost">lost</option>
                  <option value="blacklisted">blacklisted</option>
                </select>
              </label>
              <label class="field">下次跟進時間
                <input type="datetime-local" name="next_follow_up_at" />
              </label>
              <label class="field">備註
                <textarea name="note" placeholder="例如：已約好明天下午再聯繫"></textarea>
              </label>
              <button class="btn" type="submit">送出狀態更新</button>
            </form>
          </article>
          <article class="card">
            <h3>新增跟進</h3>
            <form class="stack" method="post" action="/school-platform/admin/leads/{lead.id}/logs">
              <label class="field">顧問名稱
                <input type="text" name="staff_name" value="{escape(lead.assigned_staff_name or 'System')}" />
              </label>
              <label class="field">聯繫方式
                <select name="contact_method">
                  <option value="system">system</option>
                  <option value="line">line</option>
                  <option value="call">call</option>
                  <option value="email">email</option>
                </select>
              </label>
              <label class="field">紀錄內容
                <textarea name="content" placeholder="輸入這次跟進的內容"></textarea>
              </label>
              <label class="field">下一步
                <input type="text" name="next_action" placeholder="例如：兩天後再次確認是否預約試聽" />
              </label>
              <button class="btn" type="submit">新增跟進紀錄</button>
            </form>
          </article>
        </div>
      </section>
    """
    return _page_shell(f"名單詳情 - {lead.name}", body)


@router.post("/admin/leads/{lead_id}/assign")
def school_platform_admin_lead_assign_submit(
    lead_id: UUID,
    staff_id: str = Form(...),
):
    lead_workflow_service.assign_lead(lead_id, LeadAssignmentRequest(staff_id=UUID(staff_id)))
    return RedirectResponse(url=f"/school-platform/admin/leads/{lead_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/leads/{lead_id}/status")
def school_platform_admin_lead_status_submit(
    lead_id: UUID,
    status_value: str = Form(...),
    next_follow_up_at: str = Form(default=""),
    note: str = Form(default=""),
):
    next_follow_up = datetime.fromisoformat(next_follow_up_at) if next_follow_up_at else None
    payload = LeadStatusChangeRequest(status=status_value, next_follow_up_at=next_follow_up, note=note or None)
    lead_workflow_service.change_status(lead_id, payload)
    return RedirectResponse(url=f"/school-platform/admin/leads/{lead_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/leads/{lead_id}/logs")
def school_platform_admin_lead_log_submit(
    lead_id: UUID,
    staff_name: str = Form(...),
    contact_method: str = Form(...),
    content: str = Form(...),
    next_action: str = Form(default=""),
):
    lead_workflow_service.add_log(lead_id, staff_name, contact_method, content, next_action or None)
    return RedirectResponse(url=f"/school-platform/admin/leads/{lead_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/classes", response_class=HTMLResponse)
def school_platform_admin_classes_page() -> str:
    classes = catalog_service.open_classes()
    course_options = "".join(
        f"<option value='{escape(item.slug)}'>{escape(item.name)} ({escape(item.slug)})</option>"
        for item in catalog_service.list_courses()
    )
    class_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.course_slug)}</div>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>老師：{escape(item.teacher_name)} / 地點：{escape(item.location_label)}</p>"
        f"<p>時間：{escape(item.weekday)} {escape(item.start_time.strftime('%H:%M'))}-{escape(item.end_time.strftime('%H:%M'))}</p>"
        f"<div class='meta'>"
        f"<span class='chip'>名額 {item.enrolled_count}/{item.capacity}</span>"
        f"<span class='chip'>{escape(item.start_date.isoformat())}</span>"
        f"<span class='chip'>{escape(item.status)}</span>"
        "</div>"
        f"<div class='actions'><a class='btn' href='/school-platform/admin/classes/{item.id}/edit'>編輯班級</a></div>"
        "</article>"
        for item in classes
    ) or "<article class='card'><h3>目前沒有班級</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Classes Management</div>
        <h1>班級管理</h1>
        <p>這裡先把目前所有開放班級整理成管理頁，下一段會接課程管理、教師排課與班級詳頁。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/classes">查看 classes JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{class_cards}</div>
      </section>
      <section class="section">
        <h2>操作區塊</h2>
        <div class="grid two">
          <article class="card">
            <h3>新增班級</h3>
            <form class="stack" method="post" action="/school-platform/admin/classes/create">
              <label class="field">課程
                <select name="course_slug">{course_options}</select>
              </label>
              <label class="field">班級名稱
                <input type="text" name="name" placeholder="例如：7 月晚間班" />
              </label>
              <label class="field">教師名稱
                <input type="text" name="teacher_name" value="Aki Mori" />
              </label>
              <label class="field">開始日期
                <input type="date" name="start_date" />
              </label>
              <label class="field">結束日期
                <input type="date" name="end_date" />
              </label>
              <label class="field">星期
                <input type="text" name="weekday" value="Tue / Thu" />
              </label>
              <label class="field">開始時間
                <input type="time" name="start_time" value="19:30" />
              </label>
              <label class="field">結束時間
                <input type="time" name="end_time" value="21:00" />
              </label>
              <label class="field">容量
                <input type="number" name="capacity" value="16" />
              </label>
              <label class="field">上課地點
                <input type="text" name="location_label" value="Zoom Live" />
              </label>
              <button class="btn" type="submit">建立班級</button>
            </form>
          </article>
          <article class="card">
            <h3>更新班級</h3>
            <p><code>PATCH /school-platform/api/classes/{'{class_id}'}</code></p>
            <p>下一段會把這裡接成真正表單，直接在後台改班級資料。</p>
          </article>
        </div>
      </section>
    """
    return _page_shell("班級管理", body)


@router.post("/admin/classes/create")
def school_platform_admin_class_create_submit(
    course_slug: str = Form(...),
    name: str = Form(...),
    teacher_name: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    weekday: str = Form(...),
    start_time_value: str = Form(..., alias="start_time"),
    end_time_value: str = Form(..., alias="end_time"),
    capacity: int = Form(...),
    location_label: str = Form(...),
):
    payload = ClassUpsertRequest(
        course_slug=course_slug,
        name=name,
        teacher_name=teacher_name,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        weekday=weekday,
        start_time=time.fromisoformat(start_time_value),
        end_time=time.fromisoformat(end_time_value),
        capacity=capacity,
        location_label=location_label,
        status="open",
    )
    curriculum_admin_service.create_class(payload)
    return RedirectResponse(url="/school-platform/admin/classes", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/classes/{class_id}/edit", response_class=HTMLResponse)
def school_platform_admin_class_edit_page(class_id: UUID) -> str:
    class_item = next((item for item in catalog_service.open_classes() if item.id == class_id), None)
    if class_item is None:
        raise HTTPException(status_code=404, detail="Class not found")
    course_options = "".join(
        f"<option value='{escape(item.slug)}' {'selected' if item.slug == class_item.course_slug else ''}>{escape(item.name)} ({escape(item.slug)})</option>"
        for item in catalog_service.list_courses()
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">Class Editor</div>
        <h1>編輯班級</h1>
        <p>這裡可以直接修改班級資料並寫回目前的 store。</p>
      </section>
      <section class="section">
        <article class="card">
          <form class="stack" method="post" action="/school-platform/admin/classes/{class_item.id}/edit">
            <label class="field">課程
              <select name="course_slug">{course_options}</select>
            </label>
            <label class="field">班級名稱
              <input type="text" name="name" value="{escape(class_item.name)}" />
            </label>
            <label class="field">教師名稱
              <input type="text" name="teacher_name" value="{escape(class_item.teacher_name)}" />
            </label>
            <label class="field">開始日期
              <input type="date" name="start_date" value="{class_item.start_date.isoformat()}" />
            </label>
            <label class="field">結束日期
              <input type="date" name="end_date" value="{class_item.end_date.isoformat()}" />
            </label>
            <label class="field">星期
              <input type="text" name="weekday" value="{escape(class_item.weekday)}" />
            </label>
            <label class="field">開始時間
              <input type="time" name="start_time" value="{class_item.start_time.strftime('%H:%M')}" />
            </label>
            <label class="field">結束時間
              <input type="time" name="end_time" value="{class_item.end_time.strftime('%H:%M')}" />
            </label>
            <label class="field">容量
              <input type="number" name="capacity" value="{class_item.capacity}" />
            </label>
            <label class="field">地點
              <input type="text" name="location_label" value="{escape(class_item.location_label)}" />
            </label>
            <button class="btn" type="submit">儲存班級</button>
          </form>
        </article>
      </section>
    """
    return _page_shell("編輯班級", body)


@router.post("/admin/classes/{class_id}/edit")
def school_platform_admin_class_edit_submit(
    class_id: UUID,
    course_slug: str = Form(...),
    name: str = Form(...),
    teacher_name: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    weekday: str = Form(...),
    start_time_value: str = Form(..., alias="start_time"),
    end_time_value: str = Form(..., alias="end_time"),
    capacity: int = Form(...),
    location_label: str = Form(...),
):
    payload = ClassUpsertRequest(
        course_slug=course_slug,
        name=name,
        teacher_name=teacher_name,
        start_date=date.fromisoformat(start_date),
        end_date=date.fromisoformat(end_date),
        weekday=weekday,
        start_time=time.fromisoformat(start_time_value),
        end_time=time.fromisoformat(end_time_value),
        capacity=capacity,
        location_label=location_label,
        status="open",
    )
    curriculum_admin_service.update_class(class_id, payload)
    return RedirectResponse(url="/school-platform/admin/classes", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/courses", response_class=HTMLResponse)
def school_platform_admin_courses_page() -> str:
    courses = catalog_service.list_courses()
    course_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.course_type)} / {escape(item.level)}</div>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>{escape(item.short_description)}</p>"
        f"<div class='meta'><span class='chip'>{_format_jpy(item.price)}</span><span class='chip'>{escape(item.delivery_mode)}</span></div>"
        f"<div class='actions'><a class='btn' href='/school-platform/admin/courses/{escape(item.slug)}/edit'>編輯課程</a></div>"
        "</article>"
        for item in courses
    ) or "<article class='card'><h3>目前沒有課程</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Courses Management</div>
        <h1>課程管理</h1>
        <p>這裡先把課程資料集中在管理端查看，接下來會把新增與修改課程表單掛上來。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/courses">查看 courses JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{course_cards}</div>
      </section>
      <section class="section">
        <h2>操作區塊</h2>
        <div class="grid two">
          <article class="card">
            <h3>新增課程</h3>
            <form class="stack" method="post" action="/school-platform/admin/courses/create">
              <label class="field">slug
                <input type="text" name="slug" placeholder="例如：japan-life-intensive" />
              </label>
              <label class="field">課程名稱
                <input type="text" name="name" placeholder="例如：日本生活日語密集班" />
              </label>
              <label class="field">課程類型
                <input type="text" name="course_type" value="生活日語" />
              </label>
              <label class="field">程度
                <input type="text" name="level" value="N5" />
              </label>
              <label class="field">授課模式
                <input type="text" name="delivery_mode" value="online" />
              </label>
              <label class="field">價格（日圓）
                <input type="number" name="price" value="10800" />
              </label>
              <label class="field">短描述
                <textarea name="short_description" placeholder="輸入課程摘要"></textarea>
              </label>
              <label class="field">課程目標
                <textarea name="objectives" placeholder="每行一個目標"></textarea>
              </label>
              <label class="field">課程亮點
                <textarea name="highlights" placeholder="每行一個亮點"></textarea>
              </label>
              <label class="field">章節規劃
                <textarea name="modules" placeholder="每行一個章節"></textarea>
              </label>
              <label class="field">教師名單
                <textarea name="teacher_names" placeholder="每行一位教師"></textarea>
              </label>
              <button class="btn" type="submit">建立課程</button>
            </form>
          </article>
          <article class="card">
            <h3>更新課程</h3>
            <p><code>PATCH /school-platform/api/courses/{'{slug}'}</code></p>
            <p>下一段會接成後台表單，直接在頁面上維護課程。</p>
          </article>
        </div>
      </section>
    """
    return _page_shell("課程管理", body)


@router.post("/admin/courses/create")
def school_platform_admin_course_create_submit(
    slug: str = Form(...),
    name: str = Form(...),
    course_type: str = Form(...),
    level: str = Form(...),
    delivery_mode: str = Form(...),
    price: float = Form(...),
    short_description: str = Form(...),
    objectives: str = Form(default=""),
    highlights: str = Form(default=""),
    modules: str = Form(default=""),
    teacher_names: str = Form(default=""),
):
    payload = CourseUpsertRequest(
        slug=slug,
        name=name,
        course_type=course_type,
        level=level,
        delivery_mode=delivery_mode,
        price=price,
        short_description=short_description,
        objectives=[item.strip() for item in objectives.splitlines() if item.strip()],
        highlights=[item.strip() for item in highlights.splitlines() if item.strip()],
        modules=[item.strip() for item in modules.splitlines() if item.strip()],
        teacher_names=[item.strip() for item in teacher_names.splitlines() if item.strip()],
    )
    curriculum_admin_service.create_course(payload)
    return RedirectResponse(url="/school-platform/admin/courses", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/courses/{slug}/edit", response_class=HTMLResponse)
def school_platform_admin_course_edit_page(slug: str) -> str:
    try:
        course = catalog_service.get_course(slug)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc
    body = f"""
      <section class="hero">
        <div class="eyebrow">Course Editor</div>
        <h1>編輯課程</h1>
        <p>這裡可以直接修改課程資料並寫回目前的 store。</p>
      </section>
      <section class="section">
        <article class="card">
          <form class="stack" method="post" action="/school-platform/admin/courses/{escape(course.slug)}/edit">
            <label class="field">slug
              <input type="text" name="slug" value="{escape(course.slug)}" />
            </label>
            <label class="field">課程名稱
              <input type="text" name="name" value="{escape(course.name)}" />
            </label>
            <label class="field">課程類型
              <input type="text" name="course_type" value="{escape(course.course_type)}" />
            </label>
            <label class="field">程度
              <input type="text" name="level" value="{escape(course.level)}" />
            </label>
            <label class="field">授課模式
              <input type="text" name="delivery_mode" value="{escape(course.delivery_mode)}" />
            </label>
            <label class="field">價格（日圓）
              <input type="number" name="price" value="{course.price}" />
            </label>
            <label class="field">短描述
              <textarea name="short_description">{escape(course.short_description)}</textarea>
            </label>
            <label class="field">課程目標
              <textarea name="objectives">{escape(chr(10).join(course.objectives))}</textarea>
            </label>
            <label class="field">課程亮點
              <textarea name="highlights">{escape(chr(10).join(course.highlights))}</textarea>
            </label>
            <label class="field">章節規劃
              <textarea name="modules">{escape(chr(10).join(course.modules))}</textarea>
            </label>
            <label class="field">教師名單
              <textarea name="teacher_names">{escape(chr(10).join(course.teacher_names))}</textarea>
            </label>
            <button class="btn" type="submit">儲存課程</button>
          </form>
        </article>
      </section>
    """
    return _page_shell("編輯課程", body)


@router.post("/admin/courses/{slug}/edit")
def school_platform_admin_course_edit_submit(
    slug: str,
    slug_value: str = Form(..., alias="slug"),
    name: str = Form(...),
    course_type: str = Form(...),
    level: str = Form(...),
    delivery_mode: str = Form(...),
    price: float = Form(...),
    short_description: str = Form(...),
    objectives: str = Form(default=""),
    highlights: str = Form(default=""),
    modules: str = Form(default=""),
    teacher_names: str = Form(default=""),
):
    payload = CourseUpsertRequest(
        slug=slug_value,
        name=name,
        course_type=course_type,
        level=level,
        delivery_mode=delivery_mode,
        price=price,
        short_description=short_description,
        objectives=[item.strip() for item in objectives.splitlines() if item.strip()],
        highlights=[item.strip() for item in highlights.splitlines() if item.strip()],
        modules=[item.strip() for item in modules.splitlines() if item.strip()],
        teacher_names=[item.strip() for item in teacher_names.splitlines() if item.strip()],
    )
    updated = curriculum_admin_service.update_course(slug, payload)
    return RedirectResponse(url=f"/school-platform/admin/courses/{updated.slug}/edit", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/teachers", response_class=HTMLResponse)
def school_platform_admin_teachers_page() -> str:
    teachers = admissions_service.list_staff(role="teacher")
    teacher_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.department)}</div>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>職稱：{escape(item.title)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.role)}</span></div>"
        f"<div class='actions'><a class='btn' href='/school-platform/teacher-portal?teacher_name={escape(item.name)}'>打開教師工作台</a></div>"
        "</article>"
        for item in teachers
    ) or "<article class='card'><h3>目前沒有教師資料</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Teachers Management</div>
        <h1>教師管理</h1>
        <p>這裡已經能直接打開教師工作台，查看授課班級、待評分作業與測驗。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/staff">查看 staff JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{teacher_cards}</div>
      </section>
    """
    return _page_shell("教師管理", body)


@router.get("/teacher-portal", response_class=HTMLResponse)
def school_platform_teacher_portal_page(teacher_name: str = Query(...)) -> str:
    dashboard = teacher_workspace_service.dashboard(teacher_name)
    classes = dashboard["classes"]
    assignments = dashboard["assignments"]
    exams = dashboard["exams"]
    session_records = dashboard["session_records"]
    pending_assignment_reviews = dashboard["pending_assignment_reviews"]
    pending_exam_reviews = dashboard["pending_exam_reviews"]
    summary = dashboard["summary"]
    class_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.course_slug)}</div>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>{escape(item.weekday)} / {escape(item.start_time.strftime('%H:%M'))}-{escape(item.end_time.strftime('%H:%M'))}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.location_label)}</span><span class='chip'>{item.enrolled_count}/{item.capacity}</span></div>"
        f"<div class='actions'><a class='btn' href='/school-platform/teacher/classes/{item.id}?teacher_name={escape(teacher_name)}'>查看班級詳情</a></div>"
        "</article>"
        for item in classes
    ) or "<article class='card'><h3>目前沒有授課班級</h3></article>"
    assignment_map = {item.id: item for item in assignments}
    exam_map = {item.id: item for item in exams}
    assignment_review_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>作業待評分</div>"
        f"<h3>{escape(assignment_map[item.assignment_id].title) if item.assignment_id in assignment_map else '未知作業'}</h3>"
        f"<p>{escape(item.content)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.submitted_at.isoformat())}</span><span class='chip'>{escape(item.status)}</span></div>"
        f"<form class='stack' method='post' action='/school-platform/teacher/assignment-submissions/{item.id}/grade'>"
        f"<input type='hidden' name='teacher_name' value='{escape(teacher_name)}' />"
        "<label class='field'>分數<input type='number' name='score' step='1' value='85' /></label>"
        "<label class='field'>回饋<textarea name='feedback' placeholder='輸入老師回饋'></textarea></label>"
        f"<input type='hidden' name='graded_by' value='{escape(teacher_name)}' />"
        "<button class='btn' type='submit'>送出評分</button>"
        "</form>"
        "</article>"
        for item in pending_assignment_reviews[:8]
    ) or "<article class='card'><h3>目前沒有待評分作業</h3></article>"
    exam_review_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>測驗待評分</div>"
        f"<h3>{escape(exam_map[item.exam_id].title) if item.exam_id in exam_map else '未知測驗'}</h3>"
        f"<p>{escape(item.content)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.submitted_at.isoformat())}</span><span class='chip'>{escape(item.status)}</span></div>"
        f"<form class='stack' method='post' action='/school-platform/teacher/exam-submissions/{item.id}/grade'>"
        f"<input type='hidden' name='teacher_name' value='{escape(teacher_name)}' />"
        "<label class='field'>分數<input type='number' name='score' step='1' value='88' /></label>"
        "<label class='field'>回饋<textarea name='feedback' placeholder='輸入老師回饋'></textarea></label>"
        f"<input type='hidden' name='graded_by' value='{escape(teacher_name)}' />"
        "<button class='btn' type='submit'>送出評分</button>"
        "</form>"
        "</article>"
        for item in pending_exam_reviews[:8]
    ) or "<article class='card'><h3>目前沒有待評分測驗</h3></article>"
    session_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.class_date.isoformat())} / {escape(item.approval_status)}</div>"
        f"<h3>{escape(next((class_item.name for class_item in classes if class_item.id == item.class_id), '未知班級'))}</h3>"
        f"<p>{escape(item.summary)}</p>"
        f"<p>下次課堂焦點：{escape(item.next_class_focus or '尚未填寫')}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.teacher_name)}</span><span class='chip'>{escape(item.reviewed_by or '待主管處理')}</span></div>"
        "</article>"
        for item in session_records[:6]
    ) or "<article class='card'><h3>目前還沒有課後紀錄</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Teacher Workspace</div>
        <h1>{escape(teacher_name)} 教師工作台</h1>
        <p>這裡集中顯示授課班級、待評分作業、待評分測驗，方便教師直接處理教學任務。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin/teachers">回教師管理</a>
          <a class="btn alt" href="/school-platform/admin/teaching">回教務管理</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">授課班級</div><div class="value">{summary['class_count']}</div></div>
          <div class="stat"><div class="label">作業數</div><div class="value">{summary['assignment_count']}</div></div>
          <div class="stat"><div class="label">測驗數</div><div class="value">{summary['exam_count']}</div></div>
          <div class="stat"><div class="label">待評分</div><div class="value">{summary['pending_reviews']}</div></div>
          <div class="stat"><div class="label">課後紀錄</div><div class="value">{summary['session_record_count']}</div></div>
          <div class="stat"><div class="label">待審核課後紀錄</div><div class="value">{summary['pending_session_reviews']}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>授課班級</h2>
        <div class="grid two">{class_cards}</div>
      </section>
      <section class="section">
        <h2>待評分作業</h2>
        <div class="grid two">{assignment_review_cards}</div>
      </section>
      <section class="section">
        <h2>待評分測驗</h2>
        <div class="grid two">{exam_review_cards}</div>
      </section>
      <section class="section">
        <h2>最近課後紀錄</h2>
        <div class="grid two">{session_cards}</div>
      </section>
    """
    return _page_shell(f"{teacher_name} 教師工作台", body)


@router.get("/teacher/classes/{class_id}", response_class=HTMLResponse)
def school_platform_teacher_class_detail_page(class_id: UUID, teacher_name: str = Query(...)) -> str:
    try:
        snapshot = teacher_workspace_service.class_snapshot(teacher_name, class_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Teacher class not found") from exc

    class_item = snapshot.class_item
    summary = snapshot.summary
    class_detail_return_to = f"/school-platform/teacher/classes/{class_item.id}?{urlencode({'teacher_name': teacher_name})}"
    student_map = {item.student_id: item for item in snapshot.roster}
    assignment_map = {item.id: item for item in snapshot.assignments}
    exam_map = {item.id: item for item in snapshot.exams}
    student_options = "".join(
        f"<option value='{escape(item.email)}'>{escape(item.chinese_name)} / {escape(item.email)}</option>"
        for item in snapshot.roster
    )
    roster_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.risk_level)} / {escape(item.payment_status)}</div>"
            f"<h3>{escape(item.chinese_name)}</h3>"
            f"<p>{escape(item.email)}</p>"
            f"<div class='meta'><span class='chip'>作業 {item.assignment_submitted}/{item.assignment_total}</span><span class='chip'>測驗 {item.exam_submitted}/{item.exam_total}</span></div>"
            f"<div class='meta'><span class='chip'>出席率 {item.attendance_rate:g}%</span><span class='chip'>最近出缺勤 {escape(item.latest_attendance_status or '尚無紀錄')}</span></div>"
            "</article>"
        )
        for item in snapshot.roster
    ) or "<article class='card'><h3>目前沒有學員資料</h3></article>"
    assignment_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.created_by)}</div>"
            f"<h3>{escape(item.title)}</h3>"
            f"<p>{escape(item.content)}</p>"
            f"<div class='meta'><span class='chip'>{escape(item.due_at.isoformat())}</span></div>"
            "</article>"
        )
        for item in snapshot.assignments[:6]
    ) or "<article class='card'><h3>目前沒有作業</h3></article>"
    exam_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.exam_type)}</div>"
            f"<h3>{escape(item.title)}</h3>"
            f"<p>{escape(item.instructions)}</p>"
            f"<div class='meta'><span class='chip'>{escape(item.due_at.isoformat())}</span><span class='chip'>總分 {item.total_score:g}</span></div>"
            "</article>"
        )
        for item in snapshot.exams[:6]
    ) or "<article class='card'><h3>目前沒有測驗</h3></article>"
    attendance_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.status)}</div>"
            f"<h3>{escape(item.class_date.isoformat())}</h3>"
            f"<p>{escape(item.marked_by)}</p>"
            f"<p>{escape(item.note or '無備註')}</p>"
            "</article>"
        )
        for item in snapshot.attendance_records[:8]
    ) or "<article class='card'><h3>目前沒有出缺勤紀錄</h3></article>"
    session_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.class_date.isoformat())} / {escape(item.approval_status)}</div>"
            f"<h3>{escape(item.next_class_focus or '尚未設定下次課堂焦點')}</h3>"
            f"<p>{escape(item.summary)}</p>"
            f"<p>教材：{escape(item.materials_link or '尚未提供')}</p>"
            f"<p>作業：{escape(item.homework_summary or '尚未填寫')}</p>"
            f"<p>高風險學員：{escape(' / '.join(item.student_risk_notes) or '無')}</p>"
            f"<p>主管回覆：{escape(item.review_note or '尚未回覆')}</p>"
            f"<div class='meta'><span class='chip'>{escape(item.reviewed_by or '待主管審核')}</span></div>"
            "</article>"
        )
        for item in snapshot.session_records[:6]
    ) or "<article class='card'><h3>目前還沒有課後紀錄</h3></article>"
    pending_assignment_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(student_map[item.student_id].chinese_name) if item.student_id in student_map else '未知學員'} / 作業待批改</div>"
            f"<h3>{escape(assignment_map[item.assignment_id].title) if item.assignment_id in assignment_map else '未知作業'}</h3>"
            f"<p>{escape(item.content)}</p>"
            f"<div class='meta'><span class='chip'>{escape(student_map[item.student_id].email) if item.student_id in student_map else '未知 Email'}</span><span class='chip'>{escape(item.submitted_at.isoformat())}</span></div>"
            f"<form class='stack' method='post' action='/school-platform/teacher/assignment-submissions/{item.id}/grade'>"
            f"<input type='hidden' name='teacher_name' value='{escape(teacher_name)}' />"
            f"<input type='hidden' name='graded_by' value='{escape(teacher_name)}' />"
            f"<input type='hidden' name='return_to' value='{escape(class_detail_return_to)}' />"
            "<label class='field'>分數<input type='number' name='score' min='0' max='100' step='1' value='85' /></label>"
            "<label class='field'>回饋<textarea name='feedback' placeholder='輸入這位學員的作業評語'></textarea></label>"
            "<button class='btn' type='submit'>送出作業評分</button>"
            "</form>"
            "</article>"
        )
        for item in sorted(snapshot.assignment_submissions, key=lambda record: record.submitted_at, reverse=True)
        if item.status != "graded"
    ) or "<article class='card'><h3>目前沒有待批改作業</h3></article>"
    pending_exam_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(student_map[item.student_id].chinese_name) if item.student_id in student_map else '未知學員'} / 測驗待批改</div>"
            f"<h3>{escape(exam_map[item.exam_id].title) if item.exam_id in exam_map else '未知測驗'}</h3>"
            f"<p>{escape(item.content)}</p>"
            f"<div class='meta'><span class='chip'>{escape(student_map[item.student_id].email) if item.student_id in student_map else '未知 Email'}</span><span class='chip'>{escape(item.submitted_at.isoformat())}</span></div>"
            f"<form class='stack' method='post' action='/school-platform/teacher/exam-submissions/{item.id}/grade'>"
            f"<input type='hidden' name='teacher_name' value='{escape(teacher_name)}' />"
            f"<input type='hidden' name='graded_by' value='{escape(teacher_name)}' />"
            f"<input type='hidden' name='return_to' value='{escape(class_detail_return_to)}' />"
            "<label class='field'>分數<input type='number' name='score' min='0' max='100' step='1' value='88' /></label>"
            "<label class='field'>回饋<textarea name='feedback' placeholder='輸入這位學員的測驗評語'></textarea></label>"
            "<button class='btn' type='submit'>送出測驗評分</button>"
            "</form>"
            "</article>"
        )
        for item in sorted(snapshot.exam_submissions, key=lambda record: record.submitted_at, reverse=True)
        if item.status != "graded"
    ) or "<article class='card'><h3>目前沒有待批改測驗</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Teacher Class Detail</div>
        <h1>班級教學詳情</h1>
        <p>{escape(class_item.name)} / {escape(class_item.course_slug)} / {escape(class_item.weekday)} {escape(class_item.start_time.strftime('%H:%M'))}-{escape(class_item.end_time.strftime('%H:%M'))}</p>
        <div class="actions">
          <a class="btn" href="/school-platform/teacher-portal?teacher_name={escape(teacher_name)}">回教師工作台</a>
          <a class="btn alt" href="/school-platform/api/teacher/classes/{class_item.id}?teacher_name={escape(teacher_name)}">查看班級 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">學員數</div><div class="value">{summary.total_students}</div></div>
          <div class="stat"><div class="label">高風險</div><div class="value">{summary.high_risk_students}</div></div>
          <div class="stat"><div class="label">中風險</div><div class="value">{summary.medium_risk_students}</div></div>
          <div class="stat"><div class="label">待補作業</div><div class="value">{summary.pending_assignments}</div></div>
          <div class="stat"><div class="label">待補測驗</div><div class="value">{summary.pending_exams}</div></div>
          <div class="stat"><div class="label">出缺勤紀錄</div><div class="value">{summary.attendance_records}</div></div>
          <div class="stat"><div class="label">課後紀錄</div><div class="value">{summary.session_records}</div></div>
          <div class="stat"><div class="label">待審核</div><div class="value">{summary.pending_session_reviews}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>學員名單</h2>
        <div class="grid two">{roster_cards}</div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>快速點名</h2>
            <form class="stack" method="post" action="/school-platform/teacher/classes/{class_item.id}/attendance">
              <input type="hidden" name="teacher_name" value="{escape(teacher_name)}" />
              <label class="field">學員
                <select name="student_email">{student_options}</select>
              </label>
              <label class="field">上課日期
                <input type="date" name="class_date_value" value="{date.today().isoformat()}" />
              </label>
              <label class="field">出席狀態
                <select name="status_value">
                  <option value="present">present</option>
                  <option value="late">late</option>
                  <option value="leave">leave</option>
                  <option value="absent">absent</option>
                </select>
              </label>
              <label class="field">備註
                <textarea name="note" placeholder="例如：遲到 10 分鐘、請假已提前通知"></textarea>
              </label>
              <button class="btn" type="submit">送出點名</button>
            </form>
          </article>
          <article class="card">
            <h2>班級執行摘要</h2>
            <p>目前學員數：<code>{summary.total_students}</code></p>
            <p>待補作業：<code>{summary.pending_assignments}</code></p>
            <p>待補測驗：<code>{summary.pending_exams}</code></p>
            <p>待審核課後紀錄：<code>{summary.pending_session_reviews}</code></p>
            <p>若班級內已經收到作業或測驗提交，可直接在下方完成批改，不需要回上一層工作台。</p>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>新增 / 更新課後紀錄</h2>
            <form class="stack" method="post" action="/school-platform/teacher/classes/{class_item.id}/session-records">
              <input type="hidden" name="teacher_name" value="{escape(teacher_name)}" />
              <input type="hidden" name="return_to" value="{escape(class_detail_return_to)}" />
              <label class="field">上課日期
                <input type="date" name="class_date_value" value="{date.today().isoformat()}" />
              </label>
              <label class="field">本堂摘要
                <textarea name="summary_text" placeholder="例如：完成租屋問答、藥局購藥句型、生活敬語練習"></textarea>
              </label>
              <label class="field">教材 / 講義連結
                <input type="url" name="materials_link" placeholder="https://..." />
              </label>
              <label class="field">課後作業
                <textarea name="homework_summary" placeholder="例如：錄一段 60 秒租屋自我介紹"></textarea>
              </label>
              <label class="field">下次課堂焦點
                <input type="text" name="next_class_focus" placeholder="例如：病院掛號與症狀描述" />
              </label>
              <label class="field">高風險學員備註
                <textarea name="student_risk_notes" placeholder="每行一位，例如：王小明：連續兩週未交作業"></textarea>
              </label>
              <label class="field">送出方式
                <select name="approval_status_value">
                  <option value="submitted">submitted</option>
                  <option value="draft">draft</option>
                </select>
              </label>
              <button class="btn" type="submit">儲存課後紀錄</button>
            </form>
          </article>
          <article class="card">
            <h2>最近課後紀錄</h2>
            <div class="list">{session_cards}</div>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>待批改作業</h2>
        <div class="grid two">{pending_assignment_cards}</div>
      </section>
      <section class="section">
        <h2>待批改測驗</h2>
        <div class="grid two">{pending_exam_cards}</div>
      </section>
      <section class="section">
        <div class="grid two">
          <article>
            <h2>作業</h2>
            <div class="list">{assignment_cards}</div>
          </article>
          <article>
            <h2>測驗</h2>
            <div class="list">{exam_cards}</div>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>最近出缺勤</h2>
        <div class="grid two">{attendance_cards}</div>
      </section>
    """
    return _page_shell(f"{class_item.name} 班級教學詳情", body)


@router.get("/admin/recruiting", response_class=HTMLResponse)
def school_platform_admin_recruiting_page() -> str:
    summary = recruiting_service.recruiting_summary()
    jobs = recruiting_service.list_jobs()
    applicants = recruiting_service.list_applicants()
    interviews = recruiting_service.list_interviews()
    job_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.department)} / {escape(item.employment_type)}</div>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>{escape(item.summary)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.salary_range)}</span><span class='chip'>{escape(item.status)}</span></div>"
        "</article>"
        for item in jobs
    ) or "<article class='card'><h3>目前沒有職缺</h3></article>"
    applicant_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(str(item.ai_match_score))}</div>"
        f"<h3>{escape(item.name)}</h3>"
        f"<p>{escape(item.email)}</p>"
        f"<p>狀態：{escape(item.interview_status)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.created_at.isoformat())}</span></div>"
        f"<div class='actions'><a class='btn' href='/school-platform/admin/recruiting/applicants/{item.id}'>查看應徵者詳情</a></div>"
        "</article>"
        for item in applicants[:6]
    ) or "<article class='card'><h3>目前沒有應徵者</h3></article>"
    interview_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.status)}</div>"
        f"<h3>{escape(item.interviewer_name)}</h3>"
        f"<p>{escape(item.interview_at.isoformat())}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.format)}</span></div>"
        "</article>"
        for item in interviews[:6]
    ) or "<article class='card'><h3>目前沒有面試</h3></article>"
    applicant_options = "".join(
        f"<option value='{item.id}'>{escape(item.name)} / {escape(item.email)}</option>"
        for item in applicants
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">Recruiting Admin</div>
        <h1>招聘管理</h1>
        <p>這裡把公開職缺、應徵者、面試排程接進同一個後台，開始形成完整營運平台的一部分。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/jobs">打開公開招聘頁</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">開放職缺</div><div class="value">{summary['open_jobs']}</div></div>
          <div class="stat"><div class="label">應徵者</div><div class="value">{summary['applicants']}</div></div>
          <div class="stat"><div class="label">已排面試</div><div class="value">{summary['scheduled_interviews']}</div></div>
          <div class="stat"><div class="label">進行中 onboarding</div><div class="value">{summary['active_onboarding']}</div></div>
          <div class="stat"><div class="label">試用期追蹤</div><div class="value">{summary['active_probation']}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>新增職缺</h2>
            <form class="stack" method="post" action="/school-platform/admin/recruiting/jobs/create">
              <label class="field">職缺名稱<input type="text" name="title" /></label>
              <label class="field">部門<input type="text" name="department" value="Teaching" /></label>
              <label class="field">聘用形式<input type="text" name="employment_type" value="part_time" /></label>
              <label class="field">地點<input type="text" name="location_label" value="Taipei / Remote" /></label>
              <label class="field">薪資範圍<input type="text" name="salary_range" value="JPY 200,000 - 320,000 / month" /></label>
              <label class="field">摘要<textarea name="summary"></textarea></label>
              <label class="field">需求條件<textarea name="requirements"></textarea></label>
              <button class="btn" type="submit">建立職缺</button>
            </form>
          </article>
          <article class="card">
            <h2>安排面試</h2>
            <form class="stack" method="post" action="/school-platform/admin/recruiting/interviews/create">
              <label class="field">應徵者
                <select name="applicant_id">{applicant_options}</select>
              </label>
              <label class="field">面試時間
                <input type="datetime-local" name="interview_at" />
              </label>
              <label class="field">面試官<input type="text" name="interviewer_name" value="Yuki Wang" /></label>
              <label class="field">形式
                <select name="format">
                  <option value="google_meet">google_meet</option>
                  <option value="onsite">onsite</option>
                  <option value="phone">phone</option>
                </select>
              </label>
              <button class="btn" type="submit">安排面試</button>
            </form>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>職缺</h2>
        <div class="grid two">{job_cards}</div>
      </section>
      <section class="section">
        <h2>應徵者</h2>
        <div class="grid two">{applicant_cards}</div>
      </section>
      <section class="section">
        <h2>面試排程</h2>
        <div class="grid two">{interview_cards}</div>
      </section>
    """
    return _page_shell("招聘管理", body)


@router.get("/admin/recruiting/applicants/{applicant_id}", response_class=HTMLResponse)
def school_platform_admin_applicant_detail_page(applicant_id: UUID) -> str:
    try:
        snapshot = recruiting_service.applicant_detail(applicant_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Applicant not found") from exc

    applicant = snapshot.applicant
    position = snapshot.position
    evaluation = snapshot.evaluation
    applicant_note = escape(applicant.note or "未填寫").replace("\n", "<br />")
    applicant_status_options = "".join(
        f"<option value='{value}' {'selected' if applicant.interview_status == value else ''}>{value}</option>"
        for value in ["reviewing", "scheduled", "interviewing", "shortlisted", "offer_sent", "hired", "rejected", "talent_pool"]
    )
    interview_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.status)} / {escape(item.format)}</div>"
            f"<h3>{escape(item.interviewer_name)}</h3>"
            f"<p>{escape(item.interview_at.isoformat())}</p>"
            f"<p>{escape(item.feedback or '尚未填寫回饋').replace(chr(10), '<br />')}</p>"
            f"<form class='stack' method='post' action='/school-platform/admin/recruiting/interviews/{item.id}/review'>"
            "<label class='field'>面試狀態"
            "<select name='interview_status_value'>"
            + "".join(
                f"<option value='{value}' {'selected' if item.status == value else ''}>{value}</option>"
                for value in ["scheduled", "completed", "shortlisted", "offer_sent", "hired", "rejected", "no_show", "cancelled"]
            )
            + "</select></label>"
            "<label class='field'>案件階段"
            f"<select name='applicant_status'>{applicant_status_options}</select>"
            "</label>"
            "<label class='field'>面試回饋"
            f"<textarea name='feedback' placeholder='輸入面試觀察與建議'>{escape(item.feedback or '')}</textarea>"
            "</label>"
            "<label class='field'>HR 備註"
            "<textarea name='note' placeholder='例如：可進第二輪試教，或先放人才庫觀察'></textarea>"
            "</label>"
            "<button class='btn' type='submit'>儲存面試結論</button>"
            "</form>"
            "</article>"
        )
        for item in snapshot.interviews
    ) or "<article class='card'><h3>目前沒有面試紀錄</h3></article>"
    strength_items = "".join(f"<li>{escape(item)}</li>" for item in evaluation.strengths)
    concern_items = "".join(f"<li>{escape(item)}</li>" for item in evaluation.concerns) or "<li>目前沒有明顯風險</li>"
    question_items = "".join(f"<li>{escape(item)}</li>" for item in evaluation.suggested_questions)
    onboarding = snapshot.onboarding
    onboarding_stage_options = "".join(
        f"<option value='{value}' {'selected' if onboarding and onboarding.stage == value else ''}>{value}</option>"
        for value in ["preboarding", "docs_pending", "orientation_scheduled", "active", "completed", "cancelled"]
    )
    probation_status_options = "".join(
        f"<option value='{value}' {'selected' if onboarding and onboarding.probation_status == value else ''}>{value}</option>"
        for value in ["not_started", "in_progress", "passed", "extended", "ended"]
    )
    onboarding_checklist_text = "\n".join(onboarding.checklist_items) if onboarding and onboarding.checklist_items else ""
    body = f"""
      <section class="hero">
        <div class="eyebrow">Applicant Detail</div>
        <h1>應徵者詳情</h1>
        <p>這裡把職缺資訊、AI 配對評估與面試排程集中在同一頁，讓 HR 可直接往下處理。</p>
        <div class="meta">
          <span class="chip">{escape(applicant.name)}</span>
          <span class="chip">{escape(position.title)}</span>
          <span class="chip">AI 配對 {evaluation.ai_match_score:g}</span>
          <span class="chip">{escape(applicant.interview_status)}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/admin/recruiting">回招聘管理</a>
          <a class="btn alt" href="/school-platform/api/recruiting/applicants/{applicant.id}">查看案件 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>基本資料</h2>
            <p>Email：{escape(applicant.email)}</p>
            <p>電話：{escape(applicant.phone or '未填寫')}</p>
            <p>履歷：{escape(applicant.resume_link or '未附連結')}</p>
            <p>備註：{applicant_note}</p>
            <p>職缺：{escape(position.title)} / {escape(position.department)}</p>
          </article>
          <article class="card">
            <h2>AI 評估建議</h2>
            <p>Recommendation：<code>{escape(evaluation.recommendation)}</code></p>
            <p>下一步：{escape(evaluation.next_action)}</p>
            <ul class="clean">{strength_items}</ul>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>風險提醒</h2>
            <ul class="clean">{concern_items}</ul>
          </article>
          <article class="card">
            <h2>建議面試題</h2>
            <ul class="clean">{question_items}</ul>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>安排面試</h2>
            <form class="stack" method="post" action="/school-platform/admin/recruiting/interviews/create">
              <input type="hidden" name="applicant_id" value="{applicant.id}" />
              <input type="hidden" name="return_to" value="/school-platform/admin/recruiting/applicants/{applicant.id}" />
              <label class="field">面試時間
                <input type="datetime-local" name="interview_at" />
              </label>
              <label class="field">面試官
                <input type="text" name="interviewer_name" value="Yuki Wang" />
              </label>
              <label class="field">形式
                <select name="format">
                  <option value="google_meet">google_meet</option>
                  <option value="zoom">zoom</option>
                  <option value="onsite">onsite</option>
                </select>
              </label>
              <button class="btn" type="submit">安排面試</button>
            </form>
          </article>
          <article class="card">
            <h2>更新案件進度</h2>
            <form class="stack" method="post" action="/school-platform/admin/recruiting/applicants/{applicant.id}/status">
              <label class="field">案件階段
                <select name="interview_status">{applicant_status_options}</select>
              </label>
              <label class="field">HR 備註
                <textarea name="note" placeholder="例如：先安排試教、待主管 final review、或放入人才庫"></textarea>
              </label>
              <button class="btn" type="submit">儲存案件進度</button>
            </form>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>案件摘要</h2>
            <p>建立時間：<code>{escape(applicant.created_at.isoformat())}</code></p>
            <p>職缺需求：{escape(position.summary)}</p>
            <p>需求條件：{escape(' / '.join(position.requirements) if position.requirements else '未填寫')}</p>
          </article>
          <article class="card">
            <h2>面試流程建議</h2>
            <p>目前階段：<code>{escape(applicant.interview_status)}</code></p>
            <p>建議下一步：{escape(evaluation.next_action)}</p>
            <p>若已完成面談，可直接在下方面試紀錄卡填寫評語、更新案件階段，並推進到錄取或婉拒。</p>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>到職 / 試用追蹤</h2>
            <p>Onboarding：<code>{escape(onboarding.stage if onboarding else 'not_created')}</code></p>
            <p>Probation：<code>{escape(onboarding.probation_status if onboarding else 'not_started')}</code></p>
            <p>Owner：{escape(onboarding.owner_name if onboarding else 'Yuki Wang')}</p>
            <p>預計報到：{escape(onboarding.start_date.isoformat() if onboarding and onboarding.start_date else '未設定')}</p>
            <p>試用期結束：{escape(onboarding.probation_end_date.isoformat() if onboarding and onboarding.probation_end_date else '未設定')}</p>
            <p>備註：{escape(onboarding.notes or '尚未填寫').replace(chr(10), '<br />') if onboarding else '尚未建立 onboarding 紀錄，錄取後可直接在右側建立。'}</p>
          </article>
          <article class="card">
            <h2>更新 onboarding / probation</h2>
            <form class="stack" method="post" action="/school-platform/admin/recruiting/applicants/{applicant.id}/onboarding">
              <label class="field">Owner
                <input type="text" name="owner_name" value="{escape(onboarding.owner_name if onboarding else 'Yuki Wang')}" />
              </label>
              <label class="field">Onboarding 階段
                <select name="stage">{onboarding_stage_options}</select>
              </label>
              <label class="field">報到日
                <input type="date" name="start_date" value="{escape(onboarding.start_date.isoformat() if onboarding and onboarding.start_date else '')}" />
              </label>
              <label class="field">Probation 狀態
                <select name="probation_status">{probation_status_options}</select>
              </label>
              <label class="field">試用期結束日
                <input type="date" name="probation_end_date" value="{escape(onboarding.probation_end_date.isoformat() if onboarding and onboarding.probation_end_date else '')}" />
              </label>
              <label class="field">Checklist
                <textarea name="checklist_items" placeholder="一行一項">{escape(onboarding_checklist_text)}</textarea>
              </label>
              <label class="field">備註
                <textarea name="notes" placeholder="例如：報到第一週需完成系統權限與教學觀課">{escape(onboarding.notes or '') if onboarding else ''}</textarea>
              </label>
              <button class="btn" type="submit">儲存 onboarding / probation</button>
            </form>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>面試紀錄與評分</h2>
        <div class="grid two">{interview_cards}</div>
      </section>
    """
    return _page_shell("應徵者詳情", body)


@router.get("/admin/executive", response_class=HTMLResponse)
def school_platform_admin_executive_page() -> str:
    snapshot = executive_dashboard_service.snapshot()
    summary = snapshot.summary
    alert_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(alert.severity)}</div>"
            f"<h3>{escape(alert.title)}</h3>"
            f"<p>{escape(alert.detail)}</p>"
            "</article>"
        )
        for alert in snapshot.alerts
    ) or "<article class='card'><h3>目前沒有營運警示</h3></article>"
    lead_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.status)} / {escape(item.interested_course_slug or 'general')}</div>"
            f"<h3>{escape(item.name)}</h3>"
            f"<p>{escape(item.latest_log_summary or '尚無最新跟進摘要')}</p>"
            f"<div class='meta'><span class='chip'>意向 {item.intent_score:g}</span><span class='chip'>成交率 {item.win_probability:g}%</span></div>"
            "</article>"
        )
        for item in snapshot.hot_leads
    ) or "<article class='card'><h3>目前沒有高熱度名單</h3></article>"
    risk_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.risk_level)} / {escape(item.weak_spot)}</div>"
            f"<h3>{escape(item.chinese_name)}</h3>"
            f"<p>{escape(item.email)}</p>"
            f"<div class='meta'><span class='chip'>待補作業 {item.pending_assignments}</span><span class='chip'>待補測驗 {item.pending_exams}</span><span class='chip'>出席率 {item.attendance_rate:g}%</span></div>"
            "</article>"
        )
        for item in snapshot.high_risk_students
    ) or "<article class='card'><h3>目前沒有高風險學員</h3></article>"
    class_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.course_slug)} / {escape(item.teacher_name)}</div>"
            f"<h3>{escape(item.class_name)}</h3>"
            f"<p>滿班率 {item.fill_rate:g}% / 剩餘名額 {item.seats_left}</p>"
            f"<div class='meta'><span class='chip'>{item.enrolled_count}/{item.capacity}</span></div>"
            "</article>"
        )
        for item in snapshot.class_watchlist
    ) or "<article class='card'><h3>目前沒有班級容量資料</h3></article>"
    ai_cards = "".join(
        (
            "<article class='card'>"
            f"<div class='eyebrow'>{escape(item.module_name)}</div>"
            f"<h3>最近 7 天使用 {item.action_count} 次</h3>"
            f"<p>最近動作：{escape(item.latest_action_name or 'unknown')}</p>"
            f"<div class='meta'><span class='chip'>{escape(item.latest_at.isoformat() if item.latest_at else 'n/a')}</span></div>"
            "</article>"
        )
        for item in snapshot.ai_module_usage
    ) or "<article class='card'><h3>最近 7 天尚無 AI 使用紀錄</h3></article>"
    recommendation_items = "".join(f"<li>{escape(item)}</li>" for item in snapshot.recommendations)
    body = f"""
      <section class="hero">
        <div class="eyebrow">Executive Dashboard</div>
        <h1>主管工作台</h1>
        <p>把招生、學員、財務、教務、客服、招聘與 AI 使用整合成單一營運決策頁，讓主管直接抓到現在最該處理的事情。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/admin/executive-dashboard">查看主管 JSON</a>
          <a class="btn alt" href="/school-platform/admin/reports">前往報表中心</a>
        </div>
      </section>
      <section class="section">
        <h2>核心摘要</h2>
        <div class="stat-grid">
          <div class="stat"><div class="label">進行中班級</div><div class="value">{summary.active_classes}</div></div>
          <div class="stat"><div class="label">進行中學員</div><div class="value">{summary.active_students}</div></div>
          <div class="stat"><div class="label">逾期跟進</div><div class="value">{summary.overdue_follow_ups}</div></div>
          <div class="stat"><div class="label">高風險學員</div><div class="value">{summary.high_risk_students}</div></div>
          <div class="stat"><div class="label">待評分</div><div class="value">{summary.pending_reviews}</div></div>
          <div class="stat"><div class="label">待處理客服</div><div class="value">{summary.queued_support_cases}</div></div>
          <div class="stat"><div class="label">已收營收</div><div class="value">{_format_jpy(summary.paid_revenue)}</div></div>
          <div class="stat"><div class="label">待收營收</div><div class="value">{_format_jpy(summary.pending_revenue)}</div></div>
          <div class="stat"><div class="label">開放職缺</div><div class="value">{summary.open_jobs}</div></div>
          <div class="stat"><div class="label">應徵者</div><div class="value">{summary.applicants}</div></div>
          <div class="stat"><div class="label">面試安排</div><div class="value">{summary.scheduled_interviews}</div></div>
          <div class="stat"><div class="label">AI 7 日使用</div><div class="value">{summary.ai_actions_last_7_days}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>營運警示</h2>
        <div class="grid two">{alert_cards}</div>
      </section>
      <section class="section">
        <div class="grid two">
          <article>
            <h2>熱度最高名單</h2>
            <div class="list">{lead_cards}</div>
          </article>
          <article>
            <h2>高風險學員</h2>
            <div class="list">{risk_cards}</div>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article>
            <h2>班級容量觀察</h2>
            <div class="list">{class_cards}</div>
          </article>
          <article>
            <h2>AI 模組使用</h2>
            <div class="list">{ai_cards}</div>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>本週建議</h2>
        <ul class="clean">{recommendation_items}</ul>
      </section>
    """
    return _page_shell("主管工作台", body)


@router.get("/admin/reports", response_class=HTMLResponse)
def school_platform_admin_reports_page() -> str:
    report = analytics_service.report_overview()
    weekly = analytics_service.weekly_ai_summary()
    lead_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(status_value)}</h3>"
        f"<p>名單數：{count}</p>"
        "</article>"
        for status_value, count in report.lead_status_counts.items()
    ) or "<article class='card'><h3>尚無名單資料</h3></article>"
    fill_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(str(item['class_name']))}</h3>"
        f"<p>{escape(str(item['course_slug']))}</p>"
        f"<div class='meta'><span class='chip'>滿班率 {item['fill_rate']}%</span><span class='chip'>{item['enrolled_count']}/{item['capacity']}</span></div>"
        "</article>"
        for item in report.course_fill_rates[:6]
    ) or "<article class='card'><h3>尚無班級資料</h3></article>"
    insight_items = "".join(f"<li>{escape(str(item))}</li>" for item in weekly["insights"])
    action_items = "".join(f"<li>{escape(str(item))}</li>" for item in weekly["actions"])
    body = f"""
      <section class="hero">
        <div class="eyebrow">Reports Center</div>
        <h1>報表中心</h1>
        <p>這裡把招生、班級滿班率、營收、招聘與教務資料整理成主管可直接看的中文儀表板。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/admin/executive">打開主管工作台</a>
          <a class="btn alt" href="/school-platform/api/reports/overview">查看報表 JSON</a>
          <a class="btn alt" href="/school-platform/admin/ai-center">查看 AI 助理中心</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">已收營收</div><div class="value">{_format_jpy(report.revenue_summary['paid'])}</div></div>
          <div class="stat"><div class="label">待收營收</div><div class="value">{_format_jpy(report.revenue_summary['pending'])}</div></div>
          <div class="stat"><div class="label">應徵者</div><div class="value">{report.recruiting_summary['applicants']}</div></div>
          <div class="stat"><div class="label">作業數</div><div class="value">{report.teaching_summary['assignments']}</div></div>
        </div>
      </section>
      <section class="section">
        <h2>名單狀態分布</h2>
        <div class="grid two">{lead_cards}</div>
      </section>
      <section class="section">
        <h2>班級滿班率</h2>
        <div class="grid two">{fill_cards}</div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>{escape(str(weekly['headline']))}</h2>
            <ul class="clean">{insight_items}</ul>
          </article>
          <article class="card">
            <h2>建議動作</h2>
            <ul class="clean">{action_items}</ul>
          </article>
        </div>
      </section>
    """
    return _page_shell("報表中心", body)


@router.get("/admin/ai-center", response_class=HTMLResponse)
def school_platform_admin_ai_center_page() -> str:
    logs = analytics_service.ai_logs()[:12]
    weekly = analytics_service.weekly_ai_summary()
    provider_status = ai_assistant_service.provider_status()
    log_cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.module_name)} / {escape(item.action_name)}</div>"
        f"<h3>{escape(item.actor_email or 'system')}</h3>"
        f"<p>Input: {escape(item.input_summary)}</p>"
        f"<p>Output: {escape(item.output_summary)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.created_at.isoformat())}</span></div>"
        "</article>"
        for item in logs
    ) or "<article class='card'><h3>目前沒有 AI 紀錄</h3></article>"
    insight_items = "".join(f"<li>{escape(str(item))}</li>" for item in weekly["insights"])
    support_items = "".join(f"<li>{escape(item)}</li>" for item in provider_status.supported_features)
    last_error = escape(provider_status.last_error or "none")
    body = f"""
      <section class="hero">
        <div class="eyebrow">AI Operations Center</div>
        <h1>AI 助理中心</h1>
        <p>這裡集中顯示 AI 跟進草稿、營運摘要與系統內部 AI 操作紀錄，方便主管追蹤自動化使用狀況。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/admin/ai-teaching">打開 AI 教案中心</a>
          <a class="btn alt" href="/school-platform/api/ai/logs">查看 AI logs JSON</a>
          <a class="btn alt" href="/school-platform/api/ai/status">查看 AI status JSON</a>
          <a class="btn alt" href="/school-platform/api/reports/weekly-summary">查看週摘要 JSON</a>
        </div>
      </section>
      <section class="section">
        <h2>AI Provider 狀態</h2>
        <div class="stat-grid">
          <div class="stat"><div class="label">服務可用</div><div class="value">{'yes' if provider_status.service_ready else 'no'}</div></div>
          <div class="stat"><div class="label">外部模型就緒</div><div class="value">{'yes' if provider_status.external_model_ready else 'no'}</div></div>
          <div class="stat"><div class="label">目前供應商</div><div class="value">{escape(provider_status.active_provider)}</div></div>
          <div class="stat"><div class="label">runtime 模式</div><div class="value">{escape(provider_status.runtime_mode)}</div></div>
          <div class="stat"><div class="label">模型</div><div class="value">{escape(provider_status.model_name or 'n/a')}</div></div>
          <div class="stat"><div class="label">最近 provider 錯誤</div><div class="value">{last_error}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>本週 AI 營運摘要</h2>
            <ul class="clean">{insight_items}</ul>
          </article>
          <article class="card">
            <h2>AI 目前支援</h2>
            <ul class="clean">{support_items}</ul>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>AI 操作紀錄</h2>
        <div class="grid two">{log_cards}</div>
      </section>
    """
    return _page_shell("AI 助理中心", body)


@router.get("/admin/ai-teaching", response_class=HTMLResponse)
def school_platform_admin_ai_teaching_page(
    class_id: str | None = Query(default=None),
    lesson_focus: str = Query(default="藥局與租屋生活會話"),
    duration_minutes: int = Query(default=90),
) -> str:
    classes = catalog_service.open_classes()
    class_options = "".join(
        f"<option value='{item.id}' {'selected' if class_id == str(item.id) else ''}>{escape(item.name)} / {escape(item.teacher_name)} / {escape(item.weekday)}</option>"
        for item in classes
    )
    draft = None
    selected_class_id = class_id or (str(classes[0].id) if classes else None)
    if selected_class_id:
        try:
            draft = ai_assistant_service.lesson_plan_draft(
                LessonPlanDraftRequest(
                    class_id=UUID(selected_class_id),
                    lesson_focus=lesson_focus,
                    duration_minutes=duration_minutes,
                )
            )
        except KeyError:
            draft = None
    step_cards = (
        "".join(
            (
                "<article class='card'>"
                f"<div class='eyebrow'>{item.minutes} 分鐘</div>"
                f"<h3>{escape(item.title)}</h3>"
                f"<p>{escape(item.details)}</p>"
                "</article>"
            )
            for item in draft.teaching_steps
        )
        if draft
        else "<article class='card'><h3>目前沒有教案草稿</h3></article>"
    )
    review_items = "".join(f"<li>{escape(item)}</li>" for item in draft.review_points) if draft else "<li>請先選班級產生草稿</li>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">AI Teaching Drafts</div>
        <h1>AI 教案草稿中心</h1>
        <p>這裡可以依照班級、課堂主題與時長，快速生成可給老師修改的教案草稿與課後作業建議。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin/ai-center">回 AI 助理中心</a>
          <a class="btn alt" href="/school-platform/api/ai/logs?module_name=teaching">查看 teaching AI logs</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>產生教案草稿</h2>
            <form class="stack" method="get" action="/school-platform/admin/ai-teaching">
              <label class="field">班級
                <select name="class_id">{class_options}</select>
              </label>
              <label class="field">課堂焦點
                <input type="text" name="lesson_focus" value="{escape(lesson_focus)}" />
              </label>
              <label class="field">課程時長（分鐘）
                <input type="number" name="duration_minutes" min="30" step="10" value="{duration_minutes}" />
              </label>
              <button class="btn" type="submit">生成草稿</button>
            </form>
          </article>
          <article class="card">
            <h2>草稿摘要</h2>
            {f"<p>班級：{escape(draft.class_name)}</p><p>老師：{escape(draft.teacher_name)}</p><p>焦點：{escape(draft.lesson_focus)}</p><p>教學目標：{escape(draft.objective)}</p><p>暖身：{escape(draft.warmup)}</p><p>課後作業：{escape(draft.homework)}</p>" if draft else "<p>選擇班級後即可生成教案草稿。</p>"}
          </article>
        </div>
      </section>
      <section class="section">
        <h2>教學步驟</h2>
        <div class="grid two">{step_cards}</div>
      </section>
      <section class="section">
        <h2>教師提醒</h2>
        <article class="card"><ul class="clean">{review_items}</ul></article>
      </section>
    """
    return _page_shell("AI 教案草稿中心", body)


@router.post("/admin/recruiting/jobs/create")
def school_platform_admin_job_create_submit(
    title: str = Form(...),
    department: str = Form(...),
    employment_type: str = Form(...),
    location_label: str = Form(...),
    salary_range: str = Form(...),
    summary: str = Form(...),
    requirements: str = Form(default=""),
):
    recruiting_service.create_job(
        JobPositionCreateRequest(
            title=title,
            department=department,
            employment_type=employment_type,
            location_label=location_label,
            salary_range=salary_range,
            summary=summary,
            requirements=[item.strip() for item in requirements.splitlines() if item.strip()],
        )
    )
    return RedirectResponse(url="/school-platform/admin/recruiting", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/recruiting/interviews/create")
def school_platform_admin_interview_create_submit(
    applicant_id: str = Form(...),
    interview_at: str = Form(...),
    interviewer_name: str = Form(...),
    format: str = Form(default="google_meet"),
    return_to: str = Form(default=""),
):
    try:
        recruiting_service.schedule_interview(
            InterviewCreateRequest(
                applicant_id=UUID(applicant_id),
                interview_at=datetime.fromisoformat(interview_at),
                interviewer_name=interviewer_name,
                format=format,
            )
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=404, detail="Applicant not found") from exc
    redirect_to = return_to or "/school-platform/admin/recruiting"
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/recruiting/applicants/{applicant_id}/status")
def school_platform_admin_applicant_status_submit(
    applicant_id: UUID,
    interview_status: str = Form(...),
    note: str = Form(default=""),
):
    try:
        recruiting_service.update_applicant_status(
            applicant_id,
            ApplicantStatusUpdateRequest(interview_status=interview_status, note=note or None),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Applicant not found") from exc
    return RedirectResponse(
        url=f"/school-platform/admin/recruiting/applicants/{applicant_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/recruiting/applicants/{applicant_id}/onboarding")
def school_platform_admin_applicant_onboarding_submit(
    applicant_id: UUID,
    owner_name: str = Form(default="Yuki Wang"),
    stage: str = Form(default="preboarding"),
    start_date: str = Form(default=""),
    probation_status: str = Form(default="not_started"),
    probation_end_date: str = Form(default=""),
    checklist_items: str = Form(default=""),
    notes: str = Form(default=""),
):
    try:
        recruiting_service.upsert_onboarding_record(
            applicant_id,
            OnboardingUpsertRequest(
                owner_name=owner_name or None,
                stage=stage,
                start_date=date.fromisoformat(start_date) if start_date else None,
                probation_status=probation_status,
                probation_end_date=date.fromisoformat(probation_end_date) if probation_end_date else None,
                checklist_items=[item.strip() for item in checklist_items.splitlines() if item.strip()],
                notes=notes or None,
            ),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Applicant not found") from exc
    return RedirectResponse(
        url=f"/school-platform/admin/recruiting/applicants/{applicant_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/admin/recruiting/interviews/{interview_id}/review")
def school_platform_admin_interview_review_submit(
    interview_id: UUID,
    interview_status_value: str = Form(...),
    applicant_status: str = Form(...),
    feedback: str = Form(default=""),
    note: str = Form(default=""),
):
    try:
        interview = recruiting_service.update_interview(
            interview_id,
            InterviewUpdateRequest(status=interview_status_value, feedback=feedback or None),
        )
        recruiting_service.update_applicant_status(
            interview.applicant_id,
            ApplicantStatusUpdateRequest(interview_status=applicant_status, note=note or None),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Interview not found") from exc
    return RedirectResponse(
        url=f"/school-platform/admin/recruiting/applicants/{interview.applicant_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/admin/support-inbox", response_class=HTMLResponse)
def school_platform_admin_support_inbox_page() -> str:
    summary = admissions_service.support_inbox_summary()
    items = admissions_service.support_inbox()
    cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item.type)}</div>"
        f"<h3>{escape(item.title)}</h3>"
        f"<p>{escape(item.content)}</p>"
        f"<div class='meta'><span class='chip'>{escape(item.channel)}</span><span class='chip'>{escape(item.status)}</span><span class='chip'>{escape(item.created_at.isoformat())}</span></div>"
        f"<div class='actions'><a class='btn' href='/school-platform/admin/support-inbox/{item.id}'>查看案件</a></div>"
        "</article>"
        for item in items
    ) or "<article class='card'><h3>目前沒有客服需求</h3></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">Support Inbox</div>
        <h1>客服收件箱</h1>
        <p>這裡集中顯示從學員端送進來的客服需求，方便管理端追蹤與後續處理。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/admin">回營運總覽</a>
          <a class="btn alt" href="/school-platform/api/notifications?user_email=admin@jls.local">查看通知 JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="stat-grid">
          <div class="stat"><div class="label">總需求數</div><div class="value">{summary['total']}</div></div>
          <div class="stat"><div class="label">待處理</div><div class="value">{summary['queued']}</div></div>
          <div class="stat"><div class="label">處理中</div><div class="value">{summary['processing']}</div></div>
          <div class="stat"><div class="label">已解決</div><div class="value">{summary['resolved']}</div></div>
          <div class="stat"><div class="label">In-app 通知</div><div class="value">{summary['in_app']}</div></div>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("客服收件箱", body)


@router.post("/teacher/assignment-submissions/{submission_id}/grade")
def school_platform_teacher_assignment_grade_submit(
    submission_id: UUID,
    teacher_name: str = Form(...),
    score: float = Form(...),
    feedback: str = Form(default=""),
    graded_by: str = Form(default="Aki Mori"),
    return_to: str = Form(default=""),
):
    try:
        teaching_ops_service.grade_assignment_submission(
            submission_id,
            SubmissionGradeRequest(score=score, feedback=feedback or None, graded_by=graded_by or teacher_name),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Assignment submission not found") from exc
    redirect_to = return_to or f"/school-platform/teacher-portal?{urlencode({'teacher_name': teacher_name})}"
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/teacher/exam-submissions/{submission_id}/grade")
def school_platform_teacher_exam_grade_submit(
    submission_id: UUID,
    teacher_name: str = Form(...),
    score: float = Form(...),
    feedback: str = Form(default=""),
    graded_by: str = Form(default="Aki Mori"),
    return_to: str = Form(default=""),
):
    try:
        teaching_ops_service.grade_exam_submission(
            submission_id,
            SubmissionGradeRequest(score=score, feedback=feedback or None, graded_by=graded_by or teacher_name),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Exam submission not found") from exc
    redirect_to = return_to or f"/school-platform/teacher-portal?{urlencode({'teacher_name': teacher_name})}"
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/teacher/classes/{class_id}/attendance")
def school_platform_teacher_class_attendance_submit(
    class_id: UUID,
    teacher_name: str = Form(...),
    student_email: str = Form(...),
    class_date_value: str = Form(...),
    status_value: str = Form(...),
    note: str = Form(default=""),
):
    try:
        teaching_ops_service.mark_attendance(
            AttendanceMarkRequest(
                class_id=class_id,
                student_email=student_email,
                class_date=date.fromisoformat(class_date_value),
                status=status_value,
                note=note or None,
                marked_by=teacher_name,
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail="Invalid attendance payload") from exc
    query = urlencode({"teacher_name": teacher_name})
    return RedirectResponse(
        url=f"/school-platform/teacher/classes/{class_id}?{query}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/teacher/classes/{class_id}/session-records")
def school_platform_teacher_session_record_submit(
    class_id: UUID,
    teacher_name: str = Form(...),
    class_date_value: str = Form(...),
    summary_text: str = Form(...),
    materials_link: str = Form(default=""),
    homework_summary: str = Form(default=""),
    next_class_focus: str = Form(default=""),
    student_risk_notes: str = Form(default=""),
    approval_status_value: str = Form(default="submitted"),
    return_to: str = Form(default=""),
):
    try:
        teaching_ops_service.upsert_teaching_session_record(
            TeachingSessionUpsertRequest(
                class_id=class_id,
                teacher_name=teacher_name,
                class_date=date.fromisoformat(class_date_value),
                summary=summary_text,
                materials_link=materials_link or None,
                homework_summary=homework_summary or None,
                next_class_focus=next_class_focus or None,
                student_risk_notes=[item.strip() for item in student_risk_notes.splitlines() if item.strip()],
                approval_status=approval_status_value,
            ),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Class not found") from exc
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail="Invalid teaching session payload") from exc
    redirect_to = return_to or f"/school-platform/teacher/classes/{class_id}?{urlencode({'teacher_name': teacher_name})}"
    return RedirectResponse(url=redirect_to, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/support-inbox/{notification_id}", response_class=HTMLResponse)
def school_platform_admin_support_detail_page(notification_id: UUID) -> str:
    try:
        notification = notification_service.get_notification(notification_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Support request not found") from exc
    body = f"""
      <section class="hero">
        <div class="eyebrow">Support Detail</div>
        <h1>客服案件詳情</h1>
        <p>這裡可以更新案件狀態並直接回覆學生。</p>
        <div class="meta">
          <span class="chip">{escape(notification.type)}</span>
          <span class="chip">{escape(notification.status)}</span>
          <span class="chip">{escape(notification.created_at.isoformat())}</span>
        </div>
        <div class="actions">
          <a class="btn" href="/school-platform/admin/support-inbox">回客服收件箱</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h2>案件內容</h2>
            <p>{escape(notification.title)}</p>
            <p>{escape(notification.content)}</p>
          </article>
          <article class="card">
            <h2>更新狀態</h2>
            <form class="stack" method="post" action="/school-platform/admin/support-inbox/{notification.id}/status">
              <label class="field">狀態
                <select name="status_value">
                  <option value="processing">processing</option>
                  <option value="resolved">resolved</option>
                </select>
              </label>
              <button class="btn" type="submit">更新案件狀態</button>
            </form>
          </article>
        </div>
      </section>
      <section class="section">
        <article class="card">
          <h2>回覆學生</h2>
          <form class="stack" method="post" action="/school-platform/admin/support-inbox/{notification.id}/reply">
            <label class="field">回覆狀態
              <select name="status_value">
                <option value="processing">processing</option>
                <option value="resolved">resolved</option>
              </select>
            </label>
            <label class="field">回覆管道
              <select name="response_channel">
                <option value="email">email</option>
                <option value="line">line</option>
                <option value="in_app">in_app</option>
              </select>
            </label>
            <label class="field">回覆內容
              <textarea name="response_message" placeholder="輸入要回給學生的內容"></textarea>
            </label>
            <button class="btn" type="submit">送出回覆並更新狀態</button>
          </form>
        </article>
      </section>
    """
    return _page_shell("客服案件詳情", body)


@router.post("/admin/support-inbox/{notification_id}/status")
def school_platform_admin_support_status_submit(
    notification_id: UUID,
    status_value: str = Form(...),
):
    try:
        notification_service.update_status(notification_id, status_value)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Support request not found") from exc
    return RedirectResponse(url=f"/school-platform/admin/support-inbox/{notification_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/support-inbox/{notification_id}/reply")
def school_platform_admin_support_reply_submit(
    notification_id: UUID,
    status_value: str = Form(...),
    response_channel: str = Form(...),
    response_message: str = Form(...),
):
    try:
        student_support_service.process_support_request(notification_id, status_value, response_message, response_channel)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Support request not found") from exc
    return RedirectResponse(url=f"/school-platform/admin/support-inbox/{notification_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/progress", response_class=HTMLResponse)
def school_platform_progress_page() -> str:
    snapshot = platform_status_service.progress_snapshot()
    cards = "".join(
        "<article class='card'>"
        f"<div class='status {module.status}'>{escape(module.status.replace('_', ' '))}</div>"
        f"<h3>{escape(module.name)}</h3>"
        f"<p>{escape(module.summary)}</p>"
        "</article>"
        for module in snapshot.modules
    )
    next_actions = "".join(f"<li>{escape(item)}</li>" for item in snapshot.next_actions)
    route_cards = "".join(
        [
            "<article class='route-card'>"
            "<div class='route-label'>前台課程 API</div>"
            "<code>/school-platform/api/public/courses</code>"
            "<p>查看目前公開課程清單。</p>"
            "</article>",
            "<article class='route-card'>"
            "<div class='route-label'>管理儀表板 API</div>"
            "<code>/school-platform/api/admin/dashboard</code>"
            "<p>查看招生、報名、營收與待跟進摘要。</p>"
            "</article>",
            "<article class='route-card'>"
            "<div class='route-label'>開發進度 JSON</div>"
            "<code>/school-platform/api/progress</code>"
            "<p>查看目前完成模組、測試數與下一步。</p>"
            "</article>",
            "<article class='route-card'>"
            "<div class='route-label'>學員儀表板 API</div>"
            "<code>/school-platform/api/student/dashboard?email=...</code>"
            "<p>查看學員課程、付款狀態與通知數量。</p>"
            "</article>",
        ]
    )
    legend = "".join(
        [
            "<div class='legend-item'><span class='dot completed'></span><span>已完成：目前已可用或已通過測試</span></div>",
            "<div class='legend-item'><span class='dot in_progress'></span><span>開發中：已有骨架，正在持續補功能</span></div>",
            "<div class='legend-item'><span class='dot planned'></span><span>已規劃：下一階段會接上的模組</span></div>",
        ]
    )
    return f"""
    <!doctype html>
    <html lang="zh-Hant">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>平台開發進度</title>
        <style>
          :root {{
            --bg: #f5f1e8;
            --paper: #fffdf8;
            --ink: #1b211f;
            --muted: #5f6b66;
            --line: #d9d0bf;
            --ok: #1c7c54;
            --run: #c86d1f;
            --plan: #6a7280;
            --accent: #b64f31;
            --accent-soft: rgba(182,79,49,.10);
          }}
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; font-family: ui-sans-serif, system-ui, sans-serif; background: linear-gradient(180deg, #f8f5ef, var(--bg)); color: var(--ink); }}
          .wrap {{ max-width: 1180px; margin: 0 auto; padding: 28px 20px 64px; }}
          .hero {{ background: var(--paper); border: 1px solid var(--line); border-radius: 24px; padding: 24px; }}
          .hero h1 {{ margin: 10px 0; font-size: 40px; }}
          .muted {{ color: var(--muted); }}
          .chip-row {{ display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px; }}
          .chip {{ display: inline-flex; align-items: center; padding: 8px 12px; border-radius: 999px; background: var(--accent-soft); color: var(--accent); font-weight: 700; font-size: 13px; }}
          .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-top: 18px; }}
          .stat {{ background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 16px; }}
          .label {{ font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); }}
          .value {{ margin-top: 8px; font-size: 28px; font-weight: 800; }}
          .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-top: 18px; }}
          .card {{ background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 18px; }}
          .card h3 {{ margin: 10px 0 6px; }}
          .status {{ display: inline-block; padding: 6px 10px; border-radius: 999px; font-size: 12px; font-weight: 800; text-transform: uppercase; }}
          .status.completed {{ background: rgba(28,124,84,.12); color: var(--ok); }}
          .status.in_progress {{ background: rgba(200,109,31,.12); color: var(--run); }}
          .status.planned {{ background: rgba(106,114,128,.12); color: var(--plan); }}
          .section {{ background: var(--paper); border: 1px solid var(--line); border-radius: 24px; padding: 22px; margin-top: 18px; }}
          .section h2 {{ margin: 0 0 8px; font-size: 24px; }}
          .route-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin-top: 14px; }}
          .route-card {{ background: #fff; border: 1px solid var(--line); border-radius: 18px; padding: 16px; }}
          .route-label {{ font-size: 14px; font-weight: 800; margin-bottom: 8px; }}
          .route-card code {{ display: inline-block; font-size: 13px; margin-bottom: 8px; }}
          .route-card p {{ margin: 0; color: var(--muted); line-height: 1.6; }}
          .legend {{ display: grid; gap: 10px; margin-top: 14px; }}
          .legend-item {{ display: flex; align-items: center; gap: 10px; color: var(--muted); }}
          .dot {{ width: 12px; height: 12px; border-radius: 999px; display: inline-block; }}
          .dot.completed {{ background: var(--ok); }}
          .dot.in_progress {{ background: var(--run); }}
          .dot.planned {{ background: var(--plan); }}
          .helper-list {{ display: grid; gap: 8px; margin-top: 14px; color: var(--muted); }}
          ul {{ margin: 0; padding-left: 20px; }}
          a {{ color: var(--accent); font-weight: 700; text-decoration: none; }}
          code {{ background: #f3ecdf; padding: 3px 8px; border-radius: 10px; }}
          @media (max-width: 900px) {{ .stats, .grid, .route-grid {{ grid-template-columns: 1fr; }} .hero h1 {{ font-size: 30px; }} }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <section class="hero">
            <div class="muted">AI 日語補習班營運平台 / Live Progress</div>
            <h1>平台開發進度總覽</h1>
            <p class="muted">這是一個給你直接看的中文可視化頁面。你不用再問我有沒有繼續開發，打開這頁就能看到目前完成到哪、測試有沒有過、下一步要接什麼。</p>
            <p class="muted">更新時間：{escape(snapshot.updated_at.isoformat())}</p>
            <div class="chip-row">
              <div class="chip">目前模式：持續開發中</div>
              <div class="chip">可查看 API 進度</div>
              <div class="chip">可追蹤模組狀態</div>
            </div>
            <div class="stats">
              <div class="stat"><div class="label">完成模組</div><div class="value">{snapshot.completed_modules}/{snapshot.total_modules}</div></div>
              <div class="stat"><div class="label">測試通過</div><div class="value">{snapshot.tests_passing}</div></div>
              <div class="stat"><div class="label">追蹤檔案</div><div class="value">{snapshot.tracked_files}</div></div>
              <div class="stat"><div class="label">資料行數</div><div class="value">{snapshot.lines_of_code}</div></div>
            </div>
          </section>
          <section class="section">
            <h2>狀態說明</h2>
            <p class="muted">下面的模組卡片會標出目前是已完成、開發中，還是已規劃但尚未開工。</p>
            <div class="legend">{legend}</div>
          </section>
          <section class="grid">{cards}</section>
          <section class="section">
            <h2>目前可直接打開的功能入口</h2>
            <p class="muted">如果你想快速驗證我是不是有持續在做，可以直接打下面這些入口。</p>
            <div class="route-grid">{route_cards}</div>
          </section>
          <section class="section">
            <h2>下一步正在接什麼</h2>
            <ul>{next_actions}</ul>
            <div class="helper-list">
              <div>說明 1：這些是我接下來會持續往前補的項目，不是空白規劃。</div>
              <div>說明 2：如果這裡有變化，就代表我有繼續往前寫。</div>
              <div>說明 3：原始 JSON 可從 <a href="/school-platform/api/progress">/school-platform/api/progress</a> 查看。</div>
            </div>
          </section>
        </div>
      </body>
    </html>
    """


@router.get("/activity", response_class=HTMLResponse)
def school_platform_activity_page() -> str:
    items = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{escape(item['time'])}</div>"
        f"<h3>{escape(item['title'])}</h3>"
        f"<p>{escape(item['summary'])}</p>"
        "</article>"
        for item in platform_status_service.activity_feed()
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">Activity Feed</div>
        <h1>最近開發紀錄</h1>
        <p>如果你想知道我是不是有真的往前寫，直接看這頁。這裡會用中文列出最近補上的區塊。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/progress">回進度總覽</a>
          <a class="btn alt" href="/school-platform/api/activity">查看 activity JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{items}</div>
      </section>
    """
    return _page_shell("最近開發紀錄", body)


@router.get("/architecture", response_class=HTMLResponse)
def school_platform_architecture_page() -> str:
    domain_cards = "".join(
        [
            "<article class='card'><div class='eyebrow'>Public Growth</div><h3>前台招生域</h3><p>首頁、課程、試聽、報名、AI 推薦與名單收集。</p></article>",
            "<article class='card'><div class='eyebrow'>CRM</div><h3>招生與顧問域</h3><p>lead、指派、跟進、試聽、轉換率與招生漏斗。</p></article>",
            "<article class='card'><div class='eyebrow'>Teaching Ops</div><h3>教務與學員域</h3><p>課程、班級、教師、作業、測驗、學員中心。</p></article>",
            "<article class='card'><div class='eyebrow'>People Ops</div><h3>員工與招聘域</h3><p>staff、KPI、招聘職缺、面試流程與到職追蹤。</p></article>",
            "<article class='card'><div class='eyebrow'>Finance</div><h3>付款與報表域</h3><p>報名、付款、對帳、營收與主管報表。</p></article>",
            "<article class='card'><div class='eyebrow'>AI Layer</div><h3>AI 助理域</h3><p>招生話術、教案草稿、通知輔助與營運分析。</p></article>",
        ]
    )
    layer_cards = "".join(
        [
            "<article class='card'><h3>Presentation Layer</h3><p>公開站、學員中心、顧問後台、教務後台、主管儀表板。</p></article>",
            "<article class='card'><h3>Application API Layer</h3><p>auth、public、student、leads、courses、classes、payments、notifications、admin、ai。</p></article>",
            "<article class='card'><h3>Domain Service Layer</h3><p>LeadService、CourseService、ClassService、EnrollmentService、PaymentService、AIOrchestrator。</p></article>",
            "<article class='card'><h3>Persistence Layer</h3><p>目前 JSON repository，下一步切 PostgreSQL repository + migration。</p></article>",
            "<article class='card'><h3>Async Layer</h3><p>通知、AI worker、webhook reconciliation、週報月報、aggregation jobs。</p></article>",
            "<article class='card'><h3>Observability</h3><p>request logs、AI logs、payment logs、admin audit trail、job retry logs。</p></article>",
        ]
    )
    flow_items = "".join(
        [
            "<li>訪客進站 → 建立 lead → 指派顧問 → 試聽 → enrollment → payment → 學員中心開通</li>",
            "<li>manager 建立課程 → 建立班級 → teacher 授課 → student 學習與提交 → dashboard 聚合</li>",
            "<li>AI 只先產出草稿與建議，外部發送與最終決策保留人工確認</li>",
        ]
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">Platform Architecture</div>
        <h1>完整營運平台架構</h1>
        <p>這頁把 AI 日語補習班平台拆成 domain、系統分層、事件流與部署拓樸，給產品、工程與營運一起看同一張藍圖。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/progress">回進度總覽</a>
          <a class="btn alt" href="/school-platform/activity">回開發紀錄</a>
        </div>
      </section>
      <section class="section">
        <h2>Domain 架構</h2>
        <div class="grid two">{domain_cards}</div>
      </section>
      <section class="section">
        <h2>系統分層</h2>
        <div class="grid two">{layer_cards}</div>
      </section>
      <section class="section">
        <h2>主事件流</h2>
        <article class="card">
          <ul class="clean">{flow_items}</ul>
        </article>
      </section>
      <section class="section">
        <h2>工程現況</h2>
        <div class="grid two">
          <article class="card">
            <h3>已落地</h3>
            <p>公開站、學員中心、招生後台、課程 / 班級 / 教師管理、付款流程、auth / RBAC、進度與 activity 頁。</p>
          </article>
          <article class="card">
            <h3>下一段</h3>
            <p>PostgreSQL repository、通知 sender、AI worker、教務深化、招聘與 HR 模組。</p>
          </article>
        </div>
      </section>
    """
    return _page_shell("完整營運平台架構", body)


@router.get("/system", response_class=HTMLResponse)
def school_platform_system_page() -> str:
    summary = platform_status_service.storage_summary()
    capabilities = summary["capabilities"]
    readiness = summary["readiness"]
    artifacts = summary["migration_artifacts"]
    snapshot_integrity = summary["snapshot_integrity"]
    payment_provider = summary["payment_provider"]
    notification_providers = summary["notification_providers"]
    mutation_tables = "".join(f"<li><code>{escape(item)}</code></li>" for item in summary["mutation_tables"]) or "<li>尚未啟用 row-level mutation tables</li>"
    duplicate_cards = "".join(
        "<article class='card'>"
        f"<h3>{escape(str(item['state_key']))}.{escape(str(item['field']))}</h3>"
        f"<p>duplicate groups：{item['duplicate_count']}</p>"
        f"<p>{escape(str(item['samples'][:3]))}</p>"
        "</article>"
        for item in snapshot_integrity.get("duplicate_groups", [])
    ) or "<article class='card'><h3>Snapshot Integrity 正常</h3><p>目前沒有偵測到會阻擋 PostgreSQL cutover 的 unique-key 衝突。</p></article>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">System Status</div>
        <h1>系統與資料層狀態</h1>
        <p>這頁用來看目前平台實際跑在哪種 storage backend，以及下一步資料層要往哪裡切。</p>
      </section>
      <section class="section">
        <div class="grid two">
          <article class="card">
            <h3>目前 backend</h3>
            <p><code>{escape(str(summary['backend']))}</code></p>
            <p>repository_mode：<code>{escape(str(summary['repository_mode']))}</code></p>
            <p>query_supported：<code>{escape(str(capabilities['query_supported']).lower())}</code></p>
            <p>partial_write_supported：<code>{escape(str(capabilities['partial_write_supported']).lower())}</code></p>
            <p>row_level_write_supported：<code>{escape(str(capabilities['row_level_write_supported']).lower())}</code></p>
            <p>mutation_table_count：<code>{summary['mutation_table_count']}</code></p>
            <p>現在已支援 JSON snapshot file 與 PostgreSQL domain tables 兩種模式。</p>
          </article>
          <article class="card">
            <h3>下一步</h3>
            <p>已經完成 repository abstraction 與 domain tables migration，並開始把高頻 mutation 改成 row-level write。接下來只要提供 PostgreSQL DSN，就能進行真實 cutover 驗證。</p>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>Storage Readiness</h2>
        <div class="grid two">
          <article class="card">
            <h3>狀態摘要</h3>
            <p>ready：<code>{escape(str(readiness['ready']).lower())}</code></p>
            <p>driver_installed：<code>{escape(str(readiness['driver_installed']).lower())}</code></p>
            <p>dsn_present：<code>{escape(str(readiness['dsn_present']).lower())}</code></p>
            <p>connectable：<code>{escape(str(readiness['connectable']).lower())}</code></p>
            <p>initialized：<code>{escape(str(readiness['initialized']).lower())}</code></p>
            <p>tables_ready：<code>{escape(str(readiness['tables_ready']).lower())}</code></p>
          </article>
          <article class="card">
            <h3>說明</h3>
            <p>{escape(str(readiness['message']))}</p>
            <p><code>POST /school-platform/api/system/storage/init</code></p>
            <p>當 backend 為 postgres 且 driver / DSN 都齊全時，可用這個入口初始化 domain tables。</p>
            <p><code>POST /school-platform/api/system/storage/cutover</code></p>
            <p>切到 postgres 後，可用這個入口把目前 JSON snapshot 正式搬進 active PostgreSQL。</p>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>Migration Readiness</h2>
        <div class="grid two">
          <article class="card">
            <h3>Artifacts</h3>
            <p>domain_sql_present：<code>{escape(str(artifacts['domain_sql_present']).lower())}</code></p>
            <p>snapshot_sql_present：<code>{escape(str(artifacts['snapshot_sql_present']).lower())}</code></p>
            <p>init_script_present：<code>{escape(str(artifacts['init_script_present']).lower())}</code></p>
            <p>migrate_script_present：<code>{escape(str(artifacts['migrate_script_present']).lower())}</code></p>
            <p>smoke_test_script_present：<code>{escape(str(artifacts['smoke_test_script_present']).lower())}</code></p>
            <p>cutover_script_present：<code>{escape(str(artifacts['cutover_script_present']).lower())}</code></p>
            <p>deployment_smoke_script_present：<code>{escape(str(artifacts['deployment_smoke_script_present']).lower())}</code></p>
            <p>row_write_probe_script_present：<code>{escape(str(artifacts['row_write_probe_script_present']).lower())}</code></p>
          </article>
          <article class="card">
            <h3>Paths</h3>
            <p><code>{escape(str(artifacts['sql_domain_tables']))}</code></p>
            <p><code>{escape(str(artifacts['init_script']))}</code></p>
            <p><code>{escape(str(artifacts['migrate_script']))}</code></p>
            <p><code>{escape(str(artifacts['smoke_test_script']))}</code></p>
            <p><code>{escape(str(artifacts['cutover_script']))}</code></p>
            <p><code>{escape(str(artifacts['deployment_smoke_script']))}</code></p>
            <p><code>{escape(str(artifacts['row_write_probe_script']))}</code></p>
            <p><a href="/school-platform/db-migration">打開 DB 切換與資料搬遷說明頁</a></p>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>Snapshot Integrity</h2>
        <div class="grid two">
          <article class="card">
            <h3>JSON Source</h3>
            <p>source_json_path：<code>{escape(str(snapshot_integrity['source_json_path']))}</code></p>
            <p>present：<code>{escape(str(snapshot_integrity['present']).lower())}</code></p>
            <p>ready：<code>{escape(str(snapshot_integrity['ready']).lower())}</code></p>
            <p>duplicate_group_count：<code>{escape(str(snapshot_integrity['duplicate_group_count']))}</code></p>
          </article>
          <article class="card">
            <h3>Cutover Note</h3>
            <p>若這裡有 duplicate groups，cutover script 會先做 normalization，再把乾淨資料寫入 PostgreSQL domain tables。</p>
          </article>
        </div>
        <div class="grid two">{duplicate_cards}</div>
      </section>
      <section class="section">
        <h2>External Integrations</h2>
        <div class="grid two">
          <article class="card">
            <h3>Payments</h3>
            <p>provider：<code>{escape(str(payment_provider['provider']))}</code></p>
            <p>ready：<code>{escape(str(payment_provider['ready']).lower())}</code></p>
            <p>currency：<code>{escape(str(payment_provider['currency']))}</code></p>
            <p>{escape(str(payment_provider['message']))}</p>
          </article>
          <article class="card">
            <h3>Notifications</h3>
            <p>email_provider：<code>{escape(str(notification_providers['email_provider']))}</code></p>
            <p>email_ready：<code>{escape(str(notification_providers['email_ready']).lower())}</code></p>
            <p>line_ready：<code>{escape(str(notification_providers['line_ready']).lower())}</code></p>
            <p>{escape(str(notification_providers['message']))}</p>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>Recommended Commands</h2>
        <div class="grid two">
          <article class="card">
            <h3>PostgreSQL 一鍵 rehearsal</h3>
            <p><code>python3 scripts/cutover_school_platform_postgres.py</code></p>
            <p>會依序跑 initialize、JSON 搬遷、row counts 比對與 PostgreSQL smoke checks。</p>
          </article>
          <article class="card">
            <h3>部署 smoke test</h3>
            <p><code>python3 scripts/smoke_test_school_platform_deployment.py --base-url https://crewai1-api.onrender.com</code></p>
            <p>會檢查 progress、storage、public routes、auth、reports、AI status 與 recruiting API。</p>
          </article>
          <article class="card">
            <h3>PostgreSQL row-level write probe</h3>
            <p><code>python3 scripts/verify_school_platform_postgres_row_writes.py</code></p>
            <p>會對 notifications、ai_logs、assignment_submissions 做 upsert 驗證並自動 cleanup。</p>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>Row-level Mutation Coverage</h2>
        <article class="card">
          <p>以下是目前 PostgreSQL repository 已納入 row-level write 能力的 domain tables：</p>
          <ul class="clean">{mutation_tables}</ul>
        </article>
      </section>
    """
    return _page_shell("系統與資料層狀態", body)


@router.get("/db-migration", response_class=HTMLResponse)
def school_platform_db_migration_page() -> str:
    summary = platform_status_service.storage_summary()
    artifacts = summary["migration_artifacts"]
    mutation_tables = "".join(f"<li><code>{escape(item)}</code></li>" for item in summary["mutation_tables"]) or "<li>尚未啟用 row-level mutation tables</li>"
    body = f"""
      <section class="hero">
        <div class="eyebrow">DB Cutover Runbook</div>
        <h1>DB 切換與資料搬遷說明</h1>
        <p>這頁把 JSON store 切到 PostgreSQL domain tables 的步驟整理成一份正式 runbook，方便工程與營運一起對齊。</p>
      </section>
      <section class="section">
        <h2>切換前檢查</h2>
        <article class="card">
          <ul class="clean">
            <li>確認 <code>SCHOOL_PLATFORM_STORAGE_BACKEND=postgres</code></li>
            <li>確認 <code>SCHOOL_PLATFORM_POSTGRES_DSN</code> 已提供</li>
            <li>確認 <code>psycopg</code> 與 <code>python-multipart</code> 已安裝</li>
            <li>確認 system readiness 中 <code>driver_installed</code>、<code>dsn_present</code>、<code>connectable</code> 狀態</li>
          </ul>
        </article>
      </section>
      <section class="section">
        <h2>執行步驟</h2>
        <div class="grid two">
          <article class="card">
            <h3>1. 初始化 domain tables</h3>
            <p><code>{escape(str(artifacts['init_script']))}</code></p>
            <p>或呼叫 <code>POST /school-platform/api/system/storage/init</code></p>
          </article>
          <article class="card">
            <h3>2. 搬遷 JSON 資料</h3>
            <p><code>{escape(str(artifacts['migrate_script']))}</code></p>
            <p>把目前 JSON store 的資料搬進 PostgreSQL 細表。</p>
          </article>
          <article class="card">
            <h3>3. 一鍵 rehearsal</h3>
            <p><code>{escape(str(artifacts['cutover_script']))}</code></p>
            <p>把 initialize、搬遷、row counts 比對與 PostgreSQL smoke checks 串成單一命令。</p>
          </article>
          <article class="card">
            <h3>4. 驗證 readiness</h3>
            <p>回到 <code>/school-platform/system</code> 查看 <code>tables_ready</code> 與 <code>ready</code>。</p>
          </article>
          <article class="card">
            <h3>5. 切換 backend</h3>
            <p>部署環境把 backend 改成 <code>postgres</code>，再跑 smoke test。</p>
          </article>
          <article class="card">
            <h3>6. 跑 smoke test</h3>
            <p><code>{escape(str(artifacts['smoke_test_script']))}</code></p>
            <p>驗證 courses / leads / student portal 等核心查詢與 readiness 指標。</p>
          </article>
          <article class="card">
            <h3>7. 驗證部署 smoke test</h3>
            <p><code>{escape(str(artifacts['deployment_smoke_script']))}</code></p>
            <p>對 live 或 staging base URL 跑 public / auth / reports / AI / recruiting API smoke checks。</p>
          </article>
          <article class="card">
            <h3>8. 驗證 row-level writes</h3>
            <p><code>{escape(str(artifacts['row_write_probe_script']))}</code></p>
            <p>對 notifications、ai_logs、assignment_submissions 做 upsert probe，確認不需要整包 snapshot rewrite。</p>
          </article>
        </div>
      </section>
      <section class="section">
        <h2>Artifacts</h2>
        <article class="card">
          <p><code>{escape(str(artifacts['sql_domain_tables']))}</code></p>
          <p><code>{escape(str(artifacts['init_script']))}</code></p>
          <p><code>{escape(str(artifacts['migrate_script']))}</code></p>
          <p><code>{escape(str(artifacts['smoke_test_script']))}</code></p>
          <p><code>{escape(str(artifacts['cutover_script']))}</code></p>
          <p><code>{escape(str(artifacts['deployment_smoke_script']))}</code></p>
          <p><code>{escape(str(artifacts['row_write_probe_script']))}</code></p>
        </article>
      </section>
      <section class="section">
        <h2>目前 row-level 覆蓋表</h2>
        <article class="card">
          <ul class="clean">{mutation_tables}</ul>
        </article>
      </section>
    """
    return _page_shell("DB 切換與資料搬遷說明", body)


@router.get("/db-smoke-test", response_class=HTMLResponse)
def school_platform_db_smoke_test_page() -> str:
    checks = platform_status_service.db_smoke_test_checks()
    cards = "".join(
        "<article class='card'>"
        f"<div class='eyebrow'>{'PASS' if item['ok'] else 'CHECK'}</div>"
        f"<h3>{escape(str(item['name']))}</h3>"
        f"<p>{escape(str(item['detail']))}</p>"
        f"<div class='meta'><span class='chip'>{'ok' if item['ok'] else 'pending'}</span></div>"
        "</article>"
        for item in checks
    )
    body = f"""
      <section class="hero">
        <div class="eyebrow">DB Smoke Test</div>
        <h1>DB 切換後 smoke test</h1>
        <p>這頁用來檢查 PostgreSQL domain tables 切換後，平台是否通過最基本的資料層與流程驗證。</p>
        <div class="actions">
          <a class="btn" href="/school-platform/system">回 system 頁</a>
          <a class="btn alt" href="/school-platform/api/system/smoke-test">查看 smoke test JSON</a>
        </div>
      </section>
      <section class="section">
        <div class="grid two">{cards}</div>
      </section>
    """
    return _page_shell("DB 切換後 smoke test", body)


@api_router.get("/health")
def school_platform_health() -> dict[str, str]:
    return platform_status_service.health_payload()


@api_router.get("/progress")
def school_platform_progress() -> dict[str, object]:
    return {"data": platform_status_service.progress_snapshot().model_dump(mode="json"), "error": None}


@api_router.get("/activity")
def school_platform_activity() -> dict[str, object]:
    return {"data": platform_status_service.activity_feed(), "error": None}


@api_router.get("/system/storage")
def school_platform_storage_info() -> dict[str, object]:
    return {"data": platform_status_service.storage_summary(), "error": None}


@api_router.post("/system/storage/init")
def school_platform_storage_init() -> dict[str, object]:
    return {"data": platform_status_service.initialize_storage(), "error": None}


@api_router.post("/system/storage/cutover")
def school_platform_storage_cutover() -> dict[str, object]:
    return {"data": platform_status_service.cutover_storage(), "error": None}


@api_router.get("/system/smoke-test")
def school_platform_storage_smoke_test() -> dict[str, object]:
    return {"data": platform_status_service.db_smoke_test_checks(), "error": None}


@api_router.post("/auth/login")
def auth_login(payload: AuthLoginRequest) -> dict[str, object]:
    return {"data": auth_service.authenticate(payload.email, payload.password).model_dump(mode="json"), "error": None}


@api_router.post("/auth/logout")
def auth_logout(token: str = Depends(current_token)) -> dict[str, object]:
    auth_service.logout(token)
    return {"data": {"success": True}, "error": None}


@api_router.get("/auth/me")
def auth_me(user=Depends(get_current_user)) -> dict[str, object]:
    return {
        "data": {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "permissions": user.permissions,
            "staff_id": str(user.staff_id) if user.staff_id else None,
        },
        "error": None,
    }


@api_router.get("/public/home")
def public_home() -> dict[str, object]:
    return {"data": catalog_service.home_payload().model_dump(mode="json"), "error": None}


@api_router.get("/public/courses")
def public_courses() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in catalog_service.list_courses()], "error": None}


@api_router.get("/public/courses/{slug}")
def public_course_detail(slug: str) -> dict[str, object]:
    try:
        return {"data": catalog_service.get_course(slug).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Course not found: {slug}") from exc


@api_router.get("/public/courses/{slug}/classes")
def public_course_classes(slug: str) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in catalog_service.classes_for_course(slug)], "error": None}


@api_router.get("/public/trial-slots")
def public_trial_slots(course_slug: str | None = Query(default=None)) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in public_admissions_service.trial_slots(course_slug)], "error": None}


@api_router.post("/public/trial-bookings")
def public_trial_booking(payload: TrialBookingCreate) -> dict[str, object]:
    return {"data": public_admissions_service.create_trial_booking(payload).model_dump(mode="json"), "error": None}


@api_router.get("/public/classes/open")
def public_open_classes() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in catalog_service.open_classes()], "error": None}


@api_router.get("/public/jobs")
def public_jobs() -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in recruiting_service.list_jobs(status="open")], "error": None}


@api_router.post("/public/applicants")
def public_create_applicant(payload: ApplicantCreateRequest) -> dict[str, object]:
    try:
        return {"data": recruiting_service.create_applicant(payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@api_router.post("/public/enrollments")
def public_create_enrollment(payload: EnrollmentCreate) -> dict[str, object]:
    try:
        return {"data": finance_service.create_enrollment(payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Class not found") from exc


@api_router.post("/public/payments/create-intent")
def public_create_payment_intent(payload: PaymentIntentCreate) -> dict[str, object]:
    try:
        return {"data": finance_service.create_payment_intent(payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Enrollment not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@api_router.get("/admin/dashboard")
def admin_dashboard(user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    return {"data": admissions_service.dashboard_metrics().model_dump(mode="json"), "error": None}


@api_router.get("/reports/overview")
def reports_overview(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": analytics_service.report_overview().model_dump(mode="json"), "error": None}


@api_router.get("/reports/weekly-summary")
def reports_weekly_summary(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    summary = analytics_service.weekly_ai_summary()
    return {
        "data": {
            **summary,
            "generated_at": summary["generated_at"].isoformat() if hasattr(summary["generated_at"], "isoformat") else summary["generated_at"],
        },
        "error": None,
    }


@api_router.get("/leads")
def list_leads(status: str | None = Query(default=None), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in admissions_service.list_leads(status)], "error": None}


@api_router.get("/leads/{lead_id}")
def lead_detail(lead_id: UUID, user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": admissions_service.get_lead(lead_id).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc


@api_router.get("/leads/{lead_id}/logs")
def lead_logs(lead_id: UUID, user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in admissions_service.logs_for_lead(lead_id)], "error": None}


@api_router.post("/leads/{lead_id}/logs")
def create_lead_log(lead_id: UUID, payload: LeadLogCreate, user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        log = lead_workflow_service.add_log(lead_id, payload.staff_name, payload.contact_method, payload.content, payload.next_action)
        return {"data": log.model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc


@api_router.post("/leads/{lead_id}/assign")
def assign_lead(lead_id: UUID, payload: LeadAssignmentRequest, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    try:
        return {"data": lead_workflow_service.assign_lead(lead_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead or staff not found") from exc


@api_router.post("/leads/{lead_id}/change-status")
def change_lead_status(lead_id: UUID, payload: LeadStatusChangeRequest, user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": lead_workflow_service.change_status(lead_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc


@api_router.get("/courses")
def admin_courses(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in catalog_service.list_courses()], "error": None}


@api_router.post("/courses")
def create_course(payload: CourseUpsertRequest, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": curriculum_admin_service.create_course(payload).model_dump(mode="json"), "error": None}


@api_router.patch("/courses/{slug}")
def update_course(slug: str, payload: CourseUpsertRequest, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    try:
        return {"data": curriculum_admin_service.update_course(slug, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc


@api_router.get("/classes")
def admin_classes(user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in catalog_service.open_classes()], "error": None}


@api_router.post("/classes")
def create_class(payload: ClassUpsertRequest, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    try:
        return {"data": curriculum_admin_service.create_class(payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Course not found") from exc


@api_router.patch("/classes/{class_id}")
def update_class(class_id: UUID, payload: ClassUpsertRequest, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    try:
        return {"data": curriculum_admin_service.update_class(class_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Class or course not found") from exc


@api_router.get("/assignments")
def admin_assignments(class_id: UUID | None = Query(default=None), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in teaching_ops_service.list_assignments(class_id)], "error": None}


@api_router.post("/assignments")
def create_assignment(payload: AssignmentCreateRequest, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": teaching_ops_service.create_assignment(payload).model_dump(mode="json"), "error": None}


@api_router.post("/assignments/submissions/{submission_id}/grade")
def grade_assignment_submission(
    submission_id: UUID,
    payload: SubmissionGradeRequest,
    user=Depends(require_roles("super_admin", "manager")),
) -> dict[str, object]:
    try:
        return {"data": teaching_ops_service.grade_assignment_submission(submission_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Assignment submission not found") from exc


@api_router.get("/attendance")
def admin_attendance(
    student_email: str | None = Query(default=None),
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    if student_email:
        try:
            return {"data": [item.model_dump(mode="json") for item in teaching_ops_service.student_attendance(student_email)], "error": None}
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Student not found") from exc
    return {"data": [], "error": None}


@api_router.post("/attendance")
def create_attendance(payload: AttendanceMarkRequest, user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": teaching_ops_service.mark_attendance(payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.get("/exams")
def admin_exams(class_id: UUID | None = Query(default=None), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in teaching_ops_service.list_exams(class_id)], "error": None}


@api_router.post("/exams")
def create_exam(payload: ExamCreateRequest, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": teaching_ops_service.create_exam(payload).model_dump(mode="json"), "error": None}


@api_router.post("/exams/submissions/{submission_id}/grade")
def grade_exam_submission(
    submission_id: UUID,
    payload: SubmissionGradeRequest,
    user=Depends(require_roles("super_admin", "manager")),
) -> dict[str, object]:
    try:
        return {"data": teaching_ops_service.grade_exam_submission(submission_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Exam submission not found") from exc


@api_router.get("/enrollments")
def admin_enrollments(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in finance_service.list_enrollments()], "error": None}


@api_router.get("/payments")
def admin_payments(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in finance_service.list_payments()], "error": None}


@api_router.get("/finance/overview")
def finance_overview(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    snapshot = finance_service.overview()
    return {
        "data": {
            "summary": snapshot.summary.model_dump(mode="json"),
            "recent_enrollments": [item.model_dump(mode="json") for item in snapshot.recent_enrollments],
            "recent_payments": [item.model_dump(mode="json") for item in snapshot.recent_payments],
            "generated_at": snapshot.generated_at.isoformat(),
        },
        "error": None,
    }


@api_router.get("/messages/overview")
def messages_overview(user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    summary = notification_service.summary()
    notifications = admissions_service.list_notifications()[:20]
    return {
        "data": {
            "summary": summary.model_dump(mode="json"),
            "notifications": [item.model_dump(mode="json") for item in notifications],
            "providers": notification_service.provider_status(),
        },
        "error": None,
    }


@api_router.post("/messages/broadcast")
def messages_broadcast(
    payload: BroadcastMessageRequest,
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        result = notification_service.broadcast(payload)
        return {"data": result.model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="Target email required for single student") from exc


@api_router.get("/admin/executive-dashboard")
def admin_executive_dashboard(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    snapshot = executive_dashboard_service.snapshot()
    return {
        "data": {
            "summary": snapshot.summary.model_dump(mode="json"),
            "alerts": [item.model_dump(mode="json") for item in snapshot.alerts],
            "hot_leads": [item.model_dump(mode="json") for item in snapshot.hot_leads],
            "high_risk_students": [item.model_dump(mode="json") for item in snapshot.high_risk_students],
            "class_watchlist": [item.model_dump(mode="json") for item in snapshot.class_watchlist],
            "ai_module_usage": [item.model_dump(mode="json") for item in snapshot.ai_module_usage],
            "recommendations": snapshot.recommendations,
            "generated_at": snapshot.generated_at.isoformat(),
        },
        "error": None,
    }


@api_router.get("/admin/schedule")
def admin_schedule_overview(user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    snapshot = scheduling_service.overview()
    return {
        "data": {
            "summary": snapshot.summary.model_dump(mode="json"),
            "teacher_loads": [item.model_dump(mode="json") for item in snapshot.teacher_loads],
            "classes": [item.model_dump(mode="json") for item in snapshot.classes],
            "conflicts": [item.model_dump(mode="json") for item in snapshot.conflicts],
            "generated_at": snapshot.generated_at.isoformat(),
        },
        "error": None,
    }


@api_router.get("/recruiting/jobs")
def admin_jobs(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in recruiting_service.list_jobs()], "error": None}


@api_router.post("/recruiting/jobs")
def create_job(payload: JobPositionCreateRequest, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": recruiting_service.create_job(payload).model_dump(mode="json"), "error": None}


@api_router.get("/recruiting/applicants")
def admin_applicants(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in recruiting_service.list_applicants()], "error": None}


@api_router.get("/recruiting/onboarding")
def admin_onboarding_records(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in recruiting_service.list_onboarding_records()], "error": None}


@api_router.get("/recruiting/applicants/{applicant_id}")
def admin_applicant_detail(applicant_id: UUID, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    try:
        snapshot = recruiting_service.applicant_detail(applicant_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Applicant not found") from exc
    return {
        "data": {
            "applicant": snapshot.applicant.model_dump(mode="json"),
            "position": snapshot.position.model_dump(mode="json"),
            "interviews": [item.model_dump(mode="json") for item in snapshot.interviews],
            "evaluation": snapshot.evaluation.model_dump(mode="json"),
            "onboarding": snapshot.onboarding.model_dump(mode="json") if snapshot.onboarding else None,
            "generated_at": snapshot.generated_at.isoformat(),
        },
        "error": None,
    }


@api_router.patch("/recruiting/applicants/{applicant_id}/status")
def update_applicant_status(
    applicant_id: UUID,
    payload: ApplicantStatusUpdateRequest,
    user=Depends(require_roles("super_admin", "manager")),
) -> dict[str, object]:
    try:
        return {"data": recruiting_service.update_applicant_status(applicant_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Applicant not found") from exc


@api_router.put("/recruiting/applicants/{applicant_id}/onboarding")
def upsert_onboarding_record(
    applicant_id: UUID,
    payload: OnboardingUpsertRequest,
    user=Depends(require_roles("super_admin", "manager")),
) -> dict[str, object]:
    try:
        return {"data": recruiting_service.upsert_onboarding_record(applicant_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Applicant not found") from exc


@api_router.post("/recruiting/interviews")
def create_interview(payload: InterviewCreateRequest, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    try:
        return {"data": recruiting_service.schedule_interview(payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Applicant not found") from exc


@api_router.patch("/recruiting/interviews/{interview_id}")
def update_interview(
    interview_id: UUID,
    payload: InterviewUpdateRequest,
    user=Depends(require_roles("super_admin", "manager")),
) -> dict[str, object]:
    try:
        return {"data": recruiting_service.update_interview(interview_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Interview not found") from exc


@api_router.post("/payments/webhook")
def payments_webhook(payload: PaymentWebhookPayload) -> dict[str, object]:
    try:
        return {"data": finance_service.apply_payment_webhook(payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Payment not found") from exc


@api_router.post("/payments/stripe/webhook")
async def payments_stripe_webhook(request: Request) -> dict[str, object]:
    payload = await request.body()
    signature_header = request.headers.get("stripe-signature")
    try:
        result = finance_service.apply_stripe_webhook(payload, signature_header)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Payment not found for webhook") from exc
    if isinstance(result.get("payment"), BaseModel):
        result = {**result, "payment": result["payment"].model_dump(mode="json")}
    return {"data": result, "error": None}


@api_router.get("/staff")
def admin_staff(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in admissions_service.list_staff()], "error": None}


@api_router.get("/notifications")
def admin_notifications(user_email: str | None = Query(default=None), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in admissions_service.list_notifications(user_email)], "error": None}


@api_router.post("/notifications")
def create_notification(payload: NotificationCreate, user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": notification_service.create_notification(payload).model_dump(mode="json"), "error": None}


@api_router.post("/messages/drain")
def api_messages_drain(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in notification_service.drain_queued_notifications()], "error": None}


@api_router.post("/notifications/{notification_id}/status")
def update_notification_status(
    notification_id: UUID,
    payload: NotificationStatusUpdateRequest,
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        return {"data": notification_service.update_status(notification_id, payload.status).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Notification not found") from exc


@api_router.get("/support-inbox")
def api_support_inbox(user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    return {
        "data": {
            "summary": admissions_service.support_inbox_summary(),
            "items": [item.model_dump(mode="json") for item in admissions_service.support_inbox()],
        },
        "error": None,
    }


@api_router.post("/support-inbox/{notification_id}/reply")
def api_support_reply(
    notification_id: UUID,
    payload: SupportReplyRequest,
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        result = student_support_service.process_support_request(
            notification_id,
            payload.status,
            payload.response_message,
            payload.response_channel,
        )
        return {
            "data": {key: value.model_dump(mode="json") for key, value in result.items()},
            "error": None,
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Support request not found") from exc


@api_router.get("/student/dashboard")
def student_dashboard(email: str = Query(...), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": student_portal_service.student_dashboard(email).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.get("/student/courses")
def student_courses(email: str = Query(...), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": [item.model_dump(mode="json") for item in student_portal_service.student_classes(email)], "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.get("/student/assignments")
def student_assignments(email: str = Query(...), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": [item.model_dump(mode="json") for item in teaching_ops_service.student_assignments(email)], "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.post("/student/assignments/{assignment_id}/submit")
def submit_student_assignment(
    assignment_id: UUID,
    payload: AssignmentSubmissionCreateRequest,
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        return {"data": teaching_ops_service.submit_assignment(assignment_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Assignment or student not found") from exc


@api_router.get("/student/attendance")
def student_attendance(email: str = Query(...), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": [item.model_dump(mode="json") for item in teaching_ops_service.student_attendance(email)], "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.get("/student/progress")
def student_progress(email: str = Query(...), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": teaching_ops_service.student_progress(email).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.get("/student/exams")
def student_exams(email: str = Query(...), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": [item.model_dump(mode="json") for item in teaching_ops_service.student_exams(email)], "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.get("/student/ai-practice")
def student_ai_practice(
    email: str = Query(...),
    theme: str = Query(default="藥局與購物生活會話"),
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        return {"data": ai_assistant_service.practice_conversation(email, theme).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.post("/student/exams/{exam_id}/submit")
def submit_student_exam(
    exam_id: UUID,
    payload: ExamSubmissionCreateRequest,
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        return {"data": teaching_ops_service.submit_exam(exam_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Exam or student not found") from exc


@api_router.get("/student/payments")
def student_payments(email: str = Query(...), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": [item.model_dump(mode="json") for item in student_portal_service.student_payments(email)], "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.get("/student/notifications")
def student_notifications(email: str = Query(...), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": [item.model_dump(mode="json") for item in student_portal_service.student_notifications(email)], "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc


@api_router.get("/admin/student-progress")
def admin_student_progress(user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in teaching_ops_service.student_progress_overview()], "error": None}


@api_router.get("/admin/students")
def admin_students(user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    snapshot = student_admin_service.overview()
    return {
        "data": {
            "summary": snapshot.summary.model_dump(mode="json"),
            "items": [item.model_dump(mode="json") for item in snapshot.items],
            "generated_at": snapshot.generated_at.isoformat(),
        },
        "error": None,
    }


@api_router.get("/admin/students/detail")
def admin_student_detail(
    email: str = Query(...),
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        snapshot = student_admin_service.detail(email)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Student not found") from exc
    return {
        "data": {
            "item": snapshot.item.model_dump(mode="json"),
            "classes": [item.model_dump(mode="json") for item in snapshot.classes],
            "enrollments": [item.model_dump(mode="json") for item in snapshot.enrollments],
            "payments": [item.model_dump(mode="json") for item in snapshot.payments],
            "notifications": [item.model_dump(mode="json") for item in snapshot.notifications],
            "history": [item.model_dump(mode="json") for item in snapshot.history],
            "generated_at": snapshot.generated_at.isoformat(),
        },
        "error": None,
    }


@api_router.get("/admin/staff-performance")
def admin_staff_performance(user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    overview = staff_ops_service.performance_overview()
    return {
        "data": {
            "summary": overview["summary"].model_dump(mode="json"),
            "items": [item.model_dump(mode="json") for item in overview["items"]],
        },
        "error": None,
    }


@api_router.get("/consultant/dashboard")
def consultant_dashboard(
    staff_name: str = Query(...),
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    snapshot = consultant_workspace_service.dashboard(staff_name)
    return {
        "data": {
            "summary": snapshot.summary.model_dump(mode="json"),
            "hot_leads": [item.model_dump(mode="json") for item in snapshot.hot_leads],
            "follow_up_queue": [item.model_dump(mode="json") for item in snapshot.follow_up_queue],
            "recently_updated": [item.model_dump(mode="json") for item in snapshot.recently_updated],
            "generated_at": snapshot.generated_at.isoformat(),
        },
        "error": None,
    }


@api_router.get("/consultant/leads/{lead_id}")
def consultant_lead_detail(
    lead_id: UUID,
    staff_name: str = Query(...),
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        snapshot = consultant_workspace_service.lead_detail(staff_name, lead_id)
        snapshot = snapshot.model_copy(update={"followup_draft": ai_assistant_service.followup_draft(lead_id)})
        return {"data": snapshot.model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Consultant lead not found") from exc


@api_router.post("/ai/leads/{lead_id}/followup-draft")
def ai_followup_draft(lead_id: UUID, user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    try:
        return {"data": ai_assistant_service.followup_draft(lead_id).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Lead not found") from exc


@api_router.post("/ai/lesson-plan-draft")
def ai_lesson_plan_draft(
    payload: LessonPlanDraftRequest,
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        return {"data": ai_assistant_service.lesson_plan_draft(payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Class not found") from exc


@api_router.get("/ai/logs")
def ai_logs(module_name: str | None = Query(default=None), user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": [item.model_dump(mode="json") for item in analytics_service.ai_logs(module_name)], "error": None}


@api_router.get("/ai/status")
def ai_status(user=Depends(require_roles("super_admin", "manager"))) -> dict[str, object]:
    return {"data": ai_assistant_service.provider_status().model_dump(mode="json"), "error": None}


@api_router.get("/teaching/session-records")
def teaching_session_records(
    class_id: UUID | None = Query(default=None),
    teacher_name: str | None = Query(default=None),
    approval_status: str | None = Query(default=None),
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    items = teaching_ops_service.list_teaching_session_records(class_id, teacher_name, approval_status)
    return {"data": [item.model_dump(mode="json") for item in items], "error": None}


@api_router.post("/teaching/session-records")
def create_teaching_session_record(
    payload: TeachingSessionUpsertRequest,
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        return {"data": teaching_ops_service.upsert_teaching_session_record(payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Class not found") from exc


@api_router.patch("/teaching/session-records/{record_id}/review")
def review_teaching_session_record(
    record_id: UUID,
    payload: TeachingSessionReviewRequest,
    user=Depends(require_roles("super_admin", "manager")),
) -> dict[str, object]:
    try:
        return {"data": teaching_ops_service.review_teaching_session_record(record_id, payload).model_dump(mode="json"), "error": None}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Teaching session record not found") from exc


@api_router.get("/teacher/dashboard")
def teacher_dashboard(teacher_name: str = Query(...), user=Depends(require_roles("super_admin", "manager", "consultant"))) -> dict[str, object]:
    dashboard = teacher_workspace_service.dashboard(teacher_name)
    return {
        "data": {
            "teacher_name": dashboard["teacher_name"],
            "summary": dashboard["summary"],
            "classes": [item.model_dump(mode="json") for item in dashboard["classes"]],
            "assignments": [item.model_dump(mode="json") for item in dashboard["assignments"]],
            "exams": [item.model_dump(mode="json") for item in dashboard["exams"]],
            "session_records": [item.model_dump(mode="json") for item in dashboard["session_records"]],
            "pending_assignment_reviews": [item.model_dump(mode="json") for item in dashboard["pending_assignment_reviews"]],
            "pending_exam_reviews": [item.model_dump(mode="json") for item in dashboard["pending_exam_reviews"]],
        },
        "error": None,
    }


@api_router.get("/teacher/classes/{class_id}")
def teacher_class_detail(
    class_id: UUID,
    teacher_name: str = Query(...),
    user=Depends(require_roles("super_admin", "manager", "consultant")),
) -> dict[str, object]:
    try:
        snapshot = teacher_workspace_service.class_snapshot(teacher_name, class_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Teacher class not found") from exc
    return {
        "data": {
            "class_item": snapshot.class_item.model_dump(mode="json"),
            "summary": snapshot.summary.model_dump(mode="json"),
            "roster": [item.model_dump(mode="json") for item in snapshot.roster],
            "assignments": [item.model_dump(mode="json") for item in snapshot.assignments],
            "exams": [item.model_dump(mode="json") for item in snapshot.exams],
            "attendance_records": [item.model_dump(mode="json") for item in snapshot.attendance_records],
            "assignment_submissions": [item.model_dump(mode="json") for item in snapshot.assignment_submissions],
            "exam_submissions": [item.model_dump(mode="json") for item in snapshot.exam_submissions],
            "session_records": [item.model_dump(mode="json") for item in snapshot.session_records],
            "generated_at": snapshot.generated_at.isoformat(),
        },
        "error": None,
    }


router.include_router(api_router)
