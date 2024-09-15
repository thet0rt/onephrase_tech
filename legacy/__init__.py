from flask import Blueprint

legacy_bp = Blueprint('legacy', __name__)

from . import routes
