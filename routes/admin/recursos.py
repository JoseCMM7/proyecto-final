from flask import render_template, session, redirect, url_for, request, flash
from datetime import date
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
            nuevo_gps = DispositivoGPS(nombre=nombre, freq_gps=request.form.get('freq_gps'), fecha_registro_gps=date.today())
            db.session.add(nuevo_gps)
        elif tipo == 'beacon':
            nuevo_beacon = DispositivoBeacon(nombre=nombre, tx_power=request.form.get('tx_power'), intervalo_adv=request.form.get('intervalo_adv'), fecha_registro_beacon=date.today())
            db.session.add(nuevo_beacon)
        elif tipo == 'nfc':
            nuevo_nfc = DispositivoNFC(nombre=nombre, codigo_nfc=request.form.get('codigo_nfc'), fecha_registro_nfc=date.today())
            db.session.add(nuevo_nfc)

        db.session.commit()
        flash('Dispositivo registrado en el inventario correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar el dispositivo: {str(e)}', 'error')

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

    # 1. Obtener datos según el tipo de dispositivo
    if tipo == 'beacon':
        d = DispositivoBeacon.query.get_or_404(id)
        disp_nombre, fecha_reg, fecha_baja = d.nombre, d.fecha_registro_beacon, d.fecha_baja_beacon
        configs = {'TX POWER': f"{d.tx_power}", 'INTERVALO DE LLAMADAS': f"{d.intervalo_adv}"}
        asig_db = AsignacionBeacon.query.filter_by(id_beacon=id).order_by(AsignacionBeacon.fecha_asignacion.desc()).all()
        regs_db = RegistroBeacon.query.filter_by(id_beacon=id).order_by(RegistroBeacon.fecha_beacon_log.desc()).limit(10).all()
        total_logs = RegistroBeacon.query.filter_by(id_beacon=id).count()
        for r in regs_db:
            registros_logs.append({
                'fecha': r.fecha_beacon_log.strftime('%d/%m/%Y %H:%M'),
                'col1': f"{r.distancia_calculada_beacon} m" if r.distancia_calculada_beacon else "N/A",
                'col2': "Detección de zona"
            })

    elif tipo == 'gps':
        d = DispositivoGPS.query.get_or_404(id)
        disp_nombre, fecha_reg, fecha_baja = d.nombre, d.fecha_registro_gps, d.fecha_baja_gps
        configs = {'FRECUENCIA ACTUALIZACIÓN': f"{d.freq_gps}"}
        asig_db = AsignacionGPS.query.filter_by(id_gps=id).order_by(AsignacionGPS.fecha_asignacion.desc()).all()
        regs_db = RegistroGPS.query.filter_by(id_gps=id).order_by(RegistroGPS.fecha_gps_log.desc()).limit(10).all()
        total_logs = RegistroGPS.query.filter_by(id_gps=id).count()
        for r in regs_db:
            registros_logs.append({
                'fecha': r.fecha_gps_log.strftime('%d/%m/%Y %H:%M'),
                'col1': f"Lat: {r.latitud}, Lon: {r.longitud}",
                'col2': f"Dist: {r.distancia_calculada_gps}m" if r.distancia_calculada_gps else "N/A"
            })

    elif tipo == 'nfc':
        d = DispositivoNFC.query.get_or_404(id)
        disp_nombre, fecha_reg, fecha_baja = d.nombre, d.fecha_registro_nfc, d.fecha_baja_nfc
        configs = {'CÓDIGO NFC / UID': d.codigo_nfc}
        asig_db = AsignacionNFC.query.filter_by(id_nfc=id).order_by(AsignacionNFC.fecha_asignacion.desc()).all()
        regs_db = RegistroNFC.query.filter_by(id_nfc=id).order_by(RegistroNFC.fecha_nfc_log.desc()).limit(10).all()
        total_logs = RegistroNFC.query.filter_by(id_nfc=id).count()
        for r in regs_db:
            registros_logs.append({
                'fecha': r.fecha_nfc_log.strftime('%d/%m/%Y %H:%M'),
                'col1': r.motivo_escaneo or "Lectura NFC",
                'col2': f"Doctor ID: {r.id_doctor}"
            })

    # 2. Procesar asignaciones a pacientes
    lista_asignaciones = []
    paciente_actual = "N/A"
    
    for a in asig_db:
        p = Paciente.query.get(a.id_paciente)
        if not p: continue
        
        # Si no tiene fecha de retiro, es el paciente actual asignado
        if not a.fecha_retiro: paciente_actual = f"{p.nombre} {p.apellido}"

        est = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
        enf_rel = PacienteEnfermedad.query.filter_by(id_paciente=p.id).first()
        enf_nombre = Enfermedad.query.get(enf_rel.id_enfermedad).nombre if enf_rel else "Sin registro"

        lista_asignaciones.append({
            'nombre': f"{p.nombre} {p.apellido}",
            'estado': est.estado.lower() if est else 'verde',
            'enfermedad': enf_nombre,
            'fecha_vinc': a.fecha_asignacion.strftime('%d/%m/%Y'),
            'activa': True if not a.fecha_retiro else False
        })

    datos_disp = {
        'id': id,
        'nombre': disp_nombre, 'tipo': tipo,
        'fecha_reg': fecha_reg.strftime('%d/%m/%Y') if fecha_reg else 'N/A',
        'fecha_baja': fecha_baja.strftime('%d/%m/%Y') if fecha_baja else 'N/A',
        'configs': configs, 'paciente_actual': paciente_actual,
        'total_asignaciones': len(asig_db), 'total_logs': total_logs
    }

    return render_template('admin/perfil_recurso.html', disp=datos_disp, asignaciones=lista_asignaciones, logs=registros_logs)

