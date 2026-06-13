# Delivery Plan

這份文件的目的，是把 AI 日語補習班營運平台從產品藍圖轉成可執行的團隊作戰方式。這裡不再討論「要不要做」，而是直接定義「誰負責什麼、先做什麼、怎麼協作、怎麼控風險」。

## 1. Team Structure

### Lead Agent

- 你是總協調與最終決策者。
- 你只看結果、里程碑、風險與例外，不處理日常碎片決策。
- 你負責確認每個 sprint 的輸入與輸出是否對齊產品目標。

### Product / PM

- 負責需求切片、驗收標準、優先序與 scope 控制。
- 把 `04-roadmap-and-prd.md` 與 `05-mvp-backlog.md` 轉成 sprint backlog。
- 維護 issue 優先順序與變更紀錄。

### Design

- 負責首頁、課程頁、報名頁、後台三大頁面群的資訊層級與互動流程。
- 先做低保真 wireframe，再補視覺系統與元件規格。
- 優先處理招生轉換路徑與後台高密度表格的可讀性。

### Frontend Engineering

- 負責公開站、學員中心、員工工作台、管理後台的頁面實作。
- 負責表單流程、權限導頁、列表詳情頁、狀態切換 UI。
- 與 design 對齊元件可重用性與響應式行為。

### Backend Engineering

- 負責 auth / RBAC、CRM、課程班級、報名付款、通知、AI helper API。
- 負責 queue jobs、webhook、audit log、dashboard aggregation。
- 確保資料模型與流程狀態一致。

### QA / Ops

- 負責驗收腳本、測試資料、關鍵流程回歸。
- 先驗證「收名單、試聽、報名、付款、通知」四條主線。
- 追蹤上線後的錯誤與流程漏接。

---

## 2. Role Allocation

### 我方分工原則

1. PM 只負責定義和驗收，不負責臨場救火。
2. Design 只要先鎖住轉換路徑與操作密度，不必一次畫完整站。
3. Frontend 先把流程跑通，再補視覺細節。
4. Backend 先保證資料與事件正確，再做優化與 AI。
5. QA 先盯住關鍵金流與狀態流，不平均用力。

### 建議人力配置

- 1 位 PM
- 1 位 Designer
- 2 位 Frontend
- 2 位 Backend
- 1 位 QA / Ops

如果人力不足，優先保留：

1. 1 PM
2. 1 Designer
3. 1 Frontend
4. 1 Backend
5. 0.5 QA by PM / backend support

---

## 3. Execution Phases

### Phase 0: Setup

目標：

- 先把產品範圍鎖在 MVP。
- 先把資料模型、API domain、頁面清單固定。

輸出：

- `03-data-model.md`
- `04-roadmap-and-prd.md`
- `05-mvp-backlog.md`

### Phase 1: Revenue Capture

目標：

- 先讓網站能接名單、能預約試聽、能送出報名。

重點：

- 公開站首頁與課程頁
- 試聽預約
- 報名流程
- leads CRUD
- basic notifications

### Phase 2: Operations Control

目標：

- 讓招生顧問與行政真的在後台工作。

重點：

- 顧問分派
- 名單跟進紀錄
- 班級管理
- 付款追蹤
- dashboard

### Phase 3: Teaching Support

目標：

- 把教務帶進平台，降低人工整理成本。

重點：

- 學員中心
- 出缺勤
- 作業與測驗
- 教師工作台
- AI 教案草稿

### Phase 4: Management Intelligence

目標：

- 讓主管看數字、看風險、看預測。

重點：

- KPI
- 招生漏斗
- 招聘
- AI 週報 / 月報
- 風險預警

---

## 4. Sprint Ceremonies

### Weekly Cadence

- Monday: sprint planning
- Wednesday: mid-sprint check
- Friday: demo and bug triage
- Daily: short async check-in

### Sprint Planning Inputs

- 上一個 sprint 的完成率
- 產品優先序
- 風險與阻塞項
- 設計與 API 依賴

### Demo Rules

- 只展示可跑通的端到端流程。
- 不接受只完成 UI、沒有資料閉環的項目。
- 每次 demo 都要包含可驗證的資料狀態變化。

### Retro Rules

- 只討論阻礙交付的流程問題。
- 追蹤依賴是否太晚曝光。
- 追蹤是否有 scope creep。

---

## 5. Dependency Sequencing

### Dependency Order

1. 產品邊界與 MVP scope
2. 資料模型
3. Auth / RBAC
4. 公開站內容與課程資料
5. Leads / trial booking
6. Enrollments / payments
7. Admin dashboard
8. Staff / teaching workflows
9. AI helper flows
10. Analytics / reporting

