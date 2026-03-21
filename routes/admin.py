from flask import Blueprint, render_template, session, redirect, url_for

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/home_admin')
def home():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    return render_template('home_admin.html')