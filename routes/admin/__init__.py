from flask import Blueprint

# 1. Creamos el Blueprint maestro
admin_bp = Blueprint('admin', __name__)

# 2. Importamos las rutas de los otros archivos para que se registren
# OJO: Estas importaciones DEBEN ir aquí abajo para evitar errores de "importación circular"
from . import dashboard, pacientes, doctores, recursos