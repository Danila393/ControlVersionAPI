import asyncio
import sys

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.api.v1.routers.analytics import router as analytics_router
from src.api.v1.routers.batches import router as batches_router
from src.api.v1.routers.products import router as products_router
from src.api.v1.routers.tasks import router as tasks_router
from src.api.v1.routers.webhooks import router as webhooks_router
from src.core.exceptions import register_exception_handlers
from src.core.rate_limit import limiter

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


app = FastAPI(
    title="Production Control API",
    description="API системы контроля заданий на выпуск продукции",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

register_exception_handlers(app)

app.include_router(batches_router)
app.include_router(products_router)
app.include_router(webhooks_router)
app.include_router(tasks_router)
app.include_router(analytics_router)

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Проверяет, что приложение запущено и отвечает на запросы."""
    return {"status": "ok"}