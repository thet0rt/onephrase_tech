from . import auth_bp
from flask import request, flash, redirect, url_for, render_template
from flask_login import login_user, logout_user
from db import db
from models import User


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.session.query(User).filter_by(username=username).one_or_none()

        if user and user.check_password(password):
            login_user(user)
            flash('Login successful', 'success')
            return redirect(url_for('homepage'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

# @auth_bp.route('/register')
# def register():
