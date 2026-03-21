from flask import Blueprint, render_template, session, redirect, url_for
from models import (
    db, Usuario, Paciente, Administrador, HistorialEstado, 
    DispositivoGPS, DispositivoBeacon, DispositivoNFC, Doctor
)

# Definimos el blueprint para el administrador
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/home_admin')
def home():
    # 1. Seguridad: Solo permite el acceso si el rol es admin [cite: 46, 65]
    if session.get('rol') != 'admin':
        return redirect(url_for('auth.login'))

    # 2. Obtener nombre del administrador logueado [cite: 8, 65]
    admin_actual = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    admin_nombre = admin_actual.nombre if admin_actual else "Administrador"

    # 3. Estadísticas para las tarjetas superiores [cite: 41]
    total_pacientes_count = Paciente.query.count()
    total_pacientes_fmt = "{:,}".format(total_pacientes_count)

    # Conteo de dispositivos con estado 'Activo' [cite: 41, 66]
    gps_activos = DispositivoGPS.query.filter_by(estado_gps='Activo').count()
    beacons_activos = DispositivoBeacon.query.filter_by(estado_beacon='Activo').count()
    nfc_activos = DispositivoNFC.query.filter_by(estado_nfc='Activo').count()
    total_dispositivos_fmt = "{:,}".format(gps_activos + beacons_activos + nfc_activos)

    # 4. Consultas para las listas de alertas (Rojo y Amarillo) [cite: 41, 42]
    # Pacientes en Rojo (Atención inmediata)
    pacientes_rojos = Paciente.query.join(HistorialEstado).filter(
        HistorialEstado.estado == 'ROJO',
        HistorialEstado.fecha_fin == None
    ).all()
    pacientes_rojos_count = len(pacientes_rojos)

    # Pacientes en Amarillo (Monitoreo continuo)
    pacientes_amarillos = Paciente.query.join(HistorialEstado).filter(
        HistorialEstado.estado == 'AMARILLO',
        HistorialEstado.fecha_fin == None
    ).all()

    # Renderizamos apuntando a la subcarpeta 'admin/' 
    return render_template('admin/home_admin.html', 
                           admin_nombre=admin_nombre,
                           total_pacientes=total_pacientes_fmt,
                           total_dispositivos=total_dispositivos_fmt,
                           pacientes_rojos_count=pacientes_rojos_count,
                           pacientes_rojos=pacientes_rojos,
                           pacientes_amarillos=pacientes_amarillos)

@admin_bp.route('/pacientes')
def pacientes():
    # Seguridad [cite: 46]
    if session.get('rol') != 'admin':
        return redirect(url_for('auth.login'))

    # Nombre del admin [cite: 8, 65]
    admin_actual = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    admin_nombre = admin_actual.nombre if admin_actual else "Administrador"

    # Obtener todos los pacientes registrados [cite: 28, 30]
    pacientes_db = Paciente.query.all()
    pacientes_lista = []

    for p in pacientes_db:
        # Buscamos el estado más reciente del semáforo clínico [cite: 42]
        estado_actual = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
        color_estado = estado_actual.estado.lower() if estado_actual else 'verde'

        pacientes_lista.append({
            'id': p.id,
            'nombre': f"{p.nombre} {p.apellido}",
            'fecha_ingreso': p.fecha_ingreso.strftime('%d/%m/%Y'),
            'estado': color_estado
        })

    # Renderizamos la pestaña de listado de pacientes [cite: 7]
    return render_template('admin/admin_pacientes.html', 
                           admin_nombre=admin_nombre, 
                           pacientes=pacientes_lista)

@admin_bp.route('/doctores')
def doctores():
    if session.get('rol') != 'admin':
        return redirect(url_for('auth.login'))

    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    # CONSULTA REAL: Obtenemos todos los doctores de la base de datos
    doctores_db = Doctor.query.all()
    lista_doctores = []

    for d in doctores_db:
        lista_doctores.append({
            'nombre': f"{d.nombre} {d.apellido}",
            # Formateamos la fecha de contratación
            'fecha_ingreso': d.fecha_contratacion.strftime('%d/%m/%Y')
        })

    return render_template('admin/admin_doctores.html', 
                           admin_nombre=admin.nombre if admin else "Admin", 
                           doctores=lista_doctores)