from celery.result import AsyncResult
from fastapi import APIRouter

from src.api.v1.schemas.task import TaskStatusResponse
from src.celery_app import celery_app

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    async_result = AsyncResult(task_id, app=celery_app)  # создай AsyncResult, как я объяснил выше
    return TaskStatusResponse(
        task_id=task_id,
        status=async_result.status,  # у AsyncResult есть атрибут .status
        result=async_result.result if async_result.ready() else None,
    )