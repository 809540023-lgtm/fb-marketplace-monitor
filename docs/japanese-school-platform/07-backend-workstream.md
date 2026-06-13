# Backend Workstream

## 1. 目的

這份文件定義 AI 日語補習班營運平台的 MVP 後端執行方式。原則是先做成可穩定上線的「模組化單體後端」，把招生、報名、課程、通知、AI 輔助與報表的核心能力先收斂在同一個服務邊界內，避免第一版就陷入過度微服務化。

---

## 2. 後端總體策略

### 2.1 MVP 架構選擇

建議第一版採用：

- `NestJS` 作為主要 API 後端
- `PostgreSQL` 作為主資料庫
- `Redis` 作為 queue、cache、rate limit 與短期狀態儲存
- `Worker process` 負責通知、AI 摘要、同步 webhook、排程任務

理由：

1. 後台模組多，NestJS 的 module / provider 邊界清楚。
2. RBAC、guard、pipe、scheduler 與 webhook 驗證較容易標準化。
3. MVP 階段先不要切成多個獨立微服務，避免部署與觀測成本過高。

### 2.2 服務邊界

MVP 先分成 4 個 runtime 邊界：

- `api`
  對外 HTTP API，承接前台、學員端、員工端、管理端。
- `worker`
  非同步任務處理，包含通知、AI 草稿、報表匯總、重試。
- `scheduler`
  定時任務入口，可與 worker 合併執行，但概念上獨立。
- `webhook receiver`
  金流、LINE、第三方通知事件入口，實作上可直接掛在 `api` 中，但需獨立 module 與 log。

### 2.3 不在 MVP 切出的服務

第一版先不拆：

- 獨立 AI service
- 獨立通知 service
- 獨立報表 service
- 獨立搜尋 service

這些都先以模組方式存在，等量體變大再拆。

---

## 3. Backend Module Map

### 3.1 `auth` module

責任：

- 登入
- 登出
- session / JWT 管理
- refresh token
- 密碼重設
- email OTP

對應路由：

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `POST /api/auth/refresh`
- `POST /api/auth/request-reset`
- `POST /api/auth/reset-password`

### 3.2 `rbac` module

責任：

- role 定義
- permission 定義
- scope 控制
- route guard
- resource guard

核心概念：

- `role`
  管理 admin / manager / consultant / teacher / staff / student。
- `permission`
  管理可執行動作，例如 `read_leads`、`edit_courses`、`manage_payments`。
- `scope`
  控制資料可見範圍，例如 `self`、`assigned`、`branch`、`all`。

### 3.3 `public-site` module

責任：

- 首頁資料
- 公開課程列表
- 課程詳情
- 試聽預約
- 正式報名
- 職缺列表
- AI 課程推薦入口

### 3.4 `leads` module

責任：

- 名單 CRUD
- 跟進紀錄
- 名單分派
- 狀態流轉
- 試聽預約整合

### 3.5 `students` module

責任：

- 學員檔案
- 學員與報名的關聯
- 學習概況
- 付款與課程資料彙整視圖

### 3.6 `courses` module

責任：

- 課程 CRUD
- 課綱章節
- 公開狀態
- 課程推薦資料

### 3.7 `classes` module

責任：

- 班級 CRUD
- 教師配置
- 報名名額控管
- 班級狀態
- `class_sessions` 生成與維護

### 3.8 `enrollments` module

責任：

- 報名流程
- 學員與班級關聯
- 報名狀態更新
- 優惠碼 / 金額

### 3.9 `payments` module

責任：

- 訂單建立
- 金流付款狀態
- webhook 驗證
- 退款

### 3.10 `notifications` module

責任：

- Email / LINE / in-app 通知
- 模板管理
- 發送狀態
- 重試與失敗紀錄

### 3.11 `ai-assistant` module

責任：

- 招生話術草稿
- 課程推薦
- 教務摘要
- 主管摘要
- 招聘摘要

MVP 原則：

- AI 只提供建議，不直接改核心資料。
- 所有 AI 呼叫都要寫 `ai_logs`。

### 3.12 `staff` module

責任：

- 員工檔案
- 教師檔案
- 主管關係
- KPI 與排班資料

