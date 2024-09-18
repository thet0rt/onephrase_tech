from . import admin_bp
from flask import render_template
from flask_login import login_required

@login_required
@admin_bp.route('/homepage', methods=['GET'])
def homepage():
    return render_template('home.html')
