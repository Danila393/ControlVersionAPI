from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.webhook import (
    WebhookCreate,
    WebhookDeliveryListResponse,
    WebhookListResponse,
    WebhookRead,
    WebhookUpdate,
)
from src.core.database import get_db
from src.data.repositories.webhook_repository import WebhookRepository
from src.domain.exceptions import WebhookNotFoundError
from src.domain.services.webhook_service import WebhookService

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookRead, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    payload: WebhookCreate,
    session: AsyncSession = Depends(get_db)
):
    service = WebhookService(
        webhook_repo=WebhookRepository(session),
    )
    webhooks = await service.create_webhook(payload)

    await session.commit()
    return webhooks


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    session: AsyncSession = Depends(get_db),
):
    service = WebhookService(webhook_repo=WebhookRepository(session))
    webhooks = await service.list_webhook()
    return WebhookListResponse(items=webhooks, total=len(webhooks))


@router.patch("/{webhook_id}", response_model=WebhookRead)
async def update_webhooks(
        webhook_id: int,
        payload: WebhookUpdate,
        session: AsyncSession = Depends(get_db),
):
    service = WebhookService(
        webhook_repo=WebhookRepository(session),
    )
    try:
        webhook = await service.update_webhook(webhook_id, payload)
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} не найден")

    await session.commit()
    return webhook


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = WebhookService(
        webhook_repo=WebhookRepository(session),
    )
    try:
        await service.delete_webhook(webhook_id)
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} не найден")

    await session.commit()


@router.get("/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def list_webhook_deliveries(
    webhook_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = WebhookService(
        webhook_repo=WebhookRepository(session),
    )
    try:
        deliveries = await service.list_deliveries(webhook_id)
    except WebhookNotFoundError:
        raise HTTPException(status_code=404, detail=f"Webhook {webhook_id} не найден")

    return WebhookDeliveryListResponse(items=deliveries, total=len(deliveries))