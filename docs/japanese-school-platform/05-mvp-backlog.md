# MVP 開發 Backlog

## 1. 使用方式

這份文件是給產品、設計、前端、後端一起用的 MVP 實作清單。切法原則：

1. 先做能完成招生與報名閉環的功能。
2. 先做高依賴、低爭議的底層模組。
3. AI 功能先做輔助與摘要，不先做高風險全自動決策。

---

## 2. MVP 產品範圍

MVP 只聚焦四個結果：

1. 訪客可以看課程、預約試聽、送出報名。
2. 招生顧問可以管理名單、跟進、安排試聽。
3. 行政可以建立課程與班級、確認付款。
4. 管理者可以看基本轉換與營收概況。

---

## 3. 前端頁面清單

### P0 前台頁面

#### `/`

目的：

- 品牌說明
- 導向課程、試聽、報名
- 放 AI 客服入口

主要區塊：

- Hero
- 課程分類
- 報名流程
- 學員見證
- FAQ
- CTA

依賴 API：

- `GET /api/public/home`
- `GET /api/public/courses/featured`

#### `/courses`

目的：

- 顯示公開課程列表

主要區塊：

- 篩選條件
- 課程卡片
- 課程類型 / 程度標籤

依賴 API：

- `GET /api/public/courses`

#### `/courses/[slug]`

目的：

- 顯示課程詳情與報名入口

主要區塊：

- 課程介紹
- 適合對象
- 課綱
- 師資
- 費用
- 可報名班級
- CTA

依賴 API：

- `GET /api/public/courses/:slug`
- `GET /api/public/courses/:slug/classes`

#### `/trial-booking`

目的：

- 建立試聽預約

主要區塊：

- 課程選擇
- 可預約時段
- 基本資料
- 程度 / 目標
- LINE 綁定選填

依賴 API：

- `GET /api/public/trial-slots`
- `POST /api/public/trial-bookings`

#### `/apply`

目的：

- 建立正式報名與付款流程

主要區塊：

- 學員資料
- 課程 / 班級
- 優惠碼
- 付款資訊
- 完成頁

依賴 API：

- `GET /api/public/classes/open`
- `POST /api/public/enrollments`
- `POST /api/public/payments/create-intent`

#### `/jobs`

目的：

- 顯示職缺列表與應徵入口

依賴 API：

- `GET /api/public/jobs`
- `POST /api/public/applicants`

---

### P0 後台頁面

#### `/admin/login`

目的：

- 員工登入

依賴 API：

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

#### `/admin`

目的：

- 管理者總儀表板

主要區塊：

- 今日新名單
- 本週報名數
- 試聽轉換率
- 待處理事項

依賴 API：

- `GET /api/admin/dashboard`

#### `/admin/leads`

目的：

- 名單總覽與篩選

主要區塊：

- 狀態篩選
- 顧問篩選
- 來源篩選
- 名單表格

依賴 API：

- `GET /api/leads`
- `PATCH /api/leads/:id`
- `POST /api/leads/:id/assign`

#### `/admin/leads/[id]`

目的：

- 查看名單詳情與跟進紀錄

主要區塊：

- 基本資料
- 意向分數
- 跟進時間軸
- 試聽紀錄
- AI 建議話術

依賴 API：

- `GET /api/leads/:id`
- `GET /api/leads/:id/logs`
- `POST /api/leads/:id/logs`
- `POST /api/ai/leads/:id/followup-draft`

#### `/admin/courses`

目的：

- 管理課程

依賴 API：

- `GET /api/courses`
- `POST /api/courses`
- `PATCH /api/courses/:id`

#### `/admin/classes`

目的：

- 管理班級與開班

依賴 API：

- `GET /api/classes`
- `POST /api/classes`
- `PATCH /api/classes/:id`

#### `/admin/enrollments`

目的：

- 查看報名與付款狀態

依賴 API：

- `GET /api/enrollments`
- `PATCH /api/enrollments/:id`
- `GET /api/payments`
- `PATCH /api/payments/:id`

