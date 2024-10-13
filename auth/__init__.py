from flask_smorest import Blueprint

auth_bp = Blueprint('auth', __name__)

from . import routes