### Hard Dependencies

- 沒有 `users` 和 `user_permissions`，後台權限不能開始。
- 沒有 `courses`、`classes`，前台報名與後台班級無法串起來。
- 沒有 `leads`、`lead_logs`，招生 CRM 無法追蹤。
- 沒有 `enrollments`、`payments`，無法完成營收閉環。
- 沒有 `notifications`，任何提醒與確認都會斷掉。

### Parallelizable Work

- Design 可以先做首頁、課程頁、後台表格頁三條線。
- Frontend 可以先做公開站與後台 shell。
- Backend 可以先做 auth、courses、leads 三個 module。
- QA 可以先寫報名與付款的驗收腳本。

---

## 6. Lead Agent Assignment Model

### 我會怎麼分配工作

#### 給 PM

- 把 backlog 切成 sprint issue。
- 管 scope，避免功能在 sprint 內漂移。
- 定義每個功能的 acceptance criteria。

#### 給 Design

- 先做高轉換頁面與高頻後台頁。
- 先交 wireframe，再交 component spec。
- 先把資料密度高的表格和名單頁處理好。

#### 給 Frontend

- 先做可見頁面，再做帳號與權限頁。
- 先把表單、列表、詳情、狀態標籤這四種模式統一。
- 同步建立可重用元件，避免每頁各寫一套。

#### 給 Backend

- 先把 auth、leads、courses、classes、enrollments 這五組主體打通。
- 先保證 webhook 和 queue job 的可靠性。
- 先把 audit log 與狀態流寫正確。

#### 給 QA / Ops

- 先驗證報名、付款、通知三條最容易壞的鏈路。
- 每個 sprint 都保留回歸測試案例。
- 追蹤哪些流程需要人工備援。

### 我會怎麼控節奏

- 任何會影響資料結構的需求，必須先經過 PM 與 backend 對齊。
- 任何會影響主要轉換流程的 UI 變更，必須先由 design 和 frontend 對齊。
- 任何 AI 功能都先以「建議」形式上線，不直接寫入核心資料。

---

## 7. Risk Register

### Risk 1: Scope Too Large

- 風險：一次想做完招生、教務、員工、招聘、報表，會拖垮交付。
- 對策：MVP 嚴格只保留招生閉環與基礎後台。

### Risk 2: Data Model Drift

- 風險：前後台各自長出不同的欄位與狀態。
- 對策：先固定資料模型與狀態字典，再開始開發。

### Risk 3: Payment or Notification Failure

- 風險：報名成功但付款或通知漏接。
- 對策：金流 webhook、notification job 與 retry 機制先做。

### Risk 4: AI Overreach

- 風險：AI 直接做決策，造成招生、教務或人事誤判。
- 對策：AI 只產生建議與草稿，關鍵動作保留人工確認。

### Risk 5: Role Confusion

- 風險：顧問、行政、主管權限交疊，後台難維護。
- 對策：RBAC + scope 從第一版開始就實作。

### Risk 6: Late Design Handoff

- 風險：前端等設計，或設計等產品定義，造成排程卡住。
- 對策：先做首頁、課程頁、名單頁、後台表格頁四個高頻畫面。

### Risk 7: No Operational Backup

- 風險：系統化後，如果流程失敗就無人工 fallback。
- 對策：為報名、付款、通知、試聽預約保留 manual override。

---

## 8. Operating Rules

1. 任何需求變更都先回到 backlog，不口頭散落到各人。
2. 任何 sprint 都只允許一個主目標。
3. 任何功能只要沒有資料閉環，就不算完成。
4. 任何 AI 功能沒有審計紀錄，就不准進主流程。
5. 任何涉及金流、權限、資料刪除的操作，都要有回滾或補償方案。

---

## 9. First 30 Days

### Week 1

- 固定 MVP scope
- 固定資料模型
- 固定角色與權限
- 完成 wireframe 草圖

### Week 2

- 建立公開站骨架
- 建立 auth 與後台 shell
- 建立 courses / classes / leads 基礎 API

### Week 3

- 串試聽預約
- 串報名與付款
- 完成名單列表與詳情頁

### Week 4

- 完成通知與 dashboard
- 做一次端到端回歸
- 整理下一 sprint 的風險與缺口

---

## 10. Done Definition

### 對前台

- 訪客可以看懂課程。
- 訪客可以預約試聽。
- 訪客可以送出報名。

### 對後台

- 顧問可以追蹤名單。
- 行政可以確認報名與付款。
- 管理者可以看轉換與營收。

### 對團隊

- PM 可以排下一個 sprint。
- Design 可以進入下一批頁面。
- Engineering 可以持續交付，不被臨時需求打亂。
