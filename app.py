from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# OBLIGATORIO: Se requiere una clave secreta para usar sesiones y mensajes de flash
app.secret_key = 'super_secreta_healthnode_cambiar_luego'

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/ffinal'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 1. Definimos el modelo para poder consultar la tabla
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Capturamos lo que el usuario escribio en el HTML
        user_input = request.form.get('username')
        pass_input = request.form.get('password')

        # Buscamos en la base de datos
        usuario_db = Usuario.query.filter_by(username=user_input).first()

        # Verificamos si existe el usuario y si la clave coincide
        # NOTA: Por ahora comparamos texto plano porque asi esta en tu DB.
        # Una buena practica futura es usar werkzeug.security para hashear las claves.
        if usuario_db and usuario_db.password == pass_input:
            
            # Guardamos los datos en la sesion del navegador
            session['user_id'] = usuario_db.id
            session['rol'] = usuario_db.rol

            # Redirigimos dependiendo de su rol
            if usuario_db.rol == 'admin':
                return redirect(url_for('home_admin'))
            elif usuario_db.rol == 'doctor':
                return redirect(url_for('home_doctor'))
            elif usuario_db.rol == 'paciente':
                return redirect(url_for('home_paciente'))
        else:
            # Si falla, mandamos un error
            flash('Usuario o clave incorrectos. Intente nuevamente.')
            return redirect(url_for('index'))

    # Si es un GET normal, mostramos la pagina de login
    return render_template('inicio_sesion.html')

@app.route('/home_admin')
def home_admin():
    # Protegemos la ruta: si no hay sesion o no es admin, lo regresamos al login
    if 'user_id' not in session or session.get('rol') != 'admin':
        return redirect(url_for('index'))
    return render_template('home_admin.html')

@app.route('/home_doctor')
def home_doctor():
    if 'user_id' not in session or session.get('rol') != 'doctor':
        return redirect(url_for('index'))
    return render_template('home_doctor.html')

@app.route('/home_paciente')
def home_paciente():
    if 'user_id' not in session or session.get('rol') != 'paciente':
        return redirect(url_for('index'))
    return render_template('home_paciente.html')

# Ruta extra util para cerrar sesion
@app.route('/logout')
def logout():
    session.clear() # Borra todos los datos de la sesion
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)