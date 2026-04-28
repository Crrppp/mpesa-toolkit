# backend/celery_app.py
from celery import Celery
import os

broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("mpesa_tasks", broker=broker_url, backend=broker_url)
celery_app.conf.update(task_track_started=True)