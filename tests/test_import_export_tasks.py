import csv
import os
import tempfile
import uuid
from urllib.parse import urlparse

from openpyxl import Workbook

from src.storage.minio_service import MinIOService
from tests.conftest import TestSessionLocal


async def _create_batch(client, batch_number: int) -> int:
    payload = [{
        "СтатусЗакрытия": False,
        "ПредставлениеЗаданияНаСмену": "Тестовое задание",
        "РабочийЦентр": "Тестовый цех",
        "Смена": "1 смена",
        "Бригада": "Тестовая бригада",
        "НомерПартии": batch_number,
        "ДатаПартии": "2026-01-01",
        "Номенклатура": "Тестовая деталь",
        "КодЕКН": "EKN-TEST",
        "ИдентификаторРЦ": "RC-TEST",
        "ДатаВремяНачалаСмены": "2026-01-01T08:00:00",
        "ДатаВремяОкончанияСмены": "2026-01-01T20:00:00",
    }]
    response = await client.post("/api/v1/batches", json=payload)
    return response.json()[0]["id"]


def _upload_import_file(rows: list[list], extension: str) -> str:
    header = [
        "НомерПартии", "ДатаПартии", "Номенклатура", "РабочийЦентр",
        "ИдентификаторРЦ", "Смена", "Бригада", "КодЕКН",
        "ПредставлениеЗаданияНаСмену", "ДатаВремяНачалаСмены", "ДатаВремяОкончанияСмены",
    ]
    local_path = os.path.join(tempfile.gettempdir(), f"pytest_import_{uuid.uuid4().hex[:8]}.{extension}")

    if extension == "csv":
        with open(local_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(header)
            writer.writerows(rows)
    else:
        wb = Workbook()
        sheet = wb.active
        sheet.append(header)
        for row in rows:
            sheet.append(row)
        wb.save(local_path)

    object_name = f"pytest_{uuid.uuid4().hex[:8]}.{extension}"
    storage = MinIOService()
    storage.client.fput_object(bucket_name="imports", object_name=object_name, file_path=local_path)
    os.remove(local_path)
    return object_name


def _row(batch_number: int) -> list:
    return [
        batch_number, "2026-01-01", "Импорт деталь", "Импорт цех", "RC-IMPORT",
        "1 смена", "Бригада", "EKN-IMPORT", "Задание", "2026-01-01T08:00:00", "2026-01-01T20:00:00",
    ]


async def test_import_batches_from_excel(monkeypatch):
    import src.tasks.imports as imports_module

    monkeypatch.setattr(imports_module, "AsyncSessionLocal", TestSessionLocal)

    object_name = _upload_import_file([_row(701)], "xlsx")

    result = await imports_module._import_batches_from_file_async(object_name, user_id=None)

    assert result == {
        "success": True,
        "total_rows": 1,
        "created": 1,
        "skipped": 0,
        "errors": [],
    }

    MinIOService().delete_file("imports", object_name)


async def test_import_batches_from_csv(monkeypatch):
    import src.tasks.imports as imports_module

    monkeypatch.setattr(imports_module, "AsyncSessionLocal", TestSessionLocal)

    object_name = _upload_import_file([_row(702), _row(703)], "csv")

    result = await imports_module._import_batches_from_file_async(object_name, user_id=None)

    assert result["created"] == 2
    assert result["skipped"] == 0

    MinIOService().delete_file("imports", object_name)


async def test_import_batches_duplicate_row_is_skipped(client, monkeypatch):
    import src.tasks.imports as imports_module

    monkeypatch.setattr(imports_module, "AsyncSessionLocal", TestSessionLocal)

    await _create_batch(client, batch_number=704)
    object_name = _upload_import_file([_row(704)], "xlsx")

    result = await imports_module._import_batches_from_file_async(object_name, user_id=None)

    assert result["created"] == 0
    assert result["skipped"] == 1
    assert result["errors"][0]["error"] == "Duplicate batch number and date"

    MinIOService().delete_file("imports", object_name)


async def test_export_batches_to_excel(client, monkeypatch):
    import src.tasks.exports as exports_module

    monkeypatch.setattr(exports_module, "AsyncSessionLocal", TestSessionLocal)

    await _create_batch(client, batch_number=705)

    result = await exports_module._export_batches_to_file_async(
        {"batch_number": 705}, format="excel"
    )

    assert result["success"] is True
    assert result["total_batches"] == 1

    object_name = os.path.basename(urlparse(result["file_url"]).path)
    MinIOService().delete_file("exports", object_name)


async def test_export_batches_to_csv(client, monkeypatch):
    import src.tasks.exports as exports_module

    monkeypatch.setattr(exports_module, "AsyncSessionLocal", TestSessionLocal)

    await _create_batch(client, batch_number=706)

    result = await exports_module._export_batches_to_file_async(
        {"batch_number": 706}, format="csv"
    )

    assert result["success"] is True
    assert result["total_batches"] == 1

    object_name = os.path.basename(urlparse(result["file_url"]).path)
    assert object_name.endswith(".csv")
    MinIOService().delete_file("exports", object_name)
