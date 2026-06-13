from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


TaskStatus = Literal["todo", "in_progress", "done", "blocked"]
CheckResult = Literal["pass", "watch", "reject"]
BatchStatus = Literal["planned", "marinating", "ready_for_test", "approved", "discarded"]
DecisionStatus = Literal["pending", "approved", "retest"]
IssueStatus = Literal["new", "investigating", "resolved"]
SopStatus = Literal["draft", "active", "archived"]
PhotoReviewStatus = Literal["pending", "approved", "reshoot"]


class CookingProfile(BaseModel):
    mode: str
    temperature_c: int
    humidity_pct: int
    fan_speed: int
    target_core_temp_c: int
    tray_type: str
    finish_note: str


class ProductSpec(BaseModel):
    code: str
    name: str
    protein_source: str
    raw_weight_g: int = 150
    marinade_note: str
    description: str
    main_cost: float
    combo_cost: float
    calories: int
    protein_g: float
    fat_g: float
    carbs_g: float
    subscription_price_total: float
    subscription_unit_price: float
    retail_price: float
    texture_style: str
    cooking_profile: CookingProfile


class ShiftTask(BaseModel):
    id: UUID
    work_date: date
    shift_label: str
    owner_name: str | None = None
    title: str
    checklist: list[str] = Field(default_factory=list)
    status: TaskStatus = "todo"
    notes: str | None = None
    decision_needed: str | None = None
    created_at: datetime
    updated_at: datetime


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    owner_name: str | None = None
    notes: str | None = None


class PurchaseLogCreate(BaseModel):
    purchase_date: date
    supplier_name: str
    item_name: str
    item_spec: str
    quantity: float
    unit: str
    unit_cost: float
    storage_location: str
    check_result: CheckResult = "pass"
    photo_url: str | None = None
    recorded_by: str
    notes: str | None = None


class PurchaseLog(PurchaseLogCreate):
    id: UUID
    total_cost: float
    created_at: datetime


class MarinadeBatchCreate(BaseModel):
    batch_code: str
    product_code: str
    protein_source: str
    raw_weight_g: float
    portion_count: int
    rice_wine_cc: float = 0
    apple_vinegar_cc: float = 0
    flour_g: float = 0
    marinade_started_at: datetime
    planned_cook_date: date
    status: BatchStatus = "planned"
    handled_by: str
    notes: str | None = None


class MarinadeBatch(MarinadeBatchCreate):
    id: UUID
    created_at: datetime


class OvenTestCreate(BaseModel):
    test_code: str
    test_date: date
    product_code: str
    texture_style: str
    oven_mode: str
    temperature_c: int
    humidity_pct: int
    fan_speed: int
    target_core_temp_c: int
    actual_core_temp_c: float | None = None
    raw_weight_g: float
    cooked_weight_g: float | None = None
    appearance_score: int | None = None
    taste_score: int | None = None
    juiciness_score: int | None = None
    photo_url: str | None = None
    notes: str | None = None
    decision: DecisionStatus = "pending"
    recorded_by: str


class OvenTestRecord(OvenTestCreate):
    id: UUID
    weight_loss_pct: float | None = None
    created_at: datetime


class PhotoAssetCreate(BaseModel):
    captured_on: date
    product_code: str
    stage: str
    file_name: str
    drive_url: str | None = None
    purpose: str
    captured_by: str
    review_status: PhotoReviewStatus = "pending"
    notes: str | None = None


class PhotoAsset(PhotoAssetCreate):
    id: UUID
    created_at: datetime


class SopRecord(BaseModel):
    id: UUID
    code: str
    category: str
    title: str
    version: str
    status: SopStatus
    trigger_condition: str
    steps: list[str] = Field(default_factory=list)
    completion_standard: str
    required_uploads: list[str] = Field(default_factory=list)
    exception_rule: str
    updated_at: datetime


class IssueReportCreate(BaseModel):
    reported_at: datetime
    category: str
    title: str
    description: str
    action_taken: str
    severity: Literal["low", "medium", "high"]
    blocks_service: bool = False
    needs_owner_decision: bool = True
    reported_by: str
    status: IssueStatus = "new"
    attachment_url: str | None = None


class IssueReport(IssueReportCreate):
    id: UUID
    created_at: datetime


class DashboardMetrics(BaseModel):
    work_date: date
    product_count: int
    task_total: int
    task_completed: int
    task_blocked: int
    test_count: int
    approved_test_count: int
    open_issue_count: int
    approved_sop_count: int


class OperationsDashboard(BaseModel):
    metrics: DashboardMetrics
    tasks: list[ShiftTask] = Field(default_factory=list)
    recent_purchases: list[PurchaseLog] = Field(default_factory=list)
    recent_batches: list[MarinadeBatch] = Field(default_factory=list)
    recent_tests: list[OvenTestRecord] = Field(default_factory=list)
    open_issues: list[IssueReport] = Field(default_factory=list)
    recent_photos: list[PhotoAsset] = Field(default_factory=list)
    sops: list[SopRecord] = Field(default_factory=list)
