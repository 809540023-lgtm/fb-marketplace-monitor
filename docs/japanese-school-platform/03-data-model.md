# 資料模型與 ER 草案

## 1. 核心實體分組

建議把資料模型分成七組：

1. 身分與權限
2. 招生 CRM
3. 課程與班級
4. 學習與教務
5. 財務
6. 員工與招聘
7. AI 與系統記錄

---

## 2. 核心資料表

### 2.1 身分與權限

#### `users`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| name | varchar | 顯示名稱 |
| email | varchar | 登入信箱 |
| phone | varchar | 手機 |
| password_hash | varchar | 密碼雜湊 |
| role | varchar | 主要角色 |
| status | varchar | active / inactive / suspended |
| locale | varchar | zh-TW / ja-JP |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

#### `user_permissions`

用來支援細粒度權限覆蓋。

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| user_id | uuid | 對應 users |
| permission_key | varchar | 權限代碼 |
| scope | varchar | all / self / assigned / branch |
| created_at | timestamptz | 建立時間 |

---

### 2.2 招生 CRM

#### `leads`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| name | varchar | 姓名 |
| phone | varchar | 手機 |
| email | varchar | 信箱 |
| line_id | varchar | LINE ID |
| source_channel | varchar | 來源渠道 |
| campaign_name | varchar | 廣告活動 |
| interested_course_id | uuid | 感興趣課程 |
| budget_range | varchar | 預算區間 |
| japanese_level | varchar | 程度 |
| study_goal | text | 學習目標 |
| departure_plan_date | date | 預計赴日時間 |
| intent_score | numeric | 意向分數 |
| win_probability | numeric | 成交預測 |
| status | varchar | 名單狀態 |
| assigned_staff_id | uuid | 指派顧問 |
| last_contact_at | timestamptz | 最後聯繫 |
| next_follow_up_at | timestamptz | 下次跟進 |
| notes | text | 備註 |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

#### `lead_logs`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| lead_id | uuid | 對應 leads |
| staff_id | uuid | 操作者 |
| contact_method | varchar | line / call / email / meeting |
| content | text | 跟進內容 |
| next_action | text | 下一步 |
| created_at | timestamptz | 建立時間 |

#### `trial_bookings`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| lead_id | uuid | 對應 lead |
| course_id | uuid | 試聽課程 |
| class_id | uuid | 試聽班級，可空 |
| slot_start_at | timestamptz | 試聽開始 |
| slot_end_at | timestamptz | 試聽結束 |
| status | varchar | booked / completed / canceled / no_show |
| feedback | text | 試聽回饋 |
| created_at | timestamptz | 建立時間 |

---

### 2.3 學員與報名

#### `students`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| user_id | uuid | 對應 users |
| chinese_name | varchar | 中文姓名 |
| english_name | varchar | 英文姓名 |
| japanese_name | varchar | 日文姓名 |
| gender | varchar | 性別 |
| nationality | varchar | 國籍 |
| native_language | varchar | 母語 |
| age_group | varchar | 年齡層 |
| city | varchar | 居住地 |
| japanese_level | varchar | 日語程度 |
| study_goal | text | 學習目標 |
| source_channel | varchar | 來源 |
| consultant_id | uuid | 負責顧問 |
| status | varchar | active / inactive / graduated |
| notes | text | 備註 |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

#### `enrollments`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| student_id | uuid | 對應 student |
| class_id | uuid | 對應 class |
| lead_id | uuid | 對應來源 lead，可空 |
| enrolled_at | timestamptz | 報名時間 |
| status | varchar | pending / active / canceled / completed |
| payment_status | varchar | unpaid / partial / paid / refunded |
| coupon_code | varchar | 優惠碼 |
| list_price | numeric | 原價 |
| paid_amount | numeric | 實付金額 |
| consultant_id | uuid | 經手顧問 |
| created_at | timestamptz | 建立時間 |

---

### 2.4 課程與班級

