from celery import Celery
from celery.schedules import crontab

from src.core.config import settings

celery_app = Celery(
    "production_control",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.tasks.aggregation",
        "src.tasks.webhooks",
        "src.tasks.scheduled",
        "src.tasks.reports",
        "src.tasks.imports",
        "src.tasks.exports",
    ],
)

# Beat только планирует задачи по расписанию, выполняет их обычный worker
celery_app.conf.beat_schedule = {
    "auto-close-expired-batches": {
        "task": "src.tasks.scheduled.auto_close_expired_batches",
        "schedule": crontab(hour=1, minute=0),
    },
    "retry-failed-webhooks": {
        "task": "src.tasks.scheduled.retry_failed_webhooks",
        "schedule": crontab(minute="*/15"),
    },
    "cleanup-old-files": {
        "task": "src.tasks.scheduled.cleanup_old_files",
        "schedule": crontab(hour=2, minute=0),
    },
    "update-cached-statistics": {
        "task": "src.tasks.scheduled.update_cached_statistics",
        "schedule": crontab(minute="*/5"),
    },
}