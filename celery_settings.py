from celery import Celery
import os


print({os.getenv('REDIS_HOST')})
celery = Celery(
    broker=f"redis://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DATABASES')}",
    backend=f"redis://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DATABASES')}",
    include=["methods", "tasks", "products.products"],
    timezone="Europe/Moscow",
)

celery.conf.task_default_queue = "default"
celery.conf.task_queues = {
    "default": {"exchange": "default", "routing_key": "default"},
    "priority": {"exchange": "priority", "routing_key": "priority"},
}
