from datetime import datetime as dt

from sqlalchemy.orm import joinedload

import models
from . import money_bp
from flask_smorest import abort
from flask import request
from flask_login import login_required, current_user
from db import db
from models import Category, Transaction
from .schemas import CategorySchema, TransactionSchema


@money_bp.route("/category/add", methods=["POST"])
@login_required
@money_bp.arguments(CategorySchema)
def add_category(data):
    category = Category.query.filter_by(description=data['description']).first()
    if category:
        abort(409, message='Category with this name already exists')
    new_category = Category(
        description=data['description'],
        type=data['type']
    )
    db.session.add(new_category)
    db.session.commit()
    return data, 201


@money_bp.route("/transaction/add", methods=["POST"])
@login_required
@money_bp.arguments(TransactionSchema)
def add_transaction(data):
    user_id = current_user.id
    category = Category.query.filter_by(id=data['category_id']).one_or_none()
    if not category:
        abort(404, message='Category not found')

    new_transaction = Transaction(
        created_by_id=user_id,
        category_id=data['category_id'],
        amount=data['amount'],
        transaction_date=dt.now(),
        description=data.get('description', '')
    )
    db.session.add(new_transaction)
    db.session.commit()
    return data, 201


@money_bp.route("/transaction/all", methods=["GET"])
@login_required
@money_bp.response(200, TransactionSchema(many=True))
def get_transactions():
    user_id = current_user.id
    transactions = Transaction.query.options(joinedload(Transaction.category)).filter_by(created_by_id=user_id).all()
    return transactions
