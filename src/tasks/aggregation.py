import asyncio
import sys

from src.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository
from src.domain.services.product_service import ProductService
from src.domain.exceptions import (
    ProductNotFoundError,
    ProductAlreadyAggregatedError,
)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def _aggregate_products_batch_async(
    batch_id: int, unique_codes: list[str]
) -> dict:
    aggregated_count = 0
    errors = []

    async with AsyncSessionLocal() as session:
        service = ProductService(
            product_repo=ProductRepository(session),
            batch_repo=BatchRepository(session),
        )

        for code in unique_codes:
            try:
                await service.aggregate_product(batch_id, code)
                aggregated_count += 1
            except ProductNotFoundError:
                errors.append({"code": code, "reason": "not found"})
            except ProductAlreadyAggregatedError:
                errors.append({"code": code, "reason": "already aggregated"})
            # Обрати внимание: НИЧЕГО не бросаем наружу (никаких raise/HTTPException) —
            # плохой код просто уходит в errors, а цикл идёт дальше к следующему.

        await session.commit()

    return aggregated_count, errors


@celery_app.task(bind=True, max_retries=3)
def aggregate_products_batch(
    self,
    batch_id: int,
    unique_codes: list[str],
    user_id: int | None = None,
) -> dict:
    aggregated, errors = asyncio.run(
        _aggregate_products_batch_async(batch_id, unique_codes)
    )
    total = len(unique_codes)
    return {
        "success": True,
        "total": total,
        "aggregated": aggregated,
        "failed": len(errors),
        "errors": errors,
    }
