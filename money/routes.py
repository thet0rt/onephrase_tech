from . import money_bp
from flask_smorest import abort
from flask_login import login_required
from db import db
from models import Categories
from .schemas import CategorySchema


@money_bp.route("/category/add", methods=["POST"])
@login_required
@money_bp.arguments(CategorySchema)
def add_category(data):
    category = Categories.query.filter_by(description=data['description']).first()
    if category:
        abort(409, message='Category with this name already exists')
    new_category = Categories(
        description=data['description'],
        type=data['type']
    )
    db.session.add(new_category)
    db.session.commit()
    return data, 201