### 3.13 `recruiting` module

責任：

- 職缺
- 應徵者
- 面試流程
- 錄取結果

### 3.14 `analytics` module

責任：

- 管理 dashboard
- 招生漏斗
- 報名轉換率
- 課程滿班率
- 基礎營收指標

### 3.15 `audit` module

責任：

- 操作記錄
- AI 記錄
- 付款與 webhook 記錄
- 權限變更記錄

---

## 4. API Design Rules

### 4.1 API 分層

每個 domain 固定分成 4 類：

- `list`
- `detail`
- `create/update`
- `actions`

例子：

- `GET /api/leads`
- `GET /api/leads/:id`
- `POST /api/leads`
- `POST /api/leads/:id/assign`

### 4.2 回傳格式

建議統一：

```json
{
  "data": {},
  "meta": {},
  "error": null
}
```

列表回傳可加：

- `page`
- `pageSize`
- `total`
- `sort`
- `filters`

### 4.3 錯誤格式

統一使用：

- `code`
- `message`
- `details`
- `requestId`

這樣 webhook、worker 與 API log 可以共用錯誤字典。

---

## 5. Auth and RBAC

### 5.1 登入方式

MVP 先支援：

- email + password
- session cookie 或 short-lived JWT
- refresh token

第二階段再加：

- email OTP
- Google login
- LINE login

### 5.2 角色建議

- `super_admin`
- `manager`
- `consultant`
- `teacher`
- `staff`
- `student`

### 5.3 權限原則

建議先定義以下 permission groups：

- `read_public`
- `manage_leads`
- `manage_courses`
- `manage_classes`
- `manage_enrollments`
- `manage_payments`
- `manage_staff`
- `manage_recruiting`
- `view_reports`
- `run_ai_assistant`

### 5.4 Scope 規則

scope 是 MVP 很重要的安全層：

- `self`
  只能看自己資料。
- `assigned`
  只能看指派給自己的名單或班級。
- `branch`
  只能看所屬校區資料。
- `all`
  全站可見。

### 5.5 需要寫入 audit 的動作

- 登入失敗多次
- 權限變更
- 名單狀態流轉
- 顧問分派
- 金流狀態變更
- 退款
- AI 建議採用或拒絕

---

## 6. Queue Jobs

### 6.1 任務分類

#### 即時任務

- 登入
- 公開查詢
- 報名送出
- webhook 接收

#### 非同步任務

- 通知發送
- AI 草稿生成
- 報表彙總
- 跟進提醒
- 付款同步

#### 排程任務

- 每日跟進提醒
- 每日未付款提醒
- 每週 KPI 摘要
- 每日 dashboard 數據刷新

### 6.2 必做 jobs

#### `send-trial-booking-confirmation`

觸發：

- 新試聽預約建立後

動作：

- 寄 Email
- 發 LINE 通知
- 建立站內通知

#### `send-enrollment-confirmation`

觸發：

- 報名建立後

動作：

- 寄送報名成功通知
- 建立學員帳號通知

#### `sync-payment-status`

觸發：

- 金流 webhook

動作：

- 更新 payment
- 更新 enrollment
- 觸發通知

#### `generate-followup-draft`

觸發：

- 顧問手動點擊 AI 建議

動作：

- 呼叫 LLM
- 寫入 `ai_logs`
- 回傳話術草稿

#### `daily-followup-reminder`

觸發：

- 每日排程

動作：

- 列出今日待跟進 leads
- 通知對應顧問

#### `daily-dashboard-refresh`

觸發：

- 每日固定時間

動作：

- 更新基本營運指標
- 預熱 dashboard cache

### 6.3 Job 規則

- job 必須可重試
- job 必須冪等
- job 失敗要進死信或 error table
- job payload 需保留 requestId / actorId / source

---

## 7. Webhook Flows

### 7.1 金流 webhook

主要用途：

- 付款成功
- 付款失敗
- 退款成功

設計要求：

- 驗簽
- 去重
- 支援重送
- 回應要快，不在 webhook request 內做重工作

處理流程：

