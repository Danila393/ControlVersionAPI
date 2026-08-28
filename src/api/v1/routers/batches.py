from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.batch import BatchCreate, BatchRead, BatchUpdate
from src.api.v1.schemas.product import ProductAggregateRequest, ProductRead, AggregateAsyncRequest
from src.api.v1.schemas.task import ReportRequest
from src.tasks.aggregation import aggregate_products_batch
from src.tasks.reports import generate_batch_report
from src.core.database import get_db
from src.data.repositories.batch_repository import BatchRepository
from src.data.repositories.product_repository import ProductRepository
from src.data.repositories.webhook_repository import WebhookRepository
from src.data.repositories.work_center_repository import WorkCenterRepository
from src.domain.services.batch_service import BatchService
from src.domain.services.product_service import ProductService
from src.domain.services.webhook_service import WebhookService
from src.domain.exceptions import (
    BatchAlreadyExistsError,
    BatchNotFoundError,
    ProductAlreadyAggregatedError,
    ProductNotFoundError,
)



router = APIRouter(prefix='/api/v1/batches', tags=['batches'])


@router.post("", response_model=list[BatchRead], status_code=status.HTTP_201_CREATED)
async def create_batches(
    payload: list[BatchCreate],
    session: AsyncSession = Depends(get_db),
):
    service = BatchService(
        batch_repo=BatchRepository(session),
        work_center_repo=WorkCenterRepository(session),
        webhook_service=WebhookService(webhook_repo=WebhookRepository(session)),
    )

    try:
        created = [await service.create_batch(item) for item in payload]
    except BatchAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    await session.commit()
    return created


@router.get("", response_model=list[BatchRead])
async def list_batches(
    is_closed: bool | None = None,
    batch_number: int | None = None,
    batch_date: date | None = None,
    work_center_id: str | None = None,
    shift: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    service = BatchService(
        batch_repo=BatchRepository(session),
        work_center_repo=WorkCenterRepository(session),
        webhook_service=WebhookService(webhook_repo=WebhookRepository(session)),
    )
    return await service.list_batches(
        is_closed=is_closed,
        batch_number=batch_number,
        batch_date=batch_date,
        work_center_identifier=work_center_id,
        shift=shift,
        offset=offset,
        limit=limit,
    )


@router.get("/{batch_id}", response_model=BatchRead)
async def get_batch(
    batch_id: int,
    session: AsyncSession = Depends(get_db),
):
    service = BatchService(
        batch_repo=BatchRepository(session),
        work_center_repo=WorkCenterRepository(session),
        webhook_service=WebhookService(webhook_repo=WebhookRepository(session)),
    )
    try:
        return await service.get_batch(batch_id)
    except BatchNotFoundError:
        raise HTTPException(status_code=404, detail="Партия не найдена")


@router.patch("/{batch_id}", response_model=BatchRead)
async def update_batch(
    batch_id: int,
    payload: BatchUpdate,
    session: AsyncSession = Depends(get_db),
):
    service = BatchService(
        batch_repo=BatchRepository(session),
        work_center_repo=WorkCenterRepository(session),
        webhook_service=WebhookService(webhook_repo=WebhookRepository(session)),
    )
    try:
        batch = await service.update_batch(batch_id, payload)
    except BatchNotFoundError:
        raise HTTPException(status_code=404, detail="Партия не найдена")

    await session.commit()
    return batch


@router.post("/{batch_id}/aggregate", response_model=ProductRead)
async def aggregate_product(
    batch_id: int,
    payload: ProductAggregateRequest,
    session: AsyncSession = Depends(get_db),
):
    service = ProductService(
        product_repo=ProductRepository(session),
        batch_repo=BatchRepository(session),
        webhook_service=WebhookService(webhook_repo=WebhookRepository(session)),
    )
    try:
        product = await service.aggregate_product(batch_id, payload.unique_code)
    except ProductNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ProductAlreadyAggregatedError as e:
        raise HTTPException(status_code=409, detail=str(e))

    await session.commit()
    return product


@router.post("/{batch_id}/aggregate-async", status_code=status.HTTP_202_ACCEPTED)
async def aggregate_async(
    batch_id: int,
    payload: AggregateAsyncRequest,
):
    result = aggregate_products_batch.delay(batch_id, payload.unique_codes)
    return {
        "task_id": result.id,
        "status": "PENDING",
        "message": "Aggregation task started",
    }


@router.post("/{batch_id}/reports", status_code=status.HTTP_202_ACCEPTED)
async def create_batch_report(
    batch_id: int,
    payload: ReportRequest,
):
    result = generate_batch_report.delay(batch_id, payload.format, payload.email)
    return {
        "task_id": result.id,
        "status": "PENDING",
    }