#### `/admin/staff`

目的：

- 帳號與角色維護

依賴 API：

- `GET /api/staff`
- `POST /api/staff`
- `PATCH /api/staff/:id`

---

## 4. 後端 API Backlog

### Epic A：Auth 與權限

#### A-1 登入與 Session

- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

完成條件：

- 可用 email + password 登入
- 回傳角色與基本權限

資料表依賴：

- `users`
- `user_permissions`

#### A-2 Route Guard

- 前台公開 API 與後台 API 分權
- 支援 `admin`、`manager`、`consultant`、`staff`

---

### Epic B：Public Site

#### B-1 公開課程列表

- `GET /api/public/home`
- `GET /api/public/courses`
- `GET /api/public/courses/:slug`
- `GET /api/public/courses/:slug/classes`

資料表依賴：

- `courses`
- `course_modules`
- `classes`
- `teachers`

#### B-2 試聽預約

- `GET /api/public/trial-slots`
- `POST /api/public/trial-bookings`

完成條件：

- 可建立名單
- 可建立 trial booking
- 可發送確認通知

資料表依賴：

- `leads`
- `trial_bookings`
- `notifications`

#### B-3 正式報名

- `GET /api/public/classes/open`
- `POST /api/public/enrollments`

完成條件：

- 若學員尚未存在，先建立 lead 或 student
- 建立 enrollment 待付款狀態

資料表依賴：

- `students`
- `classes`
- `enrollments`

#### B-4 招聘公開入口

- `GET /api/public/jobs`
- `POST /api/public/applicants`

---

### Epic C：Leads CRM

#### C-1 名單列表

- `GET /api/leads`
- 支援狀態、來源、顧問、日期篩選

#### C-2 名單詳情

- `GET /api/leads/:id`
- `PATCH /api/leads/:id`

#### C-3 跟進紀錄

- `GET /api/leads/:id/logs`
- `POST /api/leads/:id/logs`

#### C-4 指派與狀態流轉

- `POST /api/leads/:id/assign`
- `POST /api/leads/:id/change-status`

#### C-5 試聽整合

- `GET /api/trial-bookings`
- `PATCH /api/trial-bookings/:id`

資料表依賴：

- `leads`
- `lead_logs`
- `trial_bookings`
- `staff`

---

### Epic D：Courses 與 Classes

#### D-1 課程管理

- `GET /api/courses`
- `POST /api/courses`
- `PATCH /api/courses/:id`

#### D-2 課綱章節

- `GET /api/courses/:id/modules`
- `POST /api/courses/:id/modules`
- `PATCH /api/course-modules/:id`

#### D-3 班級管理

- `GET /api/classes`
- `POST /api/classes`
- `PATCH /api/classes/:id`

資料表依賴：

- `courses`
- `course_modules`
- `classes`
- `teachers`

---

### Epic E：Enrollment 與 Payment

#### E-1 報名清單

- `GET /api/enrollments`
- `GET /api/enrollments/:id`
- `PATCH /api/enrollments/:id`

#### E-2 金流建立與回寫

- `POST /api/public/payments/create-intent`
- `POST /api/payments/webhook`
- `GET /api/payments`
- `PATCH /api/payments/:id`

完成條件：

- 建立訂單
- 可接收付款成功 webhook
- 成功後更新 enrollment 狀態

資料表依賴：

- `payments`
- `enrollments`
- `notifications`

---

### Epic F：Dashboard 與報表

#### F-1 管理儀表板

- `GET /api/admin/dashboard`

最小輸出：

- 今日新名單數
- 本週試聽數
- 本週報名數
- 已付款訂單總額
- 待跟進名單數

資料表依賴：

- `leads`
- `trial_bookings`
- `enrollments`
- `payments`

---

### Epic G：AI Assistants

#### G-1 AI 招生話術草稿

- `POST /api/ai/leads/:id/followup-draft`

輸入：

- lead 基本資料
- 最近跟進紀錄