1. 接收 webhook。
2. 驗證來源與簽章。
3. 查找 `order_no` 或外部 transaction id。
4. 寫入 webhook log。
5. 更新 `payments`。
6. 視狀態更新 `enrollments`。
7. 觸發通知 job。

### 7.2 LINE webhook

主要用途：

- 使用者訊息進站
- AI 客服前置收名單
- 已綁定聯絡方式更新

處理流程：

1. 接收 LINE event。
2. 驗證來源。
3. 判斷是否為已知 lead / student。
4. 建立訊息紀錄。
5. 若符合規則，觸發 AI 回答或轉人工。

### 7.3 Email / notification callback

若供應商有回調：

- delivery
- bounce
- failure

需要把狀態寫回 `notifications`，方便後台查看。

### 7.4 AI 外部回呼

MVP 原則上不需要外部 AI callback，但若使用第三方代理服務，需保留：

- request payload
- model name
- response payload
- usage cost

---

## 8. Runtime and Deployment

### 8.1 Process topology

建議最少部署 2 個進程：

- `api`
- `worker`

如果平台需要排程分離，可再加：

- `scheduler`

### 8.2 Environment Variables

必備：

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `APP_BASE_URL`
- `SUPPORT_EMAIL`

金流：

- `PAYMENT_PROVIDER_KEY`
- `PAYMENT_WEBHOOK_SECRET`

通知：

- `EMAIL_PROVIDER_KEY`
- `LINE_CHANNEL_ACCESS_TOKEN`
- `LINE_CHANNEL_SECRET`

AI：

- `OPENAI_API_KEY`

觀測：

- `SENTRY_DSN`
- `LOG_LEVEL`

### 8.3 Observability

MVP 至少要有：

- request id
- structured logs
- job logs
- webhook logs
- AI logs
- payment logs

建議把以下事件都記錄：

- `auth.login_failed`
- `lead.assigned`
- `trial_booking.created`
- `enrollment.created`
- `payment.webhook_received`
- `payment.paid`
- `ai.followup_generated`

### 8.4 Error handling

後端不要把錯誤直接吐給前端原文。建議：

- 內部錯誤保留完整 stack trace
- 對外回傳友善訊息與 error code
- webhook 和 job 失敗要可重試

### 8.5 Performance considerations

MVP 預先做的性能控制：

- dashboard aggregation 用 cache
- 列表查詢預設分頁
- 搜尋欄位加 index
- webhook 快取驗簽結果只做短時間
- AI 呼叫走 async

---

## 9. Data Ownership Rules

### 9.1 單一資料來源

每個模組有自己的寫入責任：

- `leads` 只能由 leads / public-site / ai-assistant 的授權動作寫入
- `payments` 只能由 payments / webhook 寫入
- `classes` 只能由 admin / staff 寫入
- `students` 只能由 enrollment 成功流程或手動補建流程寫入

### 9.2 不直接跨模組寫表

例如：

- `payments` 成功後，不要在 controller 直接同步改 5 張表。
- 改採 service + domain event + job。

這樣比較容易維護，也更方便之後拆服務。

---

## 10. MVP Delivery Order

### Sprint 1

- auth
- RBAC
- public courses
- trial bookings
- leads CRUD
- basic notifications

### Sprint 2

- courses / classes
- enrollments
- payments
- webhook handling
- dashboard basics

### Sprint 3

- AI assistant
- staff management
- analytics
- audit logs
- recruiting foundation

---

## 11. Implementation Notes

1. 第一版請以「可追蹤、可重試、可審計」為優先，不要追求功能炫技。
2. AI 功能先做輔助，不做強制自動化決策。
3. webhook 與 job 都要 idempotent，避免重送造成重複入帳或重複通知。
4. 若要支援多校區，從第一版就把 `branch_id` 留在主要表的模型規格中。
5. 後端 API 需和前台文案解耦，避免之後改名就要重改程式碼。

---

## 12. Recommended first build package

如果只允許先做一個最小可上線的 backend package，順序是：

1. `auth` + `rbac`
2. `courses` + `classes`
3. `leads` + `trial_bookings`
4. `enrollments` + `payments`
5. `notifications`
6. `analytics`
7. `ai-assistant`

