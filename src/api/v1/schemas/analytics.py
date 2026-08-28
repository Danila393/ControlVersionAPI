from datetime import datetime, date
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