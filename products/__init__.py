from flask_smorest import Blueprint

products_bp = Blueprint('products', __name__)

from . import routes
