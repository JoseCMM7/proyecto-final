from flask import Blueprint, render_template, session, redirect, url_for

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/home_doctor')
def home():
    if session.get('rol') != 'doctor': return redirect(url_for('auth.login'))
    return render_template('home_doctor.html')