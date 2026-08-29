from tests.conftest import TestSessionLocal


async def _create_batch_and_products(client, batch_number: int, codes: list[str]) -> int:
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
    batch_id = response.json()[0]["id"]

    for code in codes:
        await client.post("/api/v1/products", json={"batch_id": batch_id, "unique_code": code})

    return batch_id


async def test_aggregate_products_batch_async(client, monkeypatch):
    # Задача открывает сессию сама через AsyncSessionLocal, минуя dependency
    # override клиента (тот работает только для Depends(get_db) в роутерах).
    import src.tasks.aggregation as aggregation_module

    monkeypatch.setattr(aggregation_module, "AsyncSessionLocal", TestSessionLocal)

    batch_id = await _create_batch_and_products(
        client, batch_number=301, codes=["A1", "A2", "A3"]
    )

    aggregated_count, errors = await aggregation_module._aggregate_products_batch_async(
        batch_id, ["A1", "A2", "UNKNOWN"]
    )

    assert aggregated_count == 2
    assert errors == [{"code": "UNKNOWN", "reason": "not found"}]
