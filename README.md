# CrewAI Marketplace Agent Team

這是一套以 CrewAI 為核心的商品運營自動化系統，將五組代理拆成清楚的分工：

- A 組：抓 Facebook Marketplace 商品
- B 組：補官方規格、價格、上市資訊
- C 組：社群貼文模組已預留，但目前停用
- D 組：將各階段結果寫入 Supabase，保留監控紀錄
- E 組：掃描 Google Drive 入倉圖片，自動做 AI 辨識、估價、行銷文與批發頁展示

目前專案同時提供兩種運行方式：

- CLI / Cron：適合 Render 排程執行
- FastAPI：適合後台手動觸發、之後串前端或 webhook

## 目前營運設定

- 首發平台：`Threads`
- 主要商品類型：`二手生財餐飲器具`
- 主要市場區域：`新北市 -> 台北市 -> 桃園`
- GitHub repo：`https://github.com/809540023-lgtm/crewAI1`
- 搜尋模式：`餐飲設備詞庫輪搜`

## 專案結構

```text
.
├── .env.example
├── .github/workflows/validate.yml
├── .gitignore
├── README.md
├── agents.py
├── api.py
├── config.py
├── main.py
├── models.py
├── render.yaml
├── requirements.txt
├── services/
│   ├── __init__.py
│   ├── inventory_pipeline.py
│   ├── pipeline.py
│   └── social_publisher.py
├── sql/
│   ├── create_inventory_tables.sql
│   └── create_product_logs.sql
├── tasks.py
├── tools/
│   ├── __init__.py
│   ├── apify_tool.py
│   ├── google_drive_inventory_tool.py
│   ├── inventory_ai_tool.py
│   ├── inventory_supabase_tool.py
│   ├── official_research_tool.py
│   └── supabase_tool.py
└── utils/
    └── json_parser.py
```

## 補強後的重點

### 1. 結構化輸出驗證

- `utils/json_parser.py` 會從 LLM 輸出中抽 JSON。
- `models.py` 用 Pydantic 驗證 A、B、C、D 四段結果。
- 如果某一段 JSON 格式不正確，summary 會標記 `partial_success` 並記錄風險。

### 2. 主流程與持久化分離

- `services/pipeline.py` 負責統整 CrewAI 執行、解析結果、寫入 Supabase。
- D 組仍然負責產出 summary，但實際資料落庫由程式保底完成，穩定性更高。
- summary 目前也會記錄 AI 成本估算、token 使用量與 web search 次數，供 dashboard 做近 6 小時統計。

### 3. API 與排程雙入口

- `main.py` 提供 CLI / cron 執行。
- `api.py` 提供 `POST /runs` 觸發。
- `render.yaml` 同時包含 Render Web Service 與 Cron Job。

### 4. 社群層先保留骨架，暫停執行

- `services/social_publisher.py` 已經預留 Facebook / Instagram / Threads 三平台的發布流程。
- 目前系統先專注在資料收集，不會執行社群文案生成與發送。
- 等你把平台 API 與權限準備好後，再把各平台 connector 接上即可。

### 5. E 組入庫建檔與批發頁

- `tools/google_drive_inventory_tool.py` 會掃描 Google Drive 根資料夾 `agai2_new`，抓最新日期資料夾或指定日期資料夾。
- E 組同時支援兩種結構：
  - `agai2_new/20260101/商品名_1.jpg`
  - `agai2_new/封口機/*.jpg`
- 如果未提供 `GOOGLE_SERVICE_ACCOUNT_JSON`，但 `agai2_new` 是公開共享資料夾，E 組會自動改走公開分享 fallback 模式。
- `services/inventory_pipeline.py` 會把 1 到 4 張同商品圖片自動分組，交給 AI 辨識商品名稱、類別、品牌、狀況、建議售價與行銷文。
- `tools/inventory_supabase_tool.py` 會把資料寫入 `inventory_items`、`inventory_item_images`、`inventory_marketing_assets`。
- `GET /inventory/latest` 會自動生成「最新入庫歡迎同行批發」網頁，頁尾電話固定顯示 `0915888927`。

