from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.data.models.webhook_subscription import WebhookSubscription
from src.data.models.webhook_delivery import WebhookDelivery


class WebhookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, subscription: WebhookSubscription) -> WebhookSubscription:
        self.session.add(subscription)
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            raise
        return subscription

    async def list_all(self) -> list[WebhookSubscription]:
        result = await self.session.execute(
            select(WebhookSubscription)
        )
        return list(result.scalars().all())

    async def get_by_id(self, webhook_id: int) -> WebhookSubscription | None:
        result = await self.session.execute(
            select(WebhookSubscription)
            .where(WebhookSubscription.id == webhook_id)
        )
        return result.scalar_one_or_none()

    async def update(self, subscription: WebhookSubscription) -> WebhookSubscription:
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            raise
        return subscription

    async def delete(self, subscription: WebhookSubscription) -> None:
        await self.session.delete(subscription)
        await self.session.flush()

    async def list_deliveries_by_subscription(
        self, subscription_id: int
    ) -> list[WebhookDelivery]:
        result = await self.session.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
        )
        return list(result.scalars().all())