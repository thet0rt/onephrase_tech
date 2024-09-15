# -*- coding: utf-8 -*-
from flask import Flask
from legacy import legacy_bp
import os
from db import db
app = Flask(__name__)
app.register_blueprint(legacy_bp, url_prefix='/')



connection_str = f"postgresql://{os.getenv('DB_USER')}:{'DB_PASSWORD'}@" \
                 f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/postgres"

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.getenv('DB_USER')}:{'DB_PASSWORD'}@"\
                                        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/postgres"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Регистрируем БП


# @app.get("/healthcheck1")
# def health_check_():
#     log.info("Healthcheck. Everything is fine. Have a good day!")
#     return Response("Healthcheck. Everything is fine. Have a good day!", status=200)


