from flask_sqlalchemy import SQLAlchemy
import redis
import os

db = SQLAlchemy()
r = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=os.getenv('REDIS_PORT'),
    password=os.getenv('REDIS_PASSWORD'),
    db=0
)
