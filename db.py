from flask_sqlalchemy import SQLAlchemy
import redis
import os

db = SQLAlchemy()
r = redis.Redis(host={os.getenv('REDIS_HOST')}, port=int(os.getenv("REDIS_PORT")), db=0)
