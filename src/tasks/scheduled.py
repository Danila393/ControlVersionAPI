import asyncio
import sys
from datetime import datetime

from src.celery_app import celery_app
from src.core.cache import invalidate
from src.core.database import AsyncSessionLocal
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.webhook_repository import WebhookRepository
from src.domain.services.webhook_service import WebhookService
from src.tasks.webhooks import send_webhook_delivery

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def _auto_close_expired_batches_async() -> int:
    closed_count = 0

    async with AsyncSessionLocal() as session:
        batch_repo = BatchRepository(session)
        webhook_service = WebhookService(webhook_repo=WebhookRepository(session))

        now = datetime.now()
        expired_batches = await batch_repo.list_expired_open_batches(now)

        for batch in expired_batches:
            batch.is_closed = True
            batch.closed_at = now
            await batch_repo.update(batch)

            await webhook_service.dispatch_event(
                "batch_closed",
                {
                    "id": batch.id,
                    "batch_number": batch.batch_number,
                    "closed_at": str(batch.closed_at),
                },
            )
            await invalidate(f"batch_detail:{batch.id}")
            closed_count += 1

        await session.commit()

    if closed_count:
        await invalidate("batches_list")

    return closed_count


@celery_app.task
def auto_close_expired_batches() -> dict:
    """Запускается Celery Beat каждый день в 01:00."""
    closed_count = asyncio.run(_auto_close_expired_batches_async())
    return {"closed": closed_count}


async def _retry_failed_webhooks_async() -> int:
    async with AsyncSessionLocal() as session:
        repo = WebhookRepository(session)
        failed_deliveries = await repo.list_failed_deliveries()
        delivery_ids = [delivery.id for delivery in failed_deliveries]

    for delivery_id in delivery_ids:
        send_webhook_delivery.delay(delivery_id)

    return len(delivery_ids)


@celery_app.task
def retry_failed_webhooks() -> dict:
    """Запускается Celery Beat каждые 15 минут."""
    requeued_count = asyncio.run(_retry_failed_webhooks_async())
    return {"requeued": requeued_count}
