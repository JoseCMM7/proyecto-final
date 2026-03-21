from flask import Blueprint, render_template, session, redirect, url_for
from models import Usuario, Paciente, HistorialEstado, DispositivoGPS, DispositivoBeacon, DispositivoNFC, Administrador

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/home_admin')
def home():
    if session.get('rol') != 'admin':
        return redirect(url_for('auth.login'))

    # 1. Consultar el nombre real del administrador
    admin_actual = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    admin_nombre = admin_actual.nombre if admin_actual else "Administrador"

    # 2. Consultas de tarjetas
    total_pacientes_count = Paciente.query.count()
    total_pacientes_fmt = "{:,}".format(total_pacientes_count)

    gps_activos = DispositivoGPS.query.filter_by(estado_gps='Activo').count()
    beacons_activos = DispositivoBeacon.query.filter_by(estado_beacon='Activo').count()
    nfc_activos = DispositivoNFC.query.filter_by(estado_nfc='Activo').count()
    total_dispositivos_fmt = "{:,}".format(gps_activos + beacons_activos + nfc_activos)

    # 3. Consultas de pacientes
    pacientes_rojos = Paciente.query.join(HistorialEstado).filter(
        HistorialEstado.estado == 'ROJO',
        HistorialEstado.fecha_fin == None
    ).all()
    pacientes_rojos_count = len(pacientes_rojos)

    pacientes_amarillos = Paciente.query.join(HistorialEstado).filter(
        HistorialEstado.estado == 'AMARILLO',
        HistorialEstado.fecha_fin == None
    ).all()

    return render_template('home_admin.html', 
                           admin_nombre=admin_nombre,
                           total_pacientes=total_pacientes_fmt,
                           total_dispositivos=total_dispositivos_fmt,
                           pacientes_rojos_count=pacientes_rojos_count,
                           pacientes_rojos=pacientes_rojos,
                           pacientes_amarillos=pacientes_amarillos)