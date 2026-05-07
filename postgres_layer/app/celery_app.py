"""Celery app — broker via REDIS_URL. Beat schedule for matchday jobs."""
from __future__ import annotations

import os

from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "footbail",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.match_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=30,
    task_max_retries=3,
)

# Beat schedule (Layer 4)
celery_app.conf.beat_schedule = {
    "create-recurring-match-instances": {
        "task": "app.tasks.match_tasks.create_recurring_match_instances",
        "schedule": crontab(hour=0, minute=30),  # 06:00 IST
    },
    "send-match-reminders-24h": {
        "task": "app.tasks.match_tasks.send_match_reminders_24h",
        "schedule": crontab(minute="*/30"),
    },
    "send-match-reminders-2h": {
        "task": "app.tasks.match_tasks.send_match_reminders_2h",
        "schedule": crontab(minute="*/30"),
    },
}