#### `courses`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| slug | varchar | 前台網址識別 |
| name | varchar | 課程名稱 |
| course_type | varchar | 課程類型 |
| level | varchar | 程度等級 |
| description | text | 課程介紹 |
| objectives | text | 課程目標 |
| total_sessions | integer | 總堂數 |
| session_minutes | integer | 每堂分鐘數 |
| price | numeric | 費用 |
| delivery_mode | varchar | online / offline / hybrid |
| is_public | boolean | 是否公開 |
| created_by | uuid | 建立者 |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

#### `course_modules`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| course_id | uuid | 對應 courses |
| title | varchar | 章節名稱 |
| sort_order | integer | 排序 |
| description | text | 內容說明 |
| material_url | text | 教材連結 |

#### `classes`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| course_id | uuid | 對應課程 |
| name | varchar | 班級名稱 |
| teacher_id | uuid | 對應 teacher |
| start_date | date | 開課日 |
| end_date | date | 結課日 |
| weekday_mask | varchar | 上課星期 |
| start_time | time | 開始時間 |
| end_time | time | 結束時間 |
| capacity | integer | 名額上限 |
| enrolled_count | integer | 已報名數 |
| location_label | varchar | 教室或線上標籤 |
| meeting_url | text | 線上連結 |
| status | varchar | draft / open / full / running / completed |
| created_at | timestamptz | 建立時間 |
| updated_at | timestamptz | 更新時間 |

#### `class_sessions`

把每堂課拆出來，後續才能做點名、補課、作業與教案。

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| class_id | uuid | 對應 classes |
| module_id | uuid | 對應章節，可空 |
| starts_at | timestamptz | 上課開始時間 |
| ends_at | timestamptz | 上課結束時間 |
| teacher_id | uuid | 當堂老師 |
| classroom | varchar | 教室 |
| meeting_url | text | 視訊連結 |
| status | varchar | scheduled / done / canceled / makeup |
| lesson_plan | text | 教案摘要 |

---

### 2.5 教務與學習

#### `attendance`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| class_session_id | uuid | 對應課堂 |
| student_id | uuid | 對應 student |
| status | varchar | present / absent / late / leave |
| notes | text | 備註 |
| created_at | timestamptz | 建立時間 |

#### `assignments`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| class_id | uuid | 對應班級 |
| class_session_id | uuid | 對應課堂，可空 |
| title | varchar | 標題 |
| content | text | 作業內容 |
| due_at | timestamptz | 截止時間 |
| created_by | uuid | 建立者 |
| created_at | timestamptz | 建立時間 |

#### `assignment_submissions`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| assignment_id | uuid | 對應作業 |
| student_id | uuid | 對應 student |
| content | text | 繳交內容 |
| score | numeric | 分數 |
| feedback | text | 回饋 |
| submitted_at | timestamptz | 繳交時間 |

#### `exams`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| class_id | uuid | 對應班級 |
| title | varchar | 測驗名稱 |
| exam_type | varchar | placement / quiz / final |
| total_score | numeric | 滿分 |
| created_by | uuid | 建立者 |
| created_at | timestamptz | 建立時間 |

#### `exam_results`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| exam_id | uuid | 對應測驗 |
| student_id | uuid | 對應學生 |
| score | numeric | 分數 |
| result_level | varchar | 等第 |
| feedback | text | 回饋 |
| created_at | timestamptz | 建立時間 |

---

### 2.6 財務

#### `payments`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| enrollment_id | uuid | 對應報名 |
| order_no | varchar | 訂單號 |
| amount | numeric | 金額 |
| payment_method | varchar | card / transfer / cash / line_pay |
| status | varchar | pending / paid / failed / refunded |
| paid_at | timestamptz | 付款時間 |
| invoice_data | jsonb | 發票資訊 |
| gateway_payload | jsonb | 金流回傳 |
| created_at | timestamptz | 建立時間 |

#### `refunds`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| payment_id | uuid | 對應 payment |
| amount | numeric | 退款金額 |
| reason | text | 原因 |
| status | varchar | pending / processed / rejected |
| created_at | timestamptz | 建立時間 |

---

### 2.7 教師、員工、招聘