## 本地安裝

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 本地執行

### 1. 跑 CLI 任務

```bash
python main.py --query "二手 生財 餐飲 器具" --location "New Taipei City" --max-results 3
```

### 2. 啟動 API

```bash
uvicorn api:app --reload
```

### 3. 呼叫 API

```bash
curl -X POST http://127.0.0.1:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "query": "二手 MacBook Pro M2",
    "location": "New Taipei City",
    "max_results": 3,
    "publish": false
  }'
```

### 4. 觸發 E 組入倉建檔

```bash
curl -X POST http://127.0.0.1:8000/inventory/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "folder_name": "20260101"
  }'
```

如果不傳 `folder_name`，系統會自動抓 `agai2_new` 底下最新的日期資料夾。

## School Platform Storage 切換

如果你要把 AI 日語補習班平台從 JSON store 切到 PostgreSQL，至少需要這三個環境變數：

```bash
SCHOOL_PLATFORM_STORAGE_BACKEND=postgres
SCHOOL_PLATFORM_JSON_PATH=data/school_platform_store.json
SCHOOL_PLATFORM_POSTGRES_DSN=postgresql://USER:PASSWORD@HOST:5432/DBNAME
SCHOOL_PLATFORM_APP_BASE_URL=https://your-school-platform-domain
```

可用的初始化 / 搬遷 / 驗證腳本：

```bash
python3 scripts/init_school_platform_postgres.py
python3 scripts/migrate_school_platform_json_to_postgres.py
python3 scripts/smoke_test_school_platform_postgres.py
python3 scripts/cutover_school_platform_postgres.py
python3 scripts/verify_school_platform_postgres_row_writes.py
```

如果要看目前 readiness 與 cutover 說明，可以直接打開：

- `/school-platform/system`
- `/school-platform/db-migration`
- `/school-platform/db-smoke-test`

如果要對 live / staging 站做 smoke check，也可以直接跑：

```bash
python3 scripts/smoke_test_school_platform_deployment.py --base-url https://crewai1-api.onrender.com
```

## School Platform Payments / Notifications

如果要把金流與通知外發切成正式 provider，請至少補齊下面這批環境變數：

```bash
# Payments
SCHOOL_PLATFORM_PAYMENT_PROVIDER=stripe
SCHOOL_PLATFORM_PAYMENT_CURRENCY=jpy
SCHOOL_PLATFORM_STRIPE_SECRET_KEY=sk_live_or_test_xxx
SCHOOL_PLATFORM_STRIPE_PUBLISHABLE_KEY=pk_live_or_test_xxx
SCHOOL_PLATFORM_STRIPE_WEBHOOK_SECRET=whsec_xxx
SCHOOL_PLATFORM_STRIPE_SUCCESS_URL=https://your-domain/school-platform/payment?email={CHECKOUT_EMAIL}&order_no={CHECKOUT_ORDER_NO}&payment_result=success
SCHOOL_PLATFORM_STRIPE_CANCEL_URL=https://your-domain/school-platform/payment?email={CHECKOUT_EMAIL}&order_no={CHECKOUT_ORDER_NO}&payment_result=cancel

# Email
SCHOOL_PLATFORM_EMAIL_PROVIDER=auto
SCHOOL_PLATFORM_SMTP_HOST=smtp.example.com
SCHOOL_PLATFORM_SMTP_PORT=587
SCHOOL_PLATFORM_SMTP_USERNAME=your-user
SCHOOL_PLATFORM_SMTP_PASSWORD=your-password
SCHOOL_PLATFORM_SMTP_FROM_EMAIL=noreply@example.com

# or Resend
SCHOOL_PLATFORM_RESEND_API_KEY=re_xxx
SCHOOL_PLATFORM_RESEND_FROM_EMAIL=School Platform <noreply@example.com>

# LINE
SCHOOL_PLATFORM_LINE_CHANNEL_ACCESS_TOKEN=your_line_token
SCHOOL_PLATFORM_LINE_CHANNEL_SECRET=your_line_secret
```

