from flask import Flask
from models import db
# Importaciones ajustadas a tu estructura de carpetas
from routes.admin.admin import admin_bp 
from routes.inicio_sesion import auth_bp
from routes.doctor import doctor_bp
from routes.paciente import paciente_bp

app = Flask(__name__)
app.secret_key = 'healthnode_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/ffinal'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Registro de rutas
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(paciente_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)