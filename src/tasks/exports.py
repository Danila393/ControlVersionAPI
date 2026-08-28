import asyncio
import os
import sys
import tempfile
import uuid
from datetime import date

from openpyxl import Workbook

from src.celery_app import celery_app
from src.core.database import AsyncSessionLocal
from src.data.repositories.batch_repository import BatchRepository
from src.storage.minio_service import MinIOService

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def _export_batches_to_file_async(filters: dict, format: str = "excel") -> dict:
    batch_date = filters.get("batch_date")
    if batch_date:
        batch_date = date.fromisoformat(batch_date)
    date_from = filters.get("date_from")
    if date_from:
        date_from = date.fromisoformat(date_from)
    date_to = filters.get("date_to")
    if date_to:
        date_to = date.fromisoformat(date_to)

    async with AsyncSessionLocal() as session:
        batch_repo = BatchRepository(session)
        batches = await batch_repo.list_batches(
            is_closed=filters.get("is_closed"),
            batch_number=filters.get("batch_number"),
            batch_date=batch_date,
            batch_date_from=date_from,
            batch_date_to=date_to,
            work_center_identifier=filters.get("work_center_id"),
            shift=filters.get("shift"),
            offset=0,
            limit=100_000,
        )

    wb = Workbook()
    sheet = wb.active
    sheet.title = "Партии"
    sheet.append([
        "ID", "Номер партии", "Дата партии", "Статус", "Рабочий центр",
        "Смена", "Бригада", "Номенклатура", "Начало смены", "Окончание смены",
    ])
    for batch in batches:
        sheet.append([
            batch.id,
            batch.batch_number,
            str(batch.batch_date),
            "Закрыта" if batch.is_closed else "Открыта",
            batch.work_center.name,
            batch.shift,
            batch.team,
            batch.nomenclature,
            str(batch.shift_start),
            str(batch.shift_end),
        ])

    file_name = f"batches_export_{uuid.uuid4().hex[:8]}.xlsx"
    local_path = os.path.join(tempfile.gettempdir(), file_name)
    wb.save(local_path)

    try:
        storage = MinIOService()
        file_url = storage.upload_file(
            bucket="exports",
            file_path=local_path,
            object_name=file_name,
            expires_days=7,
        )
    finally:
        os.remove(local_path)

    return {
        "success": True,
        "file_url": file_url,
        "total_batches": len(batches),
    }


@celery_app.task
def export_batches_to_file(filters: dict, format: str = "excel") -> dict:
    return asyncio.run(_export_batches_to_file_async(filters, format))