目前系統頁會直接顯示：

- `Snapshot Integrity`
- `External Integrations`
- `Payments readiness`
- `Notifications readiness`

正式 webhook 入口：

- `POST /school-platform/api/payments/stripe/webhook`

## School Platform AI Runtime

School Platform 的 AI 功能現在支援「外部模型 + fallback」模式：

- 若有提供 `OPENAI_API_KEY` 與 `OPENAI_MODEL`，系統會嘗試用外部模型優化招生 follow-up、教案草稿、學員練習與週營運摘要
- 若外部模型未設定或呼叫失敗，系統會自動退回本地 fallback payload，不會讓頁面或 API 壞掉

可直接查看目前 AI readiness：

- `/school-platform/admin/ai-center`
- `/school-platform/api/ai/status`

## Supabase 資料表

在 Supabase SQL Editor 執行：

```sql
create extension if not exists pgcrypto;

create table if not exists product_logs (
  id uuid primary key default gen_random_uuid(),
  run_id text not null,
  stage text not null,
  status text not null default 'completed',
  query text,
  payload jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists product_logs_run_id_idx on product_logs (run_id);
create index if not exists product_logs_stage_idx on product_logs (stage);
create index if not exists product_logs_created_at_idx on product_logs (created_at desc);
```

E 組另外需要執行：

```sql
create extension if not exists pgcrypto;

create table if not exists inventory_items (
  id uuid primary key default gen_random_uuid(),
  warehouse_date text not null,
  folder_name text not null,
  product_name text,
  normalized_product_name text,
  source_file_stem text,
  brand text,
  model text,
  category text,
  condition_summary text,
  missing_parts text,
  cleaning_status text,
  repair_status text,
  suggested_price numeric,
  min_price numeric,
  suggested_platforms jsonb not null default '[]'::jsonb,
  confidence numeric not null default 0,
  needs_review boolean not null default false,
  source_type text not null default 'purchased_inventory',
  image_count int not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists inventory_item_images (
  id uuid primary key default gen_random_uuid(),
  inventory_item_id uuid not null references inventory_items(id) on delete cascade,
  image_name text,
  image_url text,
  image_order int not null default 1,
  created_at timestamptz not null default now()
);

create table if not exists inventory_marketing_assets (
  id uuid primary key default gen_random_uuid(),
  inventory_item_id uuid not null references inventory_items(id) on delete cascade,
  listing_title text,
  short_description text,
  facebook_post text,
  threads_post text,
  hashtags jsonb not null default '[]'::jsonb,
  seo_keywords jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
```

## 你需要準備哪些 API

### 必須

這四個是整套系統最基本要能跑起來的：

- `OPENAI_API_KEY`
  用途：B 組官方資料研究、CrewAI 代理推理
- `APIFY_API_TOKEN`
  用途：A 組抓 Facebook Marketplace
- `SUPABASE_URL`
  用途：D 組資料落地
- `SUPABASE_SERVICE_ROLE_KEY`
  用途：D 組寫資料庫
- `GOOGLE_SERVICE_ACCOUNT_JSON`
  用途：E 組讀取 Google Drive `agai2_new`

### 建議一起準備

如果你希望系統完成後主動通知團隊：

- `SLACK_BOT_TOKEN`
- `SLACK_CHANNEL_ID`

這一組之後可以接成「執行完成就把 summary 丟 Slack」。目前程式已預留 env，但還沒把 Slack 發送邏輯寫進去。

### 真正要自動發文時需要

#### Facebook Page

- `FACEBOOK_PAGE_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`

用途：把 C 組產出的 Facebook 貼文發到粉專。

#### Instagram Business

