# AI 日語補習班營運平台

這份文件組把「AI 化日語補習班營運平台」拆成可執行的產品規格，目標不是做單一招生網站，而是做一個可支援招生、教務、行政、員工、招聘、財務與 AI 自動化的完整平台。

## 文件清單

- `01-sitemap-and-ia.md`
  前台、學員端、員工端、管理端的 sitemap 與資訊架構。
- `02-modules-and-roles.md`
  核心模組、角色權限、主要流程與模組邊界。
- `03-data-model.md`
  核心資料表、關聯關係、欄位建議與實作注意事項。
- `04-roadmap-and-prd.md`
  MVP 範圍、分階段開發順序、驗收重點與 PRD 摘要。
- `05-mvp-backlog.md`
  可直接分派給設計、前端、後端與 PM 的 MVP backlog。
- `06-frontend-workstream.md`
  前端路由、頁面責任、共用元件、資料需求與 3 個 Sprint 的前端交付順序。
- `07-backend-workstream.md`
  後端模組邊界、auth/RBAC、queue jobs、webhook 流與 runtime 策略。
- `08-delivery-plan.md`
  團隊分工、sprint cadence、依賴順序、風險控管與交付節奏。
- `09-platform-architecture.md`
  完整平台 domain、system layers、event flow、AI layer 與 deployment architecture。
- `10-storage-migration-readiness.md`
  JSON store 到 PostgreSQL domain tables 的切換、migration artifacts、readiness checklist 與 rollout 順序。
- `11-db-cutover-runbook.md`
  正式 DB cutover 步驟、前置條件、smoke test 與 rollback 手冊。
- `../sql/japanese_school_platform_mvp.sql`
  PostgreSQL MVP schema 草案，可直接作為 migration 起點。

## 產品定位

平台定位為面向「準備赴日生活的華人」的 AI 日語教育與校務管理平台，核心目標：

1. 前台自動招生
2. 後台自動管理
3. AI 協助營運與教學

## 建議技術方向

- 前端：Next.js + React + Tailwind CSS
- 後端：NestJS 或 FastAPI
- 資料庫：PostgreSQL
- 快取 / 任務：Redis + Queue Worker
- 儲存：S3 或 R2
- 驗證：JWT / Session + Email OTP + 第三方登入
- 報表：內建 dashboard + Metabase / Superset

## 建議先做的事

1. 先確認 MVP 只做「招生 CRM + 課程班級管理 + 報名付款 + 基礎通知」。
2. 用 `03-data-model.md` 先建立第一版 schema。
3. 用 `04-roadmap-and-prd.md` 決定 Sprint 切法。
4. 再開始切前端頁面與 API。
