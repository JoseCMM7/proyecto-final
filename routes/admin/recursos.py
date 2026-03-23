from flask import render_template, session, redirect, url_for, request, flash
from datetime import date, datetime
from models import (
    db, Administrador, DispositivoGPS, DispositivoBeacon, DispositivoNFC,
    AsignacionGPS, AsignacionBeacon, AsignacionNFC,
    RegistroGPS, RegistroBeacon, RegistroNFC,
    Paciente, HistorialEstado, PacienteEnfermedad, Enfermedad
)
from . import admin_bp

@admin_bp.route('/recursos')
def recursos():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    gps = DispositivoGPS.query.all()
    beacons = DispositivoBeacon.query.all()
    nfcs = DispositivoNFC.query.all()

    lista_dispositivos = []

    for g in gps:
        lista_dispositivos.append({
            'id': g.id, 'nombre': g.nombre, 'tipo': 'gps', 'icono': 'fas fa-map-marker-alt', 
            'fecha_registro': g.fecha_registro_gps.strftime('%d/%m/%Y') if g.fecha_registro_gps else "N/A",
            'fecha_raw': g.fecha_registro_gps.strftime('%Y-%m-%d') if g.fecha_registro_gps else "1970-01-01"
        })
    for b in beacons:
        lista_dispositivos.append({
            'id': b.id, 'nombre': b.nombre, 'tipo': 'beacon', 'icono': 'fab fa-bluetooth-b', 
            'fecha_registro': b.fecha_registro_beacon.strftime('%d/%m/%Y') if b.fecha_registro_beacon else "N/A",
            'fecha_raw': b.fecha_registro_beacon.strftime('%Y-%m-%d') if b.fecha_registro_beacon else "1970-01-01"
        })
    for n in nfcs:
        lista_dispositivos.append({
            'id': n.id, 'nombre': n.nombre, 'tipo': 'nfc', 'icono': 'fas fa-wifi', 
            'fecha_registro': n.fecha_registro_nfc.strftime('%d/%m/%Y') if n.fecha_registro_nfc else "N/A",
            'fecha_raw': n.fecha_registro_nfc.strftime('%Y-%m-%d') if n.fecha_registro_nfc else "1970-01-01"
        })

    return render_template('admin/admin_recursos.html', admin_nombre=admin.nombre if admin else "Admin", dispositivos=lista_dispositivos)

@admin_bp.route('/recursos/alta', methods=['POST'])
def alta_recurso():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    tipo = request.form.get('tipo_dispositivo')
    nombre = request.form.get('nombre')
    try:
        if tipo == 'gps':
            nuevo = DispositivoGPS(nombre=nombre, freq_gps=request.form.get('freq_gps'), fecha_registro_gps=date.today())
            db.session.add(nuevo)
        elif tipo == 'beacon':
            nuevo = DispositivoBeacon(nombre=nombre, tx_power=request.form.get('tx_power'), intervalo_adv=request.form.get('intervalo_adv'), fecha_registro_beacon=date.today())
            db.session.add(nuevo)
        elif tipo == 'nfc':
            nuevo = DispositivoNFC(nombre=nombre, codigo_nfc=request.form.get('codigo_nfc'), fecha_registro_nfc=date.today())
            db.session.add(nuevo)
        db.session.commit()
        flash('Dispositivo registrado correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar: {str(e)}', 'error')
    return redirect(url_for('admin.recursos'))