#### `teachers`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| user_id | uuid | 對應 users |
| specialties | text | 擅長領域 |
| years_experience | numeric | 年資 |
| available_slots | jsonb | 可授課時段 |
| bio | text | 自介 |
| rating | numeric | 評分 |
| contract_type | varchar | full_time / part_time |
| pay_scheme | varchar | hourly / monthly / by_class |
| created_at | timestamptz | 建立時間 |

#### `staff`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| user_id | uuid | 對應 users |
| department | varchar | 部門 |
| title | varchar | 職稱 |
| manager_id | uuid | 主管 |
| hire_date | date | 到職日 |
| kpi_target | jsonb | KPI 目標 |
| status | varchar | active / leave / probation |
| created_at | timestamptz | 建立時間 |

#### `job_positions`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| title | varchar | 職缺名稱 |
| department | varchar | 部門 |
| description | text | 工作內容 |
| requirements | text | 條件 |
| salary_range | varchar | 薪資範圍 |
| location | varchar | 地點 |
| status | varchar | draft / open / closed |
| created_at | timestamptz | 建立時間 |

#### `applicants`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| position_id | uuid | 對應職缺 |
| name | varchar | 姓名 |
| email | varchar | 信箱 |
| phone | varchar | 手機 |
| resume_url | text | 履歷連結 |
| interview_status | varchar | new / reviewing / scheduled / done |
| ai_match_score | numeric | AI 匹配分數 |
| notes | text | 備註 |
| created_at | timestamptz | 建立時間 |

#### `interviews`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| applicant_id | uuid | 對應 applicant |
| interview_at | timestamptz | 面試時間 |
| interviewer_id | uuid | 面試官 |
| rating | numeric | 評分 |
| summary | text | 評語 |
| recommendation | varchar | hire / hold / reject |
| result | varchar | pending / passed / rejected |
| created_at | timestamptz | 建立時間 |

---

### 2.8 通知與 AI 記錄

#### `notifications`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| user_id | uuid | 對應 users |
| channel | varchar | email / line / sms / in_app |
| type | varchar | 類型 |
| title | varchar | 標題 |
| content | text | 內容 |
| status | varchar | queued / sent / failed |
| sent_at | timestamptz | 發送時間 |
| created_at | timestamptz | 建立時間 |

#### `ai_logs`

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| id | uuid | 主鍵 |
| module_name | varchar | 模組名稱 |
| user_id | uuid | 觸發者 |
| action_name | varchar | AI 動作 |
| input_summary | text | 輸入摘要 |
| output_summary | text | 輸出摘要 |
| model_name | varchar | 使用模型 |
| status | varchar | success / failed |
| created_at | timestamptz | 建立時間 |

---

## 3. 關聯摘要

核心關聯可先這樣理解：

- `users` 1 對 1 `students`
- `users` 1 對 1 `teachers`
- `users` 1 對 1 `staff`
- `leads` 1 對多 `lead_logs`
- `leads` 1 對多 `trial_bookings`
- `students` 1 對多 `enrollments`
- `courses` 1 對多 `course_modules`
- `courses` 1 對多 `classes`
- `classes` 1 對多 `class_sessions`
- `classes` 1 對多 `assignments`
- `classes` 1 對多 `exams`
- `enrollments` 1 對多 `payments`
- `assignments` 1 對多 `assignment_submissions`
- `exams` 1 對多 `exam_results`
- `job_positions` 1 對多 `applicants`
- `applicants` 1 對多 `interviews`

---

## 4. MVP 必要表

如果第一階段先求可上線，最少先做：

1. `users`
2. `leads`
3. `lead_logs`
4. `students`
5. `courses`
6. `classes`
7. `enrollments`
8. `payments`
9. `staff`
10. `notifications`

---

## 5. 實作注意事項

1. 金流、通知、AI 動作都要保留原始 payload，避免除錯困難。
2. `class_sessions` 不要省略，否則後續點名、補課、單堂教材會很難做。
3. `leads` 與 `students` 要可追溯轉換，方便看轉換率。
4. AI 產物要標示來源、模型與操作者，方便後續審計。
5. 若規劃多校區，建議多加 `branch_id` 到大多數核心表。
