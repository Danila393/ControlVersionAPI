async def _create_webhook(client, url: str = "http://example.com/hook") -> dict:
    response = await client.post(
        "/api/v1/webhooks",
        json={"url": url, "events": ["batch_created"], "secret_key": "secret"},
    )
    return response.json()


async def test_create_webhook_success(client):
    response = await client.post(
        "/api/v1/webhooks",
        json={
            "url": "http://example.com/hook",
            "events": ["batch_created"],
            "secret_key": "s",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["url"] == "http://example.com/hook"
    assert body["is_active"] is True


async def test_list_webhooks(client):
    await _create_webhook(client, url="http://a.com")
    await _create_webhook(client, url="http://b.com")

    response = await client.get("/api/v1/webhooks")

    assert response.status_code == 200
    assert response.json()["total"] == 2


async def test_update_webhook_deactivate(client):
    webhook = await _create_webhook(client)

    response = await client.patch(
        f"/api/v1/webhooks/{webhook['id']}", json={"is_active": False}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


async def test_delete_webhook(client):
    webhook = await _create_webhook(client)

    delete_response = await client.delete(f"/api/v1/webhooks/{webhook['id']}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/webhooks/{webhook['id']}/deliveries")
    assert get_response.status_code == 404


async def test_delete_webhook_not_found(client):
    response = await client.delete("/api/v1/webhooks/999999")

    assert response.status_code == 404


async def test_list_deliveries_empty_for_new_webhook(client):
    webhook = await _create_webhook(client)

    response = await client.get(f"/api/v1/webhooks/{webhook['id']}/deliveries")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}
