from datetime import UTC, datetime, timedelta

from src.core.cache import cached
from src.data.repositories.analytics_repository import AnalyticsRepository
from src.data.repositories.batch_repository import BatchRepository
from src.domain.exceptions import BatchNotFoundError
from src.api.v1.schemas.analytics import (
    BatchComparisonItem,
    BatchInfo,
    BatchStatisticsResponse,
    CompareBatchesAverage,
    CompareBatchesResponse,
    DashboardResponse,
    DashboardSummary,
    DashboardToday,
    ProductionStats,
    ShiftStats,
    TeamPerformance,
    Timeline,
    WorkCenterStats,
)


class AnalyticsService:
    def __init__(
        self,
        batch_repo: BatchRepository,
        analytics_repo: AnalyticsRepository | None = None,
    ):
        self.batch_repo = batch_repo
        self.analytics_repo = analytics_repo

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

    @cached(ttl=300, key_prefix="dashboard_stats")
    async def get_dashboard_statistics(self) -> dict:
        summary = await self.analytics_repo.get_summary()
        today_counts = await self.analytics_repo.get_today_counts(datetime.now(UTC).date())
        by_shift = await self.analytics_repo.get_by_shift()
        top_work_centers = await self.analytics_repo.get_top_work_centers()

        total_products = summary["total_products"]
        aggregated_products = summary["aggregated_products"]
        aggregation_rate = (
            aggregated_products / total_products * 100 if total_products > 0 else 0
        )

        response = DashboardResponse(
            summary=DashboardSummary(**summary, aggregation_rate=aggregation_rate),
            today=DashboardToday(**today_counts),
            by_shift={shift: ShiftStats(**stats) for shift, stats in by_shift.items()},
            top_work_centers=[WorkCenterStats(**wc) for wc in top_work_centers],
            cached_at=datetime.now(UTC),
        )
        # @cached хранит только JSON-совместимые данные (см. src/core/cache.py) —
        # ORM-объекты или произвольные Python-объекты туда не положить, а
        # Pydantic-модель через model_dump(mode="json") как раз превращается
        # в обычный dict, который json.dumps умеет сериализовать.
        return response.model_dump(mode="json")

    async def compare_batches(self, batch_ids: list[int]) -> CompareBatchesResponse:
        comparison = []

        for batch_id in batch_ids:
            batch = await self.batch_repo.get_by_id(batch_id)
            if batch is None:
                raise BatchNotFoundError(f"Batch {batch_id} not found")

            total = len(batch.products)
            aggregated_count = sum(1 for p in batch.products if p.is_aggregated)
            rate = aggregated_count / total * 100 if total > 0 else 0
            duration_hours = (batch.shift_end - batch.shift_start).total_seconds() / 3600
            products_per_hour = aggregated_count / duration_hours if duration_hours > 0 else 0

            comparison.append(
                BatchComparisonItem(
                    batch_id=batch.id,
                    batch_number=batch.batch_number,
                    total_products=total,
                    aggregated=aggregated_count,
                    rate=rate,
                    duration_hours=duration_hours,
                    products_per_hour=products_per_hour,
                )
            )

        if comparison:
            avg_rate = sum(item.rate for item in comparison) / len(comparison)
            avg_speed = sum(item.products_per_hour for item in comparison) / len(comparison)
        else:
            avg_rate = 0
            avg_speed = 0

        return CompareBatchesResponse(
            comparison=comparison,
            average=CompareBatchesAverage(
                aggregation_rate=avg_rate,
                products_per_hour=avg_speed,
            ),
        )
