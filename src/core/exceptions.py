import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("production_control")


def register_exception_handlers(app: FastAPI) -> None:
    """
    Ловит любое исключение, которое долетело до самого верха (то есть ни один
    роутер/сервис его не обработал) и превращает в чистый JSON вместо
    голого traceback'а с внутренностями кода, которые клиенту видеть не нужно.

    Сам traceback никуда не девается — он всё ещё пишется в лог сервера,
    просто наружу, в HTTP-ответ, он больше не утекает.
    """

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Внутренняя ошибка сервера"},
        )