from flask import request, redirect, url_for, flash, session
# Asegúrate de tener importado 'db' y tus modelos de dispositivos aquí arriba

@admin_bp.route('/recurso/<tipo>/<int:id>/editar', methods=['POST'])
def editar_recurso(tipo, id):
    # Protección de ruta
    if session.get('rol') != 'admin': 
        return redirect(url_for('auth.login'))

    # 1. Recibimos los datos del formulario HTML
    nombre = request.form.get('nombre')

    try:
        # 2. Lógica dependiendo del tipo de dispositivo
        if tipo == 'gps':
            frecuencia = request.form.get('freq_gps')
            # Aquí va tu código SQLAlchemy: 
            # dispositivo = DispositivoGPS.query.get_or_404(id)
            # dispositivo.nombre = nombre
            
        elif tipo == 'beacon':
            tx_power = request.form.get('tx_power')
            intervalo = request.form.get('intervalo_adv')
            # Lógica SQLAlchemy para Beacon
            
        elif tipo == 'nfc':
            codigo = request.form.get('codigo_nfc')
            # Lógica SQLAlchemy para NFC

        # db.session.commit() # Descomenta esto cuando conectes tus modelos
        flash(f'Dispositivo {tipo.upper()} actualizado correctamente.', 'success')
        
    except Exception as e:
        # db.session.rollback()
        flash(f'Error al actualizar: {str(e)}', 'error')

    return redirect(url_for('admin.perfil_recurso', tipo=tipo, id=id))


@admin_bp.route('/recurso/<tipo>/<int:id>/eliminar', methods=['POST'])
def eliminar_recurso(tipo, id):
    if session.get('rol') != 'admin': 
        return redirect(url_for('auth.login'))

    try:
        if tipo == 'gps':
            # 1. Buscamos el dispositivo
            dispositivo = DispositivoGPS.query.get_or_404(id)
            
            # 2. Eliminamos manualmente sus dependencias para evitar errores de Foreign Key
            RegistroGPS.query.filter_by(id_gps=id).delete()
            AsignacionGPS.query.filter_by(id_gps=id).delete()
            
            # 3. Eliminamos el dispositivo
            db.session.delete(dispositivo)
            db.session.commit()
            
            flash('Dispositivo GPS y todo su historial han sido eliminados permanentemente.', 'success')
            
        elif tipo == 'beacon':
            # Lógica lista para cuando quieras implementar la eliminación de Beacons
            pass
            
        elif tipo == 'nfc':
            # Lógica lista para cuando quieras implementar la eliminación de NFC
            pass

    except Exception as e:
        db.session.rollback() # Si algo falla, deshacemos cualquier cambio a medias
        flash(f'Error al eliminar el dispositivo: {str(e)}', 'error')

    # Redirigimos al inventario general
    return redirect(url_for('admin.recursos'))