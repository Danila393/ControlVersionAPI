from datetime import date, datetime

from pydantic import BaseModel


class BatchInfo(BaseModel):
    id: int
    batch_number: int
    batch_date: date
    is_closed: bool | None = None


class ProductionStats(BaseModel):
    total_products: int
    aggregated: int
    remaining: int
    aggregation_rate: float


class Timeline(BaseModel):
    shift_duration_hours: float
    elapsed_hours: float
    products_per_hour: float
    estimated_completion: datetime | None


class TeamPerformance(BaseModel):
    team: str
    avg_products_per_hour: float
    efficiency_score: float


class BatchStatisticsResponse(BaseModel):
    batch_info: BatchInfo
    production_stats: ProductionStats
    timeline: Timeline
    team_performance: TeamPerformance


class DashboardSummary(BaseModel):
    total_batches: int
    active_batches: int
    closed_batches: int
    total_products: int
    aggregated_products: int
    aggregation_rate: float


class DashboardToday(BaseModel):
    batches_created: int
    batches_closed: int
    products_added: int
    products_aggregated: int


class ShiftStats(BaseModel):
    batches: int
    products: int
    aggregated: int


class WorkCenterStats(BaseModel):
    id: str
    name: str
    batches_count: int
    products_count: int
    aggregation_rate: float


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    today: DashboardToday
    by_shift: dict[str, ShiftStats]
    top_work_centers: list[WorkCenterStats]
    cached_at: datetime


class CompareBatchesRequest(BaseModel):
    batch_ids: list[int]


class BatchComparisonItem(BaseModel):
    batch_id: int
    batch_number: int
    total_products: int
    aggregated: int
    rate: float
    duration_hours: float
    products_per_hour: float


class CompareBatchesAverage(BaseModel):
    aggregation_rate: float
    products_per_hour: float


class CompareBatchesResponse(BaseModel):
    comparison: list[BatchComparisonItem]
    average: CompareBatchesAverage