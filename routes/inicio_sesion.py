from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Usuario

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_input = request.form.get('username')
        pass_input = request.form.get('password')
        user = Usuario.query.filter_by(username=user_input).first()

        if user and user.password == pass_input:
            session['user_id'] = user.id
            session['rol'] = user.rol
            
            # Redirección según el rol [cite: 63, 64, 65]
            if user.rol == 'admin': return redirect(url_for('admin.home'))
            if user.rol == 'doctor': return redirect(url_for('doctor.home'))
            if user.rol == 'paciente': return redirect(url_for('paciente.home'))
        
        flash('Usuario o clave incorrectos.')
    return render_template('inicio_sesion.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))