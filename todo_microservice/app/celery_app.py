import os
from celery import Celery
from celery.schedules import crontab

REDIS_HOST = os.getenv("REDIS_HOST", "redis_todo")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/2"

celery = Celery(
    "todo_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.celery_tasks"]
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)


celery.conf.beat_schedule = {
    "check-deadlines-every-5-minutes": {
        "task": "check_upcoming_deadlines",
        "schedule": crontab(minute="*/5"),
    },
    "cleanup-completed-tasks-every-hour": {
        "task": "cleanup_completed_tasks",
        "schedule": crontab(minute=0, hour="*"), 
    },
}