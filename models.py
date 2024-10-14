import enum
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from db import db


class BaseEnum(enum.Enum):

    def __str__(self):
        return str(self.value)


class CategoryType(BaseEnum):
    INCOME = 'INCOME'
    OUTCOME = 'OUTCOME'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(500), nullable=False)
    superuser = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_on = db.Column(db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return "<{}:{}>".format(self.id, self.username)


class Transaction(db.Model):

    __tablename__ = 'transactions'

    id = db.Column(db.Integer(), primary_key=True)
    created_by_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    category_id = db.Column(db.Integer(), db.ForeignKey('categories.id'))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    transaction_date = db.Column(db.DateTime(), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_by = db.relationship('User', backref='transactions')
    category = db.relationship('Category', backref='transactions')



class Category(db.Model):

    __tablename__ = 'categories'

    id = db.Column(db.Integer(), primary_key=True)
    description = db.Column(db.String(255), nullable=True)
    type = db.Column(db.Enum(CategoryType, name='category_type'), nullable=False)
