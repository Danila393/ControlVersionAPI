from src.storage.minio_service import MinIOService
from tests.conftest import TestSessionLocal


async def _create_batch_and_products(
    client, batch_number: int, codes: list[str]
) -> int:
    payload = [
        {
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
        }
    ]
    response = await client.post("/api/v1/batches", json=payload)
    batch_id = response.json()[0]["id"]

    for code in codes:
        await client.post(
            "/api/v1/products", json={"batch_id": batch_id, "unique_code": code}
        )
    if codes:
        await client.post(
            f"/api/v1/batches/{batch_id}/aggregate", json={"unique_code": codes[0]}
        )

    return batch_id


async def test_generate_batch_report_excel(client, monkeypatch):
    import src.tasks.reports as reports_module

    monkeypatch.setattr(reports_module, "AsyncSessionLocal", TestSessionLocal)

    batch_id = await _create_batch_and_products(
        client, batch_number=401, codes=["R1", "R2"]
    )

    result = await reports_module._generate_batch_report_async(batch_id, format="excel")

    assert result["success"] is True
    assert result["file_name"].endswith(".xlsx")
    assert result["file_size"] > 0

    MinIOService().delete_file("reports", result["file_name"])


async def test_generate_batch_report_pdf(client, monkeypatch):
    import src.tasks.reports as reports_module

    monkeypatch.setattr(reports_module, "AsyncSessionLocal", TestSessionLocal)

    batch_id = await _create_batch_and_products(client, batch_number=402, codes=["R3"])

    result = await reports_module._generate_batch_report_async(batch_id, format="pdf")

    assert result["success"] is True
    assert result["file_name"].endswith(".pdf")

    MinIOService().delete_file("reports", result["file_name"])


async def test_generate_batch_report_not_found(monkeypatch):
    import src.tasks.reports as reports_module

    monkeypatch.setattr(reports_module, "AsyncSessionLocal", TestSessionLocal)

    result = await reports_module._generate_batch_report_async(999999, format="excel")

    assert result == {"success": False, "error": "Batch 999999 not found"}
