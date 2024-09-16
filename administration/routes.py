from . import admin_bp
from flask import request, Response, flash, redirect, url_for, render_template
from flask_login import login_user
from db import db
from models import User


@admin_bp.route('/homepage', methods=['GET'])
def homepage():
    return render_template('home.html')