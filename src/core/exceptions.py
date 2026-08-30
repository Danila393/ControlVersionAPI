import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("production_control")


def register_exception_handlers(app: FastAPI) -> None:
    """Ловит необработанные исключения и возвращает клиенту чистый 500 вместо
    traceback'а; сам traceback по-прежнему пишется в лог сервера."""

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(
            "Unhandled exception on %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Внутренняя ошибка сервера"},
        )