@admin_bp.route('/recurso/<tipo>/<int:id>')
def perfil_recurso(tipo, id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    disp_nombre = ""
    fecha_reg = None
    fecha_baja = None
    configs = {}
    asig_db = []
    regs_db = []
    registros_logs = []
    total_logs = 0

    if tipo == 'beacon':
        d = DispositivoBeacon.query.get_or_404(id)
        disp_nombre, fecha_reg, fecha_baja = d.nombre, d.fecha_registro_beacon, d.fecha_baja_beacon
        configs = {'TX POWER': f"{d.tx_power}", 'INTERVALO DE LLAMADAS': f"{d.intervalo_adv}"}
        asig_db = AsignacionBeacon.query.filter_by(id_beacon=id).order_by(AsignacionBeacon.fecha_asignacion.desc()).all()
        regs_db = RegistroBeacon.query.filter_by(id_beacon=id).order_by(RegistroBeacon.fecha_beacon_log.desc()).all()
        total_logs = len(regs_db)
        for r in regs_db:
            registros_logs.append({
                'fecha': r.fecha_beacon_log.strftime('%d/%m/%Y %H:%M'),
                'fecha_raw': r.fecha_beacon_log.strftime('%Y-%m-%dT%H:%M:%S'),
                'col1': f"{r.distancia_calculada_beacon} m" if r.distancia_calculada_beacon else "N/A",
                'col2': "12" # Dato estático para visualizar el diseño del wireframe
            })

    elif tipo == 'gps':
        d = DispositivoGPS.query.get_or_404(id)
        disp_nombre, fecha_reg, fecha_baja = d.nombre, d.fecha_registro_gps, d.fecha_baja_gps
        configs = {'FRECUENCIA ACTUALIZACIÓN': f"{d.freq_gps}"}
        asig_db = AsignacionGPS.query.filter_by(id_gps=id).order_by(AsignacionGPS.fecha_asignacion.desc()).all()
        regs_db = RegistroGPS.query.filter_by(id_gps=id).order_by(RegistroGPS.fecha_gps_log.desc()).all()
        total_logs = len(regs_db)
        for r in regs_db:
            registros_logs.append({
                'fecha': r.fecha_gps_log.strftime('%d/%m/%Y %H:%M'),
                'fecha_raw': r.fecha_gps_log.strftime('%Y-%m-%dT%H:%M:%S'),
                'col1': f"Lat: {r.latitud}, Lon: {r.longitud}",
                'col2': f"Dist: {r.distancia_calculada_gps}m" if r.distancia_calculada_gps else "N/A"
            })

    elif tipo == 'nfc':
        d = DispositivoNFC.query.get_or_404(id)
        disp_nombre, fecha_reg, fecha_baja = d.nombre, d.fecha_registro_nfc, d.fecha_baja_nfc
        configs = {'CÓDIGO NFC / UID': d.codigo_nfc}
        asig_db = AsignacionNFC.query.filter_by(id_nfc=id).order_by(AsignacionNFC.fecha_asignacion.desc()).all()
        regs_db = RegistroNFC.query.filter_by(id_nfc=id).order_by(RegistroNFC.fecha_nfc_log.desc()).all()
        total_logs = len(regs_db)
        for r in regs_db:
            registros_logs.append({
                'fecha': r.fecha_nfc_log.strftime('%d/%m/%Y %H:%M'),
                'fecha_raw': r.fecha_nfc_log.strftime('%Y-%m-%dT%H:%M:%S'),
                'col1': r.motivo_escaneo or "Lectura NFC",
                'col2': f"Doctor ID: {r.id_doctor}"
            })

    lista_asignaciones = []
    paciente_actual = "N/A"
    
    for a in asig_db:
        p = Paciente.query.get(a.id_paciente)
        if not p: continue
        if not a.fecha_retiro: paciente_actual = f"{p.nombre} {p.apellido}"
        est = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
        lista_asignaciones.append({
            'nombre': f"{p.nombre} {p.apellido}",
            'estado': est.estado.lower() if est else 'verde',
            'fecha_vinc': a.fecha_asignacion.strftime('%d/%m/%Y'),
            'activa': True if not a.fecha_retiro else False
        })

    datos_disp = {
        'id': id, 'nombre': disp_nombre, 'tipo': tipo,
        'fecha_reg': fecha_reg.strftime('%d/%m/%Y') if fecha_reg else 'N/A',
        'fecha_baja': fecha_baja.strftime('%d/%m/%Y') if fecha_baja else 'N/A',
        'configs': configs, 'paciente_actual': paciente_actual,
        'total_asignaciones': len(asig_db), 'total_logs': total_logs
    }

    return render_template('admin/perfil_recurso.html', disp=datos_disp, asignaciones=lista_asignaciones, logs=registros_logs)

@admin_bp.route('/recurso/<tipo>/<int:id>/editar', methods=['POST'])
def editar_recurso(tipo, id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    nuevo_nombre = request.form.get('nombre')
    try:
        if tipo == 'gps':
            d = DispositivoGPS.query.get_or_404(id)
            d.nombre = nuevo_nombre
            d.freq_gps = request.form.get('freq_gps')
        elif tipo == 'beacon':
            d = DispositivoBeacon.query.get_or_404(id)
            d.nombre = nuevo_nombre
            d.tx_power = request.form.get('tx_power')
            d.intervalo_adv = request.form.get('intervalo_adv')
        elif tipo == 'nfc':
            d = DispositivoNFC.query.get_or_404(id)
            d.nombre = nuevo_nombre
            d.codigo_nfc = request.form.get('codigo_nfc')
        db.session.commit()
        flash(f'Dispositivo {tipo.upper()} actualizado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar: {str(e)}', 'error')
    return redirect(url_for('admin.perfil_recurso', tipo=tipo, id=id))

@admin_bp.route('/recurso/<tipo>/<int:id>/eliminar', methods=['POST'])
def eliminar_recurso(tipo, id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    try:
        if tipo == 'gps':
            d = DispositivoGPS.query.get_or_404(id)
            RegistroGPS.query.filter_by(id_gps=id).delete()
            AsignacionGPS.query.filter_by(id_gps=id).delete()
            db.session.delete(d)
        elif tipo == 'beacon':
            d = DispositivoBeacon.query.get_or_404(id)
            RegistroBeacon.query.filter_by(id_beacon=id).delete()
            AsignacionBeacon.query.filter_by(id_beacon=id).delete()
            db.session.delete(d)
        elif tipo == 'nfc':
            d = DispositivoNFC.query.get_or_404(id)
            RegistroNFC.query.filter_by(id_nfc=id).delete()
            AsignacionNFC.query.filter_by(id_nfc=id).delete()
            db.session.delete(d)
        db.session.commit()
        flash('Dispositivo eliminado permanentemente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'error')
    return redirect(url_for('admin.recursos'))

@admin_bp.route('/recurso/<tipo>/<int:id>/baja', methods=['POST'])
def baja_recurso(tipo, id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    try:
        hoy = date.today()
        ahora = datetime.now()
        if tipo == 'gps':
            d = DispositivoGPS.query.get_or_404(id)
            d.estado_gps = 'Inactivo'
            d.fecha_baja_gps = hoy
            for asig in AsignacionGPS.query.filter_by(id_gps=id, fecha_retiro=None).all(): asig.fecha_retiro = ahora
        elif tipo == 'beacon':
            d = DispositivoBeacon.query.get_or_404(id)
            d.estado_beacon = 'Inactivo'
            d.fecha_baja_beacon = hoy
            for asig in AsignacionBeacon.query.filter_by(id_beacon=id, fecha_retiro=None).all(): asig.fecha_retiro = ahora
        elif tipo == 'nfc':
            d = DispositivoNFC.query.get_or_404(id)
            d.estado_nfc = 'Inactivo'
            d.fecha_baja_nfc = hoy
            for asig in AsignacionNFC.query.filter_by(id_nfc=id, fecha_retiro=None).all(): asig.fecha_retiro = hoy
        db.session.commit()
        flash('Dispositivo dado de baja.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al dar de baja: {str(e)}', 'error')
    return redirect(url_for('admin.perfil_recurso', tipo=tipo, id=id))

@admin_bp.route('/recurso/<tipo>/<int:id>/pacientes')
def pacientes_recurso(tipo, id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    disp_nombre = ""
    asignaciones_db = []
    if tipo == 'gps':
        d = DispositivoGPS.query.get_or_404(id)
        disp_nombre = d.nombre
        asignaciones_db = AsignacionGPS.query.filter_by(id_gps=id).order_by(AsignacionGPS.fecha_asignacion.desc()).all()
    elif tipo == 'beacon':
        d = DispositivoBeacon.query.get_or_404(id)
        disp_nombre = d.nombre
        asignaciones_db = AsignacionBeacon.query.filter_by(id_beacon=id).order_by(AsignacionBeacon.fecha_asignacion.desc()).all()
    elif tipo == 'nfc':
        d = DispositivoNFC.query.get_or_404(id)
        disp_nombre = d.nombre
        asignaciones_db = AsignacionNFC.query.filter_by(id_nfc=id).order_by(AsignacionNFC.fecha_asignacion.desc()).all()

    lista_pacientes = []
    pacientes_agregados = set()
    for a in asignaciones_db:
        if a.id_paciente not in pacientes_agregados:
            p = Paciente.query.get(a.id_paciente)
            if p:
                est = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
                lista_pacientes.append({
                    'id': p.id,
                    'nombre': f"{p.nombre} {p.apellido}",
                    'fecha_ingreso': p.fecha_ingreso.strftime('%d/%m/%Y'),
                    'estado': est.estado.lower() if est else 'verde',
                    'fecha_raw': p.fecha_ingreso.strftime('%Y-%m-%d') if p.fecha_ingreso else "1970-01-01",
                    'asignacion_activa': True if not a.fecha_retiro else False
                })
                pacientes_agregados.add(p.id)

    datos_disp = {'id': id, 'tipo': tipo, 'nombre': disp_nombre}
    return render_template('admin/pacientes_recurso.html', disp=datos_disp, pacientes=lista_pacientes)