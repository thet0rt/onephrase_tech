from flask_smorest import Blueprint

money_bp = Blueprint('money', __name__)

from . import routes
