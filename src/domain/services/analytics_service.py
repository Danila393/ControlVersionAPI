from datetime import datetime, timedelta

from src.data.repositories.batch_repository import BatchRepository
from src.domain.exceptions import BatchNotFoundError
from src.api.v1.schemas.analytics import (
    BatchInfo,
    BatchStatisticsResponse,
    ProductionStats,
    TeamPerformance,
    Timeline,
)


class AnalyticsService:
    def __init__(self, batch_repo: BatchRepository):
        self.batch_repo = batch_repo

    async def get_batch_statistics(self, batch_id: int) -> BatchStatisticsResponse:
        batch = await self.batch_repo.get_by_id(batch_id)
        if batch is None:
            raise BatchNotFoundError(f"Batch {batch_id} not found")

        total = len(batch.products)
        aggregated_count = sum(1 for p in batch.products if p.is_aggregated)
        aggregation_rate = aggregated_count / total * 100 if total > 0 else 0

        shift_hours = (batch.shift_end - batch.shift_start).total_seconds() / 3600
        products_per_hour = aggregated_count / shift_hours if shift_hours > 0 else 0

        raw_elapsed_hours = (datetime.now() - batch.shift_start).total_seconds() / 3600
        elapsed_hours = max(0, min(raw_elapsed_hours, shift_hours))

        estimated_completion = None
        if total > 0 and products_per_hour > 0:
            estimated_completion = batch.shift_start + timedelta(hours=total / products_per_hour)

        return BatchStatisticsResponse(
            batch_info=BatchInfo(
                id=batch.id,
                batch_number=batch.batch_number,
                batch_date=batch.batch_date,
                is_closed=batch.is_closed,
            ),
            production_stats=ProductionStats(
                total_products=total,
                aggregated=aggregated_count,
                remaining=total - aggregated_count,
                aggregation_rate=aggregation_rate,
            ),
            timeline=Timeline(
                shift_duration_hours=shift_hours,
                elapsed_hours=elapsed_hours,
                products_per_hour=products_per_hour,
                estimated_completion=estimated_completion,
            ),
            team_performance=TeamPerformance(
                team=batch.team,
                avg_products_per_hour=products_per_hour,
                efficiency_score=aggregation_rate,
            ),
        )
