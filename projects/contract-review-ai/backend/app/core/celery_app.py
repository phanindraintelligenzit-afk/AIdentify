from celery import Celery
from celery.signals import worker_ready, worker_shutdown
import structlog

from app.core.config import settings

logger = structlog.get_logger()

celery_app = Celery(
    "contract_review",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.contract_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3000,  # 50 min soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    result_expires=86400,  # 24 hours
    beat_schedule={},
)


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    logger.info("celery_worker_ready", worker=sender.hostname)


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    logger.info("celery_worker_shutdown", worker=sender.hostname)


# Task routing
celery_app.conf.task_routes = {
    "app.tasks.contract_tasks.process_contract": {"queue": "contracts"},
    "app.tasks.contract_tasks.batch_process": {"queue": "contracts"},
}