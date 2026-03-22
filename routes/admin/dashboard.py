from flask import render_template, session, redirect, url_for
from models import (
    Paciente, Administrador, HistorialEstado, 
    DispositivoGPS, DispositivoBeacon, DispositivoNFC
)
# Importamos el Blueprint desde __init__.py
from . import admin_bp

@admin_bp.route('/home_admin')
def home():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    total_p = Paciente.query.count()
    gps = DispositivoGPS.query.filter_by(estado_gps='Activo').count()
    beacons = DispositivoBeacon.query.filter_by(estado_beacon='Activo').count()
    nfc = DispositivoNFC.query.filter_by(estado_nfc='Activo').count()
    
    rojos = Paciente.query.join(HistorialEstado).filter(HistorialEstado.estado == 'ROJO', HistorialEstado.fecha_fin == None).all()
    amarillos = Paciente.query.join(HistorialEstado).filter(HistorialEstado.estado == 'AMARILLO', HistorialEstado.fecha_fin == None).all()

    return render_template('admin/home_admin.html', 
                           admin_nombre=admin.nombre if admin else "Admin",
                           total_pacientes="{:,}".format(total_p),
                           total_dispositivos="{:,}".format(gps+beacons+nfc),
                           pacientes_rojos_count=len(rojos),
                           pacientes_rojos=rojos,
                           pacientes_amarillos=amarillos)