from datetime import UTC, datetime


from src.api.v1.schemas.webhook import WebhookCreate, WebhookUpdate
from src.data.models.webhook_delivery import WebhookDelivery
from src.data.models.webhook_subscription import WebhookSubscription
from src.data.repositories.webhook_repository import WebhookRepository
from src.domain.exceptions import WebhookNotFoundError
from src.tasks.webhooks import send_webhook_delivery


class WebhookService:
    def __init__(
        self,
        webhook_repo: WebhookRepository
    ):
        self.webhook_repo = webhook_repo

    async def create_webhook(self, data: WebhookCreate) -> WebhookSubscription:
        subscription = WebhookSubscription(
            url=data.url,
            events=data.events,
            secret_key=data.secret_key,
            retry_count=data.retry_count,
            timeout=data.timeout,
        )
        return await self.webhook_repo.create(subscription)

    async def list_webhook(self) -> list[WebhookSubscription]:
        return await self.webhook_repo.list_all()


    async def get_webhooks(self, webhook_id: int) -> WebhookSubscription:
        webhook = await self.webhook_repo.get_by_id(webhook_id)
        if webhook is None:
            raise WebhookNotFoundError(f"WebhookSubscription {webhook_id} not found")
        return webhook


    async def update_webhook(self, webhook_id: int, data: WebhookUpdate) -> WebhookSubscription:
        webhook = await  self.webhook_repo.get_by_id(webhook_id)
        if webhook is None:
            raise WebhookNotFoundError(f"Webhook {webhook_id} not found")

        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(webhook, field, value)

        return await self.webhook_repo.update(webhook)

    async def delete_webhook(self, webhook_id: int) -> None:
        webhook = await self.webhook_repo.get_by_id(webhook_id)
        if webhook is None:
            raise WebhookNotFoundError(f"Webhook {webhook_id} not found")
        await self.webhook_repo.delete(webhook)

    async def list_deliveries(self, webhook_id: int) -> list[WebhookDelivery]:
        webhook = await self.webhook_repo.get_by_id(webhook_id)
        if webhook is None:
            raise WebhookNotFoundError(f"Webhook {webhook_id} not found")
        return await self.webhook_repo.list_deliveries_by_subscription(webhook_id)

    async def dispatch_event(self, event_type: str, data: dict) -> None:
        subscriptions = await self.webhook_repo.list_active_by_event(event_type)

        for subscription in subscriptions:
            payload = {
                "event": event_type,
                "data": data,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            delivery = WebhookDelivery(
                subscription_id=subscription.id,
                event_type=event_type,
                payload=payload,
                status="pending",
            )
            await self.webhook_repo.create_delivery(delivery)

            send_webhook_delivery.delay(delivery.id)