輸出：

- LINE 版話術
- Email 版話術
- 下一步建議

#### G-2 AI 課程推薦

- `POST /api/ai/public/course-recommendation`

輸入：

- 程度
- 目標
- 預計赴日時間

輸出：

- 推薦課程
- 推薦理由

注意：

- MVP 不讓 AI 直接改資料庫，只回傳建議。

---

## 5. 資料表落地優先順序

### Sprint 1 必建

- `users`
- `user_permissions`
- `staff`
- `courses`
- `classes`
- `leads`
- `lead_logs`
- `trial_bookings`

### Sprint 2 必建

- `students`
- `enrollments`
- `payments`
- `notifications`

### Sprint 3 可補

- `course_modules`
- `teachers`
- `job_positions`
- `applicants`
- `ai_logs`

---

## 6. 非同步任務 Backlog

### Job-1 試聽預約確認通知

觸發：

- 建立 `trial_booking` 後

動作：

- 寄送 Email
- 發送 LINE
- 建立站內通知

### Job-2 跟進提醒

觸發：

- 每日排程掃描 `next_follow_up_at`

動作：

- 提醒顧問今日待跟進名單

### Job-3 付款成功通知

觸發：

- 金流 webhook 成功

動作：

- 更新付款狀態
- 發送報名成功通知

### Job-4 AI 話術生成

觸發：

- 顧問在名單頁手動點擊

動作：

- 寫入 `ai_logs`
- 回傳跟進草稿

---

## 7. Sprint 切分建議

## Sprint 1：可收名單

目標：

- 官網可上線
- 可建立 lead
- 後台可看名單

前端：

- 首頁
- 課程列表
- 課程詳情
- 試聽預約表單
- 管理登入頁
- 名單列表頁

後端：

- auth
- public courses
- public trial booking
- leads CRUD 基礎版

驗收：

- 訪客可預約試聽
- 後台可看到名單與狀態

## Sprint 2：可完成報名付款

目標：

- 學員可正式報名
- 行政可追付款

前端：

- 報名頁
- 後台 enrollments 頁
- payments 頁

後端：

- enrollments
- payments
- 通知任務
- dashboard 基礎版

驗收：

- 報名後可生成訂單
- 付款成功會更新狀態

## Sprint 3：可營運追蹤

目標：

- 顧問與主管開始用得起來

前端：

- lead 詳情頁
- dashboard
- staff 管理頁

後端：

- lead logs
- assign lead
- AI followup draft
- dashboard metrics

驗收：

- 顧問可寫跟進紀錄
- 主管可看基本營運數字

---

## 8. 設計稿優先順序

設計不用一次全畫，先畫這 8 張就夠：

1. 首頁
2. 課程總覽
3. 課程詳情
4. 試聽預約表單
5. 報名付款頁
6. 管理登入頁
7. 名單列表頁
8. 名單詳情頁

---

## 9. 工程分工建議

### 前端工程

- 公開網站頁面
- 表單流程
- 後台列表與詳情頁
- 權限導頁

### 後端工程

- auth / RBAC
- leads / enrollments / payments API
- dashboard aggregation
- queue jobs

### 設計

- 公開站視覺
- 表單 UX
- 後台資訊密度與狀態標籤

### PM / 營運

- 課程內容
- 名單狀態規則
- 通知文案
- AI 話術審稿規則

---

## 10. 驗收清單

### 業務驗收

- 訪客從首頁到送出試聽不超過 3 分鐘。
- 顧問可在 1 分鐘內找到新名單並開始跟進。
- 行政可清楚區分未付款、已付款、取消報名。

### 技術驗收

- 後台 API 都需權限控管。
- 金流 webhook 要可重送且不重複入帳。
- 所有通知要保留發送狀態。
- 所有名單狀態變更要可追溯。

### AI 驗收

- AI 話術輸出需附推薦理由。
- AI 推薦課程不可直接替代人工確認。
- AI 操作需保留記錄。
