# -*- coding: utf-8 -*-
from flask import Flask
from legacy import legacy_bp
from auth import auth_bp
from administration import admin_bp
import os
from db import db
from flask_login import LoginManager
from flask_smorest import Api
from log_settings import Logging
from flask_cors import CORS


from models import User
from money import money_bp

app = Flask(__name__)


connection_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
                 f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/postgres"

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = connection_str
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db.init_app(app)

CORS(app, resources={r"/*": {"origins": "*"}})

# api
app.config["API_TITLE"] = "Onephrase api"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.0.2"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_JSON_PATH"] = "api-spec.json"
app.config["OPENAPI_SWAGGER_UI_PATH"] = os.getenv('OPENAPI_SWAGGER_UI_PATH')
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

logging = Logging()
logging.init_app(app)

api = Api(app)

# Регистрируем БП

api.register_blueprint(legacy_bp, url_prefix='/')
api.register_blueprint(auth_bp, url_prefix='/auth')
api.register_blueprint(admin_bp, url_prefix='/admin')
api.register_blueprint(money_bp, url_prefix='/money')

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


