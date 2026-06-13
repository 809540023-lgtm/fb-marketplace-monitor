from __future__ import annotations

from datetime import date
from uuid import UUID

from digichef.schemas import (
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
    ShiftTask,
    SopRecord,
    TaskStatusUpdate,
)


class DigiChefCatalogService:
    def __init__(self, store) -> None:
        self.store = store

    def list_products(self) -> list[ProductSpec]:
        return self.store.list_products()

    def get_product(self, code: str) -> ProductSpec:
        return self.store.get_product(code)


class DigiChefOperationsService:
    def __init__(self, store) -> None:
        self.store = store

    def dashboard(self) -> OperationsDashboard:
        return self.store.dashboard()

    def current_work_date(self) -> date:
        return self.store.current_work_date()

    def tasks_for_date(self, work_date: date | None = None) -> list[ShiftTask]:
        return self.store.tasks_for_date(work_date)

    def list_purchases(self) -> list[PurchaseLog]:
        return self.store.list_purchases()

    def list_batches(self) -> list[MarinadeBatch]:
        return self.store.list_batches()

    def list_oven_tests(self) -> list[OvenTestRecord]:
        return self.store.list_oven_tests()

    def list_photo_assets(self) -> list[PhotoAsset]:
        return self.store.list_photo_assets()

    def list_issues(self) -> list[IssueReport]:
        return self.store.list_issues()

    def list_sops(self) -> list[SopRecord]:
        return self.store.list_sops()

    def create_purchase(self, payload: PurchaseLogCreate) -> PurchaseLog:
        return self.store.create_purchase(payload)

    def create_batch(self, payload: MarinadeBatchCreate) -> MarinadeBatch:
        return self.store.create_batch(payload)

    def create_oven_test(self, payload: OvenTestCreate) -> OvenTestRecord:
        return self.store.create_oven_test(payload)

    def create_photo_asset(self, payload: PhotoAssetCreate) -> PhotoAsset:
        return self.store.create_photo_asset(payload)

    def create_issue(self, payload: IssueReportCreate) -> IssueReport:
        return self.store.create_issue(payload)

    def update_task_status(self, task_id: UUID, payload: TaskStatusUpdate) -> ShiftTask:
        return self.store.update_task_status(task_id, payload)