- `FACEBOOK_PAGE_ACCESS_TOKEN`
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`

用途：Instagram Graph API 發文。通常會跟 Meta Business / Facebook Page 綁在一起，不是單純個人 IG 就能用。

#### Threads

- `THREADS_ACCESS_TOKEN`
- `THREADS_USER_ID`

用途：把 Threads 文案自動發布出去。因為你目前優先上 Threads，這組會是你最先需要準備的發文 API。

## 哪些平台帳號型態你要先準備

- Facebook：要有 `Page`，不是只有個人帳號
- Instagram：要有 `Business` 或 `Creator` 帳號，且綁定同一個 Meta Business
- Threads：需要能取得 Threads API 存取權杖的帳號
- Supabase：一個專案即可
- Apify：一個帳號即可
- OpenAI：一個 API 專案即可

## Render 部署

專案已附 [render.yaml](./render.yaml)，可同時建立：

- 一個 Web Service：提供 API
- 一個 Cron Job：定時跑 pipeline

目前排程策略：

- 白天時段（`08:00-22:59`, `Asia/Taipei`）：每 30 分鐘執行一次
- 半夜時段（`23:00-07:59`, `Asia/Taipei`）：只在 `02:00` 與 `05:00` 執行
- Render cron 會每 30 分鐘喚醒一次，但 `main.py` 會依本地時間判斷本輪是否應略過

建議流程：

1. 先推到 GitHub
2. 在 Render 匯入 repo
3. 使用 Blueprint 建立服務
4. 在 Render 補上環境變數
5. 先以 `PUBLISH_ENABLED=false`、`PUBLISH_DRY_RUN=true` 上線
6. 等平台 API 測通後，再打開真實發文

如果你是 Threads 先上線，建議順序是：

1. 先完成 `OPENAI`、`APIFY`、`SUPABASE`
2. 再完成 `THREADS_ACCESS_TOKEN`、`THREADS_USER_ID`
3. 先讓 Render cron 以 dry run 跑通
4. 最後再打開真實發文

## GitHub 上傳

```bash
git add .
git commit -m "feat: harden marketplace CrewAI pipeline"
```

接著：

```bash
git remote add origin <your-repo-url>
git push -u origin main
```

## 現在的限制

- Facebook / Instagram / Threads 的正式發文 connector 還是骨架，尚未直接呼叫官方 API。
- 目前已經能做完整 dry run、資料驗證、DB 落地、API 觸發。
- 真正上線前，建議先挑 1 個平台做通，再擴到三平台。

## 我已經幫你完成的事

- 建好 CrewAI 四組代理與任務鏈
- 建好 E 組 Google Drive 入庫建檔骨架
- 建好 Apify / OpenAI / Supabase 工具
- 建好 CLI 與 FastAPI 雙入口
- 建好 Render `web + cron` 部署藍圖
- 建好 GitHub Actions 語法驗證
- 建好 JSON 結構化解析與 Pydantic 驗證
- 建好平台發文 connector 骨架與 Slack 通知骨架
- 建好最新入庫批發展示頁

## 你需要自己完成的事

- 建立並提供 OpenAI、Apify、Supabase 帳號與 API 金鑰
- 在 Supabase 建立資料表並貼入 SQL
- 準備 Facebook Page、Instagram Business、Threads 帳號與對應 API 權限
- 將專案推到你自己的 GitHub repo
- 在你的 Render 帳號內建立服務並填入環境變數
- 若要正式自動發文，需在各平台開發者後台完成審核、權限申請與 token 取得

## 我建議你先給我的資料

先不用一次丟全部。你先提供下面這一批，我就可以繼續幫你把系統接到更完整：

1. 你想先發的社群平台：`Facebook`、`Instagram`、`Threads` 哪些先上
2. 商品類型：例如 3C、家電、美妝、精品
3. 主要營運城市：例如 `Taipei`、`Taichung`
4. GitHub repo URL
5. Render 服務要不要我一起幫你整理成正式上線版設定
6. 如果要接真實發文，再給對應平台的 API 金鑰與帳號 ID
