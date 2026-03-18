from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# CONFIGURACIÓN (La famosa línea 4 que me pediste):
# Aquí le decimos a Flask: "Oye, usa POSTGRES, con el usuario POSTGRES, sin contraseña, en mi compu local, en la base FINAL"
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres@localhost/final'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Esta línea conecta Flask con la base de datos usando la configuración de arriba
db = SQLAlchemy(app)

@app.route('/')
def index():
    return "<h1>¡Ya funcionó la conexión!</h1>"

if __name__ == '__main__':
    # Esto hace que tu página se vea en internet usando el puerto 5000
    app.run(host='0.0.0.0', port=5000, debug=True)