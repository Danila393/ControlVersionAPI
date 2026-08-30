import http.server
import threading
from typing import ClassVar

import pytest

from src.data.models.webhook_delivery import WebhookDelivery
from src.data.models.webhook_subscription import WebhookSubscription
from src.data.repositories.webhook_repository import WebhookRepository
from tests.conftest import TestSessionLocal


class _Handler(http.server.BaseHTTPRequestHandler):
    received: ClassVar[list[bytes]] = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.__class__.received.append(self.rfile.read(length))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def log_message(self, format, *args):
        pass


@pytest.fixture
def local_receiver():
    _Handler.received = []
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}", _Handler

    server.shutdown()
    thread.join(timeout=2)


async def _create_delivery(url: str, timeout: int = 5) -> int:
    async with TestSessionLocal() as session:
        repo = WebhookRepository(session)
        subscription = WebhookSubscription(
            url=url, events=["x"], secret_key="secret", is_active=True, timeout=timeout
        )
        await repo.create(subscription)

        delivery = WebhookDelivery(
            subscription_id=subscription.id,
            event_type="x",
            payload={"event": "x", "data": {"a": 1}},
            status="pending",
        )
        await repo.create_delivery(delivery)
        await session.commit()
        return delivery.id


async def test_send_webhook_delivery_success(monkeypatch, local_receiver):
    import src.tasks.webhooks as webhooks_module

    monkeypatch.setattr(webhooks_module, "AsyncSessionLocal", TestSessionLocal)

    url, handler = local_receiver
    delivery_id = await _create_delivery(url)

    result = await webhooks_module._send_webhook_delivery_async(delivery_id)

    assert result == {"success": True}
    assert len(handler.received) == 1

    async with TestSessionLocal() as session:
        repo = WebhookRepository(session)
        delivery = await repo.get_delivery_by_id(delivery_id)
        assert delivery.status == "success"
        assert delivery.response_status == 200
        assert delivery.delivered_at is not None


async def test_send_webhook_delivery_unreachable_raises_retryable(monkeypatch):
    import src.tasks.webhooks as webhooks_module

    monkeypatch.setattr(webhooks_module, "AsyncSessionLocal", TestSessionLocal)

    delivery_id = await _create_delivery("http://127.0.0.1:1", timeout=1)

    with pytest.raises(webhooks_module.RetryableDeliveryError):
        await webhooks_module._send_webhook_delivery_async(delivery_id)

    async with TestSessionLocal() as session:
        repo = WebhookRepository(session)
        delivery = await repo.get_delivery_by_id(delivery_id)
        assert delivery.status == "failed"
        assert delivery.attempts == 1
        assert delivery.error_message
