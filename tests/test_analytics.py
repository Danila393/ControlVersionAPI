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


async def test_dashboard_returns_summary_shape(client):
    await _create_batch(client, batch_number=201)

    response = await client.get("/api/v1/analytics/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total_batches"] == 1
    assert "today" in body
    assert "by_shift" in body
    assert "top_work_centers" in body


async def test_compare_batches(client):
    batch_id_1 = await _create_batch(client, batch_number=202)
    batch_id_2 = await _create_batch(client, batch_number=203)

    response = await client.post(
        "/api/v1/analytics/compare-batches",
        json={"batch_ids": [batch_id_1, batch_id_2]},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["comparison"]) == 2
    assert "average" in body


async def test_compare_batches_unknown_id_returns_404(client):
    batch_id = await _create_batch(client, batch_number=204)

    response = await client.post(
        "/api/v1/analytics/compare-batches",
        json={"batch_ids": [batch_id, 999999]},
    )

    assert response.status_code == 404
