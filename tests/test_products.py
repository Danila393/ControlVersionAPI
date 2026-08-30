async def _create_batch(client, batch_number: int) -> int:
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
    return response.json()[0]["id"]


async def test_create_product_success(client):
    batch_id = await _create_batch(client, batch_number=101)

    response = await client.post(
        "/api/v1/products", json={"batch_id": batch_id, "unique_code": "CODE001"}
    )

    assert response.status_code == 201
    assert response.json()["unique_code"] == "CODE001"
    assert response.json()["is_aggregated"] is False


async def test_create_product_duplicate_code_returns_409(client):
    batch_id = await _create_batch(client, batch_number=102)
    payload = {"batch_id": batch_id, "unique_code": "CODE002"}

    first = await client.post("/api/v1/products", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/products", json=payload)
    assert second.status_code == 409


async def test_aggregate_product_success(client):
    batch_id = await _create_batch(client, batch_number=103)
    await client.post(
        "/api/v1/products", json={"batch_id": batch_id, "unique_code": "CODE003"}
    )

    response = await client.post(
        f"/api/v1/batches/{batch_id}/aggregate", json={"unique_code": "CODE003"}
    )

    assert response.status_code == 200
    assert response.json()["is_aggregated"] is True
    assert response.json()["aggregated_at"] is not None


async def test_aggregate_product_twice_returns_409(client):
    batch_id = await _create_batch(client, batch_number=104)
    await client.post(
        "/api/v1/products", json={"batch_id": batch_id, "unique_code": "CODE004"}
    )

    first = await client.post(
        f"/api/v1/batches/{batch_id}/aggregate", json={"unique_code": "CODE004"}
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/v1/batches/{batch_id}/aggregate", json={"unique_code": "CODE004"}
    )
    assert second.status_code == 409


async def test_aggregate_unknown_code_returns_404(client):
    batch_id = await _create_batch(client, batch_number=105)

    response = await client.post(
        f"/api/v1/batches/{batch_id}/aggregate", json={"unique_code": "NOPE"}
    )

    assert response.status_code == 404
