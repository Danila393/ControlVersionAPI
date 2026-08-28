def _batch_payload(batch_number: int = 1, work_center_identifier: str = "RC-TEST") -> dict:
    """
    Маленький помощник, а не фикстура — просто чтобы не копировать один и
    тот же длинный JSON в каждый тест. Параметр batch_number вынесен
    отдельно, потому что batch_number+batch_date вместе должны быть
    уникальны (see uq_batch_number_date) — разным тестам нужны разные
    номера, чтобы не мешать друг другу.
    """
    return {
        "СтатусЗакрытия": False,
        "ПредставлениеЗаданияНаСмену": "Тестовое задание",
        "РабочийЦентр": "Тестовый цех",
        "Смена": "1 смена",
        "Бригада": "Тестовая бригада",
        "НомерПартии": batch_number,
        "ДатаПартии": "2026-01-01",
        "Номенклатура": "Тестовая деталь",
        "КодЕКН": "EKN-TEST",
        "ИдентификаторРЦ": work_center_identifier,
        "ДатаВремяНачалаСмены": "2026-01-01T08:00:00",
        "ДатаВремяОкончанияСмены": "2026-01-01T20:00:00",
    }


async def test_create_batch_success(client):
    response = await client.post("/api/v1/batches", json=[_batch_payload(batch_number=1)])

    assert response.status_code == 201
    body = response.json()
    assert len(body) == 1
    assert body[0]["batch_number"] == 1
    assert body[0]["is_closed"] is False
    assert body[0]["products"] == []


async def test_create_batch_duplicate_returns_409(client):
    payload = [_batch_payload(batch_number=2)]

    first = await client.post("/api/v1/batches", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/batches", json=payload)
    assert second.status_code == 409


async def test_get_batch_not_found_returns_404(client):
    response = await client.get("/api/v1/batches/999999")

    assert response.status_code == 404


async def test_get_batch_success(client):
    created = await client.post("/api/v1/batches", json=[_batch_payload(batch_number=3)])
    batch_id = created.json()[0]["id"]

    response = await client.get(f"/api/v1/batches/{batch_id}")

    assert response.status_code == 200
    assert response.json()["id"] == batch_id


async def test_update_batch_closing_sets_closed_at(client):
    created = await client.post("/api/v1/batches", json=[_batch_payload(batch_number=4)])
    batch_id = created.json()[0]["id"]

    response = await client.patch(f"/api/v1/batches/{batch_id}", json={"is_closed": True})

    assert response.status_code == 200
    assert response.json()["is_closed"] is True
