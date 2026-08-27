from datetime import datetime, UTC
import asyncio
import sys
from src.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.data.repositories.webhook_repository import WebhookRepository
from src.utils.hmac_utils import sign_payload
import httpx


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def _send_webhook_delivery_async(delivery_id: int) -> dict:

    async with AsyncSessionLocal() as session:
        repo = WebhookRepository(session)
        delivery = await repo.get_delivery_by_id(delivery_id)
        if delivery is None:
            return {"success": False, "errors": "delivery not found"}

        signature = sign_payload(delivery.payload, delivery.subscription.secret_key)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    delivery.subscription.url,
                    json=delivery.payload,
                    headers={"X-Webhook-Signature": signature},
                    timeout=delivery.subscription.timeout,
                )
            except httpx.RequestError:
                delivery.status = "failed"
                delivery.attempts += 1
                delivery.error_message = "Не удалось подключиться "
            else:
                delivery.attempts += 1
                if 200 <= response.status_code < 300:
                    delivery.status = "success"
                    delivery.delivered_at = datetime.now(UTC)
                    delivery.response_status = response.status_code
                else:
                    delivery.status = "failed"
                    delivery.response_status = response.status_code
                    delivery.response_body = response.text

            await session.commit()

    return {"success": delivery.status == "success"}

@celery_app.task(bind=True, max_retries=3)
def send_webhook_delivery(self, delivery_id: int) -> dict:
    return asyncio.run(_send_webhook_delivery_async(delivery_id))


