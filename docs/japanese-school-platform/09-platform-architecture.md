# Platform Architecture

這份文件把 AI 日語補習班完整營運平台整理成工程可落地的系統架構。它不是行銷簡報，而是給產品、前端、後端、資料與營運一起對齊的底稿。

## 1. Platform Scope

平台同時包含 5 條主線：

1. 公開招生站
2. 招生 CRM 與營運後台
3. 教務與學員系統
4. 員工與招聘管理
5. AI 助理與數據決策層

這代表系統不能只看網站頁面，而要從 domain、資料流、權限、事件與報表一起規劃。

## 2. Domain Architecture

### 2.1 Public Growth Domain

負責流量轉換與前台招生活動。

核心模組：

- 品牌首頁
- 課程總覽 / 課程詳情
- 試聽預約
- 線上報名
- FAQ / 見證 / 招聘頁
- AI 課程推薦與招生聊天視窗

核心資料：

- `courses`
- `classes`
- `trial_bookings`
- `leads`
- `enrollments`

### 2.2 CRM / Admissions Domain

負責把外部流量變成名單，再變成報名與成交。

核心模組：

- lead list
- lead detail
- lead assignment
- lead logs
- trial follow-up
- conversion dashboard

核心資料：

- `leads`
- `lead_logs`
- `staff`
- `notifications`
- `ai_logs`

### 2.3 Teaching Operations Domain

負責課程、班級、教師、學員進度與教務執行。

核心模組：

- 課程管理
- 班級管理
- 排課
- 出缺勤
- 作業 / 測驗
- 教師工作台
- 學員中心

核心資料：

- `courses`
- `course_modules`
- `classes`
- `teachers`
- `students`
- `attendance`
- `assignments`
- `assignment_submissions`
- `exams`
- `exam_results`

### 2.4 People Operations Domain

負責員工、顧問、行政與招聘。

核心模組：

- 員工管理
- KPI / performance
- 招聘職缺
- 履歷收件
- 面試流程

核心資料：

- `users`
- `staff`
- `job_positions`
- `applicants`
- `interviews`

### 2.5 Finance & Decision Domain

負責付款、營收、報表與決策。

核心模組：

- 訂單 / 付款
- 收款狀態追蹤
- 營運 dashboard
- ROI / conversion 分析
- 主管週報 / 月報

核心資料：

- `enrollments`
- `payments`
- `notifications`
- `ai_logs`
- 彙總報表 materialized views

## 3. System Layers

### Layer 1: Presentation Layer

包含所有使用者可見介面：

- 公開站
- 學員中心
- 招生顧問後台
- 校務管理後台
- 教師工作台

建議實作：

- Next.js app router
- React
- Tailwind CSS
- i18n

### Layer 2: Application API Layer

負責頁面與資料之間的 use case orchestration。

建議 API 群組：

- `/public/*`
- `/auth/*`
- `/student/*`
- `/leads/*`
- `/courses/*`
- `/classes/*`
- `/payments/*`
- `/notifications/*`
- `/staff/*`
- `/admin/*`
- `/ai/*`

建議責任：

- 驗證 payload
- RBAC
- transaction orchestration
- webhook handling
- audit logging

### Layer 3: Domain Service Layer

把業務規則從 route handler 拉出來。

建議 service：

- `LeadService`
- `CourseService`
- `ClassService`
- `EnrollmentService`
- `PaymentService`
- `NotificationService`
- `StudentPortalService`
- `ReportService`
- `AIOrchestratorService`

### Layer 4: Persistence Layer

負責資料存取與查詢分離。

建議 repository：

- `UserRepository`
- `LeadRepository`
- `CourseRepository`
- `ClassRepository`
- `EnrollmentRepository`
- `PaymentRepository`
- `NotificationRepository`
- `StaffRepository`

目前 repo 內已先用 JSON repository 驗證流程，下一步再切 PostgreSQL。

### Layer 5: Async / Integration Layer

負責所有不適合同步 request 的任務。

建議工作：

- 寄送 email / LINE
- AI 產生跟進話術
- AI 教案 / 測驗生成
- payment webhook reconciliation
- dashboard aggregation
- weekly report generation

建議技術：

- Redis
- worker queue
- scheduler / cron

## 4. Role & Permission Architecture

### Core Roles

- `super_admin`
- `manager`
- `consultant`
- `teacher`
- `student`
- `support`

### Permission Model

建議採：

- role-based baseline permissions
- module-scoped fine-grained permissions
- audit trail for writes

範例：

- `leads:read`
- `leads:write`
- `courses:read`
- `courses:write`
- `payments:read`
- `staff:read`
- `reports:read`

## 5. Event Flow Architecture

### 5.1 Lead Lifecycle

1. 訪客從官網或 LINE 進站
2. 建立 `lead`
3. 自動指派顧問
4. 建立通知
5. 顧問新增 `lead_logs`
6. 試聽與報名後轉成 `enrollment`

### 5.2 Enrollment Lifecycle

1. 學員選班並送出報名
2. 建立 `student`
3. 建立 `enrollment`
4. 建立 `payment`
5. webhook 更新付款結果
6. 成功後開通學員中心與通知

### 5.3 Teaching Lifecycle

1. manager 建立課程
2. manager 建立班級
3. teacher 進入班級工作台
4. 發 attendance / assignment / exam
5. student 在 portal 查看與提交
6. dashboard 聚合學習與營運資料

## 6. AI Architecture

### AI Assistant Families

#### Admissions AI

- 推薦課程
- lead heat scoring
- follow-up draft
- source conversion analysis

#### Teaching AI

- 教案草稿
- 題目生成
- 課後摘要
- 弱點分析

#### Operations AI

- 自動提醒
- 班級名冊整理
- KPI 周報
- 招聘摘要

### AI Safety Boundary

AI 不應直接做最終不可逆決策，建議：

- AI 產出 draft
- 人工 review
- 再進行外部發送或狀態變更

需要 audit 的資料：

- prompt summary
- output summary
- actor
- target module
- created_at

## 7. Deployment Architecture

### MVP Topology

- 1 Web app service
- 1 API service
- 1 PostgreSQL
- 1 Redis
- 1 background worker
- 1 object storage bucket

### Runtime Split

- public web pages
- admin APIs
- background jobs
- file storage
- analytics / BI

### Observability

至少要有：

- request logs
- payment webhook logs
- AI action logs
- job retry logs
- admin audit trail

## 8. Recommended Build Sequence

### Step 1

先固定 domain boundary：

- public
- crm
- teaching
- finance
- ai

### Step 2

先把 repository interface 從 JSON store 抽象化。

### Step 3

切 PostgreSQL repository 與 migration。

### Step 4

補前後台 form action 與 auth session integration。

### Step 5

再接通知 sender、AI orchestration、report jobs。

## 9. Current Implementation Mapping

repo 內目前已經落地的部分：

- 公開站課程頁
- 學員中心頁
- 招生後台頁
- 課程 / 班級 / 教師管理頁
- lead 指派 / 跟進 / 狀態更新表單
- 課程 / 班級建立與編輯表單
- auth / RBAC
- payments webhook
- progress / activity pages

目前仍待正式化的部分：

- PostgreSQL repository
- 持久化 migration strategy
- notification sender
- AI worker
- teaching domain 深化
- HR domain UI

