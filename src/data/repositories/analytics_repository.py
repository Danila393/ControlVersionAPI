from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data.models.batch import Batch
from src.data.models.product import Product
from src.data.models.work_center import WorkCenter


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_summary(self) -> dict:
        total_batches = (await self.session.execute(select(func.count(Batch.id)))).scalar_one()
        active_batches = (
            await self.session.execute(
                select(func.count(Batch.id)).where(Batch.is_closed == False)
            )
        ).scalar_one()
        total_products = (await self.session.execute(select(func.count(Product.id)))).scalar_one()
        aggregated_products = (
            await self.session.execute(
                select(func.count(Product.id)).where(Product.is_aggregated == True)
            )
        ).scalar_one()

        return {
            "total_batches": total_batches,
            "active_batches": active_batches,
            "closed_batches": total_batches - active_batches,
            "total_products": total_products,
            "aggregated_products": aggregated_products,
        }

    async def get_today_counts(self, today: date) -> dict:
        batches_created = (
            await self.session.execute(
                select(func.count(Batch.id)).where(func.date(Batch.created_at) == today)
            )
        ).scalar_one()
        batches_closed = (
            await self.session.execute(
                select(func.count(Batch.id)).where(func.date(Batch.closed_at) == today)
            )
        ).scalar_one()
        products_added = (
            await self.session.execute(
                select(func.count(Product.id)).where(func.date(Product.created_at) == today)
            )
        ).scalar_one()
        products_aggregated = (
            await self.session.execute(
                select(func.count(Product.id)).where(func.date(Product.aggregated_at) == today)
            )
        ).scalar_one()

        return {
            "batches_created": batches_created,
            "batches_closed": batches_closed,
            "products_added": products_added,
            "products_aggregated": products_aggregated,
        }

    async def get_by_shift(self) -> dict[str, dict]:
        # Два отдельных запроса, а не один join — чтобы join батчей с продукцией
        # не задвоил подсчёт самих партий (у партии может быть много продукции).
        batches_per_shift = await self.session.execute(
            select(Batch.shift, func.count(Batch.id)).group_by(Batch.shift)
        )
        products_per_shift = await self.session.execute(
            select(
                Batch.shift,
                func.count(Product.id),
                func.sum(case((Product.is_aggregated == True, 1), else_=0)),
            )
            .select_from(Product)
            .join(Batch, Product.batch_id == Batch.id)
            .group_by(Batch.shift)
        )

        result: dict[str, dict] = {}
        for shift, batches_count in batches_per_shift:
            result[shift] = {"batches": batches_count, "products": 0, "aggregated": 0}
        for shift, products_count, aggregated_count in products_per_shift:
            result.setdefault(shift, {"batches": 0, "products": 0, "aggregated": 0})
            result[shift]["products"] = products_count
            result[shift]["aggregated"] = int(aggregated_count or 0)

        return result

    async def get_top_work_centers(self, limit: int = 5) -> list[dict]:
        batches_per_wc = await self.session.execute(
            select(WorkCenter.identifier, WorkCenter.name, func.count(Batch.id))
            .join(Batch, Batch.work_center_id == WorkCenter.id)
            .group_by(WorkCenter.id, WorkCenter.identifier, WorkCenter.name)
        )
        products_per_wc = await self.session.execute(
            select(
                WorkCenter.identifier,
                func.count(Product.id),
                func.sum(case((Product.is_aggregated == True, 1), else_=0)),
            )
            .select_from(Product)
            .join(Batch, Product.batch_id == Batch.id)
            .join(WorkCenter, Batch.work_center_id == WorkCenter.id)
            .group_by(WorkCenter.identifier)
        )
        products_by_identifier = {
            identifier: (products_count, int(aggregated_count or 0))
            for identifier, products_count, aggregated_count in products_per_wc
        }

        rows = []
        for identifier, name, batches_count in batches_per_wc:
            products_count, aggregated_count = products_by_identifier.get(identifier, (0, 0))
            aggregation_rate = (
                aggregated_count / products_count * 100 if products_count > 0 else 0
            )
            rows.append({
                "id": identifier,
                "name": name,
                "batches_count": batches_count,
                "products_count": products_count,
                "aggregation_rate": aggregation_rate,
            })

        rows.sort(key=lambda r: r["batches_count"], reverse=True)
        return rows[:limit]
