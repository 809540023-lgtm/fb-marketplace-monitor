from __future__ import annotations

from datetime import date, datetime
from uuid import UUID, uuid4

from digichef.config import load_settings
from digichef.repository import DigiChefJsonRepository
from digichef.schemas import (
    CookingProfile,
    DashboardMetrics,
    IssueReport,
    IssueReportCreate,
    MarinadeBatch,
    MarinadeBatchCreate,
    OperationsDashboard,
    OvenTestCreate,
    OvenTestRecord,
    PhotoAsset,
    PhotoAssetCreate,
    ProductSpec,
    PurchaseLog,
    PurchaseLogCreate,
    SopRecord,
    ShiftTask,
    TaskStatusUpdate,
)


def _now() -> datetime:
    return datetime.now().astimezone()


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.astimezone()
    return value


class DigiChefStore:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.repository = DigiChefJsonRepository(self.settings.json_path)
        self.products: list[ProductSpec] = self._seed_products()
        self.tasks: list[ShiftTask] = self._seed_tasks()
        self.purchases: list[PurchaseLog] = []
        self.marinade_batches: list[MarinadeBatch] = []
        self.oven_tests: list[OvenTestRecord] = []
        self.photo_assets: list[PhotoAsset] = []
        self.sops: list[SopRecord] = self._seed_sops()
        self.issues: list[IssueReport] = []
        self._load_or_seed()

    def _seed_products(self) -> list[ProductSpec]:
        return [
            ProductSpec(
                code="A",
                name="輕纖果醋雞胸",
                protein_source="雞胸",
                marinade_note="雞胸 150g + 米酒 10cc + 蘋果醋 5cc",
                description="清爽果醋風味，主打高蛋白與保水度。",
                main_cost=19.13,
                combo_cost=28.13,
                calories=344,
                protein_g=41.1,
                fat_g=6.3,
                carbs_g=25.9,
                subscription_price_total=840,
                subscription_unit_price=56,
                retail_price=84,
                texture_style="多汁",
                cooking_profile=CookingProfile(
                    mode="Combi-Steam",
                    temperature_c=160,
                    humidity_pct=70,
                    fan_speed=2,
                    target_core_temp_c=73,
                    tray_type="平底烤盤",
                    finish_note="以探針確認中心 72-74°C，重點是鎖水。",
                ),
            ),
            ProductSpec(
                code="B",
                name="日式薄粉雞胸",
                protein_source="雞胸",
                marinade_note="雞胸 150g + 日清粉 5g + 米酒 5cc",
                description="外層薄脆上色，適合喜歡乾爽口感的客群。",
                main_cost=19.54,
                combo_cost=28.54,
                calories=355,
                protein_g=41.4,
                fat_g=6.3,
                carbs_g=29.6,
                subscription_price_total=855,
                subscription_unit_price=57,
                retail_price=86,
                texture_style="酥炸",
                cooking_profile=CookingProfile(
                    mode="Dry Heat",
                    temperature_c=215,
                    humidity_pct=0,
                    fan_speed=4,
                    target_core_temp_c=73,
                    tray_type="洞洞烤盤",
                    finish_note="表面需噴微量油脂，確保金黃酥脆。",
                ),
            ),
            ProductSpec(
                code="C",
                name="鮮萃醋漬雞腿",
                protein_source="去皮雞腿",
                marinade_note="去皮雞腿 150g + 米酒 10cc + 蘋果醋 5cc",
                description="雞腿油脂更豐富，適合追求肉汁與飽足感。",
                main_cost=25.13,
                combo_cost=34.13,
                calories=401,
                protein_g=36.6,
                fat_g=16.9,
                carbs_g=25.9,
                subscription_price_total=1020,
                subscription_unit_price=68,
                retail_price=102,
                texture_style="多汁",
                cooking_profile=CookingProfile(
                    mode="Combi-Steam",
                    temperature_c=170,
                    humidity_pct=70,
                    fan_speed=3,
                    target_core_temp_c=73,
                    tray_type="平底烤盤",
                    finish_note="雞腿需要穩定熟度與肉汁表現。",
                ),
            ),
            ProductSpec(
                code="D",
                name="經典金黃雞腿",
                protein_source="去皮雞腿",
                marinade_note="去皮雞腿 150g + 日清粉 5g + 米酒 5cc",
                description="外觀最有賣相，適合未來做視覺主打商品。",
                main_cost=25.54,
                combo_cost=34.54,
                calories=412,
                protein_g=36.9,
                fat_g=17.0,
                carbs_g=29.6,
                subscription_price_total=1035,
                subscription_unit_price=69,
                retail_price=104,
                texture_style="酥炸",
                cooking_profile=CookingProfile(
                    mode="Dry Heat",
                    temperature_c=215,
                    humidity_pct=0,
                    fan_speed=4,
                    target_core_temp_c=73,
                    tray_type="洞洞烤盤",
                    finish_note="重點檢查金黃度、酥感與出油控制。",
                ),
            ),
        ]

    def _seed_tasks(self) -> list[ShiftTask]:
        seed_date = date(2026, 4, 14)
        now = _now()
        return [
            ShiftTask(
                id=uuid4(),
                work_date=seed_date,
                shift_label="早班",
                title="開工盤點與測試前確認",
                checklist=[
                    "拍現場照與冰箱現況",
                    "確認雞胸、雞腿、米酒、蘋果醋、日清粉、蛋、地瓜",
                    "確認磅秤、探針與烤箱可用",
                ],
                status="todo",
                decision_needed="若缺料或設備異常，要立刻回報老闆。",
                created_at=now,
                updated_at=now,
            ),
            ShiftTask(
                id=uuid4(),
                work_date=seed_date,
                shift_label="中班",
                title="A-D 套餐測試烤製",
                checklist=[
                    "建立 TEST-20260414-A1 到 D1",
                    "逐批記錄烤前重量、芯溫與烤後重量",
                    "每批補上外觀、口感、多汁度與照片",
                ],
                status="todo",
                decision_needed="若烤色或芯溫不穩，先標記待複測。",
                created_at=now,
                updated_at=now,
            ),
            ShiftTask(
                id=uuid4(),
                work_date=seed_date,
                shift_label="收班",
                title="日結回報",
                checklist=[
                    "確認測試表欄位完整",
                    "確認照片連結可開啟",
                    "回報可列正式 SOP 與需複測項目",
                ],
                status="todo",
                decision_needed="確認 2026-04-15 是否需要補料或重測。",
                created_at=now,
                updated_at=now,
            ),
        ]

    def _seed_sops(self) -> list[SopRecord]:
        now = _now()
        return [
            SopRecord(
                id=uuid4(),
                code="SOP-01",
                category="開工",
                title="開工盤點",
                version="v1.0",
                status="active",
                trigger_condition="每日第一個工作動作",
                steps=[
                    "確認冷藏、冷凍、乾貨區",
                    "確認烤箱、磅秤、探針與工作台狀態",
                    "若異常，先拍照再回報",
                ],
                completion_standard="缺料與異常已記錄在線上表單",
                required_uploads=["現場照", "冰箱現況"],
                exception_rule="設備異常時不得直接進入測試。",
                updated_at=now,
            ),
            SopRecord(
                id=uuid4(),
                code="SOP-02",
                category="進貨",
                title="進貨驗收",
                version="v1.0",
                status="active",
                trigger_condition="任何原料到貨時",
                steps=[
                    "拍包裝與到貨整體照",
                    "核對規格、數量、單價",
                    "寫入存放位置與到貨檢查結果",
                ],
                completion_standard="供應商、數量、成本、照片與庫存位置完整",
                required_uploads=["進貨照", "發票或收據照"],
                exception_rule="品質異常需標記待觀察或退貨。",
                updated_at=now,
            ),
            SopRecord(
                id=uuid4(),
                code="SOP-03",
                category="醃製",
                title="醃製批次建立",
                version="v1.0",
                status="active",
                trigger_condition="任何新批次準備時",
                steps=[
                    "依方案確認肉品與配方",
                    "每份秤重 150g",
                    "封袋並標示方案、日期與批次號",
                ],
                completion_standard="批次可追溯到配方與執行人",
                required_uploads=["醃製批次照"],
                exception_rule="配方錯誤或未標記的批次不得進入後續流程。",
                updated_at=now,
            ),
            SopRecord(
                id=uuid4(),
                code="SOP-04",
                category="測試",
                title="烤製測試紀錄",
                version="v1.0",
                status="active",
                trigger_condition="新品測試或參數調整",
                steps=[
                    "依產品設定輸入模式、溫度、濕度、風速",
                    "出爐後立刻量芯溫、秤重、拍照",
                    "完成外觀、口感與多汁度評分",
                ],
                completion_standard="每批都有完整數據與照片",
                required_uploads=["出爐照", "切面照"],
                exception_rule="若芯溫不達標，直接列入待複測。",
                updated_at=now,
            ),
            SopRecord(
                id=uuid4(),
                code="SOP-05",
                category="成品",
                title="成品拍照上傳",
                version="v1.0",
                status="active",
                trigger_condition="每一批完成後",
                steps=[
                    "依命名規則上傳照片",
                    "回填 Drive 連結到測試與照片表",
                    "確認圖片能開啟",
                ],
                completion_standard="照片可追溯到方案、日期與拍攝階段",
                required_uploads=["Drive 連結"],
                exception_rule="缺圖或連結錯誤視為未完成。",
                updated_at=now,
            ),
            SopRecord(
                id=uuid4(),
                code="SOP-06",
                category="日結",
                title="收班回報",
                version="v1.0",
                status="draft",
                trigger_condition="每日下班前",
                steps=[
                    "檢查今日表單與照片完整性",
                    "回報正式可採用參數",
                    "回報明日需補料與待決策事項",
                ],
                completion_standard="老闆可直接看懂今日狀態與明日需求",
                required_uploads=["日結摘要"],
                exception_rule="未完成日結不得視為當日交班完成。",
                updated_at=now,
            ),
        ]

    def _load_or_seed(self) -> None:
        payload = self.repository.load()
        if not payload:
            self._persist()
            return
        self.products = [ProductSpec.model_validate(item) for item in payload.get("products", self.products)]
        self.tasks = [ShiftTask.model_validate(item) for item in payload.get("tasks", self.tasks)]
        self.purchases = [PurchaseLog.model_validate(item) for item in payload.get("purchases", [])]
        self.marinade_batches = [MarinadeBatch.model_validate(item) for item in payload.get("marinade_batches", [])]
        self.oven_tests = [OvenTestRecord.model_validate(item) for item in payload.get("oven_tests", [])]
        self.photo_assets = [PhotoAsset.model_validate(item) for item in payload.get("photo_assets", [])]
        self.sops = [SopRecord.model_validate(item) for item in payload.get("sops", self.sops)]
        self.issues = [IssueReport.model_validate(item) for item in payload.get("issues", [])]

    def _persist(self) -> None:
        self.repository.save(
            {
                "products": [item.model_dump(mode="json") for item in self.products],
                "tasks": [item.model_dump(mode="json") for item in self.tasks],
                "purchases": [item.model_dump(mode="json") for item in self.purchases],
                "marinade_batches": [item.model_dump(mode="json") for item in self.marinade_batches],
                "oven_tests": [item.model_dump(mode="json") for item in self.oven_tests],
                "photo_assets": [item.model_dump(mode="json") for item in self.photo_assets],
                "sops": [item.model_dump(mode="json") for item in self.sops],
                "issues": [item.model_dump(mode="json") for item in self.issues],
            }
        )

    def list_products(self) -> list[ProductSpec]:
        return sorted(self.products, key=lambda item: item.code)

    def get_product(self, code: str) -> ProductSpec:
        normalized = code.strip().upper()
        for item in self.products:
            if item.code == normalized:
                return item
        raise KeyError(normalized)

    def current_work_date(self) -> date:
        today = date.today()
        future_dates = sorted({item.work_date for item in self.tasks if item.work_date >= today})
        if future_dates:
            return future_dates[0]
        task_dates = sorted({item.work_date for item in self.tasks})
        return task_dates[0] if task_dates else today

    def tasks_for_date(self, work_date: date | None = None) -> list[ShiftTask]:
        target = work_date or self.current_work_date()
        return sorted(
            [item for item in self.tasks if item.work_date == target],
            key=lambda item: ("早班", "中班", "收班").index(item.shift_label) if item.shift_label in {"早班", "中班", "收班"} else 99,
        )

    def list_purchases(self) -> list[PurchaseLog]:
        return sorted(self.purchases, key=lambda item: item.purchase_date, reverse=True)

    def list_batches(self) -> list[MarinadeBatch]:
        return sorted(self.marinade_batches, key=lambda item: item.marinade_started_at, reverse=True)

    def list_oven_tests(self) -> list[OvenTestRecord]:
        return sorted(self.oven_tests, key=lambda item: (item.test_date, item.created_at), reverse=True)

    def list_photo_assets(self) -> list[PhotoAsset]:
        return sorted(self.photo_assets, key=lambda item: (item.captured_on, item.created_at), reverse=True)

    def list_sops(self) -> list[SopRecord]:
        return sorted(self.sops, key=lambda item: item.code)

    def list_issues(self) -> list[IssueReport]:
        return sorted(self.issues, key=lambda item: item.reported_at, reverse=True)

    def create_purchase(self, payload: PurchaseLogCreate) -> PurchaseLog:
        record = PurchaseLog(
            id=uuid4(),
            total_cost=round(payload.quantity * payload.unit_cost, 2),
            created_at=_now(),
            **payload.model_dump(),
        )
        self.purchases.append(record)
        self._persist()
        return record

    def create_batch(self, payload: MarinadeBatchCreate) -> MarinadeBatch:
        record = MarinadeBatch(
            id=uuid4(),
            marinade_started_at=_normalize_datetime(payload.marinade_started_at),
            created_at=_now(),
            **payload.model_dump(exclude={"marinade_started_at"}),
        )
        self.marinade_batches.append(record)
        self._persist()
        return record

    def create_oven_test(self, payload: OvenTestCreate) -> OvenTestRecord:
        weight_loss_pct = None
        if payload.cooked_weight_g is not None and payload.raw_weight_g:
            weight_loss_pct = round(((payload.raw_weight_g - payload.cooked_weight_g) / payload.raw_weight_g) * 100, 2)
        record = OvenTestRecord(
            id=uuid4(),
            weight_loss_pct=weight_loss_pct,
            created_at=_now(),
            **payload.model_dump(),
        )
        self.oven_tests.append(record)
        self._persist()
        return record

    def create_photo_asset(self, payload: PhotoAssetCreate) -> PhotoAsset:
        record = PhotoAsset(
            id=uuid4(),
            created_at=_now(),
            **payload.model_dump(),
        )
        self.photo_assets.append(record)
        self._persist()
        return record

    def create_issue(self, payload: IssueReportCreate) -> IssueReport:
        record = IssueReport(
            id=uuid4(),
            reported_at=_normalize_datetime(payload.reported_at),
            created_at=_now(),
            **payload.model_dump(exclude={"reported_at"}),
        )
        self.issues.append(record)
        self._persist()
        return record

    def update_task_status(self, task_id: UUID, payload: TaskStatusUpdate) -> ShiftTask:
        for index, item in enumerate(self.tasks):
            if item.id == task_id:
                updated = item.model_copy(
                    update={
                        "status": payload.status,
                        "owner_name": payload.owner_name or item.owner_name,
                        "notes": payload.notes or item.notes,
                        "updated_at": _now(),
                    }
                )
                self.tasks[index] = updated
                self._persist()
                return updated
        raise KeyError(str(task_id))

    def dashboard(self) -> OperationsDashboard:
        work_date = self.current_work_date()
        tasks = self.tasks_for_date(work_date)
        recent_tests = self.list_oven_tests()[:6]
        recent_purchases = self.list_purchases()[:6]
        recent_batches = self.list_batches()[:6]
        recent_photos = self.list_photo_assets()[:6]
        open_issues = [item for item in self.list_issues() if item.status != "resolved"][:6]
        tests_for_work_date = [item for item in self.oven_tests if item.test_date == work_date]
        metrics = DashboardMetrics(
            work_date=work_date,
            product_count=len(self.products),
            task_total=len(tasks),
            task_completed=sum(1 for item in tasks if item.status == "done"),
            task_blocked=sum(1 for item in tasks if item.status == "blocked"),
            test_count=len(tests_for_work_date),
            approved_test_count=sum(1 for item in tests_for_work_date if item.decision == "approved"),
            open_issue_count=len([item for item in self.issues if item.status != "resolved"]),
            approved_sop_count=sum(1 for item in self.sops if item.status == "active"),
        )
        return OperationsDashboard(
            metrics=metrics,
            tasks=tasks,
            recent_purchases=recent_purchases,
            recent_batches=recent_batches,
            recent_tests=recent_tests,
            open_issues=open_issues,
            recent_photos=recent_photos,
            sops=self.list_sops(),
        )
