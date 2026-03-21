from flask import Blueprint, render_template, session, redirect, url_for

paciente_bp = Blueprint('paciente', __name__)

@paciente_bp.route('/home_paciente')
def home():
    if session.get('rol') != 'paciente': return redirect(url_for('auth.login'))
    return render_template('home_paciente.html')