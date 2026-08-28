from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.schemas.analytics import (
    CompareBatchesRequest,
    CompareBatchesResponse,
    DashboardResponse,
)
from src.core.database import get_db
from src.data.repositories.analytics_repository import AnalyticsRepository
from src.data.repositories.batch_repository import BatchRepository
from src.domain.exceptions import BatchNotFoundError
from src.domain.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(session: AsyncSession = Depends(get_db)):
    service = AnalyticsService(
        batch_repo=BatchRepository(session),
        analytics_repo=AnalyticsRepository(session),
    )
    return await service.get_dashboard_statistics()


@router.post("/compare-batches", response_model=CompareBatchesResponse)
async def compare_batches(
    payload: CompareBatchesRequest,
    session: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(batch_repo=BatchRepository(session))
    try:
        return await service.compare_batches(payload.batch_ids)
    except BatchNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
