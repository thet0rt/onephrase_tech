# -*- coding: utf-8 -*-
from flask import Flask
from legacy import legacy_bp
from auth import auth_bp
from administration import admin_bp
import os
from db import db
from flask_login import LoginManager

from models import User

app = Flask(__name__)
# Регистрируем БП

app.register_blueprint(legacy_bp, url_prefix='/')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')



connection_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
                 f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/postgres"

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = connection_str
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db.init_app(app)

# Инициируем логин-менеджер
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = '/auth/login'  # todo get_url


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
# @app.get("/healthcheck1")
# def health_check_():
#     log.info("Healthcheck. Everything is fine. Have a good day!")
#     return Response("Healthcheck. Everything is fine. Have a good day!", status=200)


