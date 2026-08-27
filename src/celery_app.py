from celery import Celery
from celery.schedules import crontab

from src.core.config import settings

celery_app = Celery(
    "production_control",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.tasks.aggregation", "src.tasks.webhooks", "src.tasks.scheduled"],
)

# beat_schedule — расписание для Celery Beat. Каждая запись говорит: "в такое-то
# время положи в очередь вот эту задачу" (Beat её только планирует, а
# выполняет её тот же worker, что и любую другую задачу из очереди).
celery_app.conf.beat_schedule = {
    "auto-close-expired-batches": {
        "task": "src.tasks.scheduled.auto_close_expired_batches",
        "schedule": crontab(hour=1, minute=0),
    },
    "retry-failed-webhooks": {
        "task": "src.tasks.scheduled.retry_failed_webhooks",
        "schedule": crontab(minute="*/15"),
    },
}