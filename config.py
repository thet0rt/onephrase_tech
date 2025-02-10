from celery import Celery
import redis
import os

celery = Celery(
    broker=f"redis://redis:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DATABASES')}",
    backend=f"redis://redis:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DATABASES')}",
    include=["methods", "tasks"],
    timezone="Europe/Moscow",
)

r = redis.Redis(host="redis", port=os.getenv("REDIS_PORT"), db=0)
