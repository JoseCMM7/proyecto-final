from datetime import date, datetime
from flask import render_template, session, redirect, url_for, request, flash, jsonify
from models import (
    db, Usuario, Paciente, Administrador, HistorialEstado, 
    DispositivoGPS, DispositivoBeacon, DispositivoNFC, 
    Doctor, Enfermedad, SubtipoEnfermedad, Familiar, PacienteFamiliar,
    AsignacionGPS, AsignacionBeacon, AsignacionNFC, PacienteEnfermedad, 
    ControlMedico, PacienteTratamiento, Tratamiento, RegistroIndicador
)
from . import admin_bp

@admin_bp.route('/api/subtipos/<int:enfermedad_id>')
def get_subtipos(enfermedad_id):
    subtipos = SubtipoEnfermedad.query.filter_by(id_enfermedad=enfermedad_id).all()
    return jsonify([{'id': s.id, 'descripcion': s.descripcion} for s in subtipos])

@admin_bp.route('/pacientes')
def pacientes():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    pacientes_db = Paciente.query.all()
    lista = []
    for p in pacientes_db:
        est = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
        lista.append({
            'id': p.id,
            'nombre': f"{p.nombre} {p.apellido}",
            'fecha_ingreso': p.fecha_ingreso.strftime('%d/%m/%Y'),
            'estado': est.estado.lower() if est else 'verde',
            'fecha_raw': p.fecha_ingreso.strftime('%Y-%m-%d') if p.fecha_ingreso else "1970-01-01"
        })

    doctores_disponibles = Doctor.query.all()
    enfermedades_disponibles = Enfermedad.query.all()
    
    gps_asignados = [a.id_gps for a in AsignacionGPS.query.filter(AsignacionGPS.fecha_retiro.is_(None)).all()]
    gps_libres = DispositivoGPS.query.filter(~DispositivoGPS.id.in_(gps_asignados)).all() if gps_asignados else DispositivoGPS.query.all()

    beacons_asignados = [a.id_beacon for a in AsignacionBeacon.query.filter(AsignacionBeacon.fecha_retiro.is_(None)).all()]
    beacons_libres = DispositivoBeacon.query.filter(~DispositivoBeacon.id.in_(beacons_asignados)).all() if beacons_asignados else DispositivoBeacon.query.all()

    nfcs_asignados = [a.id_nfc for a in AsignacionNFC.query.filter(AsignacionNFC.fecha_retiro.is_(None)).all()]
    nfcs_libres = DispositivoNFC.query.filter(~DispositivoNFC.id.in_(nfcs_asignados)).all() if nfcs_asignados else DispositivoNFC.query.all()

    return render_template('admin/admin_pacientes.html', 
                           admin_nombre=admin.nombre if admin else "Admin", 
                           pacientes=lista, doctores=doctores_disponibles, enfermedades=enfermedades_disponibles,
                           gps_libres=gps_libres, beacons_libres=beacons_libres, nfcs_libres=nfcs_libres)

@admin_bp.route('/pacientes/alta', methods=['POST'])
def alta_paciente():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()

    try:
        nuevo_usuario = Usuario(username=request.form.get('username'), password=request.form.get('password'), rol='paciente', fecha_alta=date.today())
        db.session.add(nuevo_usuario)
        db.session.flush()

        email_val = request.form.get('email', '').strip()
        paciente_email = email_val if email_val else None

        nuevo_paciente = Paciente(
            nombre=request.form.get('nombre'), apellido=request.form.get('apellido'), fecha_nacimiento=request.form.get('fecha_nacimiento'),
            telefono=request.form.get('telefono'), email=paciente_email, fecha_ingreso=date.today(),
            actividad_minima=request.form.get('actividad_minima', 0), id_admin=admin.id, id_usuario=nuevo_usuario.id
        )
        db.session.add(nuevo_paciente)
        db.session.flush()

        id_enf = request.form.get('id_enfermedad')
        id_sub = request.form.get('id_subtipo')
        fecha_diag = request.form.get('fecha_diagnostico')
        if id_enf and fecha_diag:
            db.session.add(PacienteEnfermedad(id_paciente=nuevo_paciente.id, id_enfermedad=id_enf, id_subtipo=id_sub if id_sub else None, fecha_diagnostico=fecha_diag))

        for doc_id in request.form.getlist('doctores_asignados'):
            doctor = Doctor.query.get(doc_id)
            if doctor: nuevo_paciente.doctores.append(doctor)

        ahora = datetime.now()
        hoy = date.today()

        if request.form.get('id_gps'): db.session.add(AsignacionGPS(fecha_asignacion=ahora, id_paciente=nuevo_paciente.id, id_gps=request.form.get('id_gps')))
        if request.form.get('id_beacon'): db.session.add(AsignacionBeacon(fecha_asignacion=ahora, id_paciente=nuevo_paciente.id, id_beacon=request.form.get('id_beacon')))
        if request.form.get('id_nfc'): db.session.add(AsignacionNFC(fecha_asignacion=hoy, id_paciente=nuevo_paciente.id, id_nfc=request.form.get('id_nfc')))

        if request.form.get('nombre_fam'):
            email_fam_val = request.form.get('email_fam', '').strip()
            fam_email = email_fam_val if email_fam_val else None
            
            nuevo_familiar = Familiar(nombre=request.form.get('nombre_fam'), apellido=request.form.get('apellido_fam'), email=fam_email, numero=request.form.get('telefono_fam'))
            db.session.add(nuevo_familiar)
            db.session.flush()
            db.session.add(PacienteFamiliar(id_paciente=nuevo_paciente.id, id_familiar=nuevo_familiar.id, relacion=request.form.get('relacion_fam'), fecha_creacion_cuenta=date.today()))

        db.session.add(HistorialEstado(estado='VERDE', fecha_inicio=date.today(), id_paciente=nuevo_paciente.id))
        db.session.commit()
        flash('Paciente dado de alta exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {str(e)}', 'error')

    return redirect(url_for('admin.pacientes'))

@admin_bp.route('/paciente/<int:id>')
def perfil_paciente(id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    
    paciente = Paciente.query.get_or_404(id)
    estado_obj = HistorialEstado.query.filter_by(id_paciente=id, fecha_fin=None).first()
    estado_actual = estado_obj.estado if estado_obj else 'INDEFINIDO'
    
    paciente_enf = PacienteEnfermedad.query.filter_by(id_paciente=id).first()
    enfermedad_nombre, subtipo_desc = "No registrada", "N/A"
    if paciente_enf:
        enf = Enfermedad.query.get(paciente_enf.id_enfermedad)
        sub = SubtipoEnfermedad.query.get(paciente_enf.id_subtipo) if paciente_enf.id_subtipo else None
        enfermedad_nombre = enf.nombre if enf else "No registrada"
        subtipo_desc = sub.descripcion if sub else "N/A"

    doctores = paciente.doctores
    
    # Doctores disponibles para asignar (que NO tiene ya asignados)
    doctores_asignados_ids = [d.id for d in doctores]
    if doctores_asignados_ids:
        doctores_para_asignar = Doctor.query.filter(~Doctor.id.in_(doctores_asignados_ids)).all()
    else:
        doctores_para_asignar = Doctor.query.all()
        
    relaciones_fam = PacienteFamiliar.query.filter_by(id_paciente=id).order_by(PacienteFamiliar.id_familiar.asc()).all()
    familiares = []
    familiar_actual = None
    relacion_actual = ""
    for rel in relaciones_fam:
        fam = Familiar.query.get(rel.id_familiar)
        if fam:
            familiares.append({'datos': fam, 'relacion': rel.relacion})
            if familiar_actual is None:
                familiar_actual = fam
                relacion_actual = rel.relacion

    beacons_asignados = AsignacionBeacon.query.filter_by(id_paciente=id, fecha_retiro=None).all()
    gps_asignados = AsignacionGPS.query.filter_by(id_paciente=id, fecha_retiro=None).all()
    nfc_asignados = AsignacionNFC.query.filter_by(id_paciente=id, fecha_retiro=None).all()
    
    lista_beacons = [DispositivoBeacon.query.get(b.id_beacon) for b in beacons_asignados]
    lista_gps = [DispositivoGPS.query.get(g.id_gps) for g in gps_asignados]
    lista_nfc = [DispositivoNFC.query.get(n.id_nfc) for n in nfc_asignados]
    
    current_beacon = beacons_asignados[0].id_beacon if beacons_asignados else None
    current_gps = gps_asignados[0].id_gps if gps_asignados else None
    current_nfc = nfc_asignados[0].id_nfc if nfc_asignados else None

    controles_db = ControlMedico.query.filter_by(id_paciente=id).order_by(ControlMedico.fecha_control.desc()).all()
    lista_controles = [{'fecha': c.fecha_control.strftime('%d %b %Y'), 'doctor': f"Dr. {Doctor.query.get(c.id_doctor).nombre} {Doctor.query.get(c.id_doctor).apellido}" if Doctor.query.get(c.id_doctor) else "Desconocido", 'notas': c.notas} for c in controles_db]

    tratamientos_db = PacienteTratamiento.query.filter_by(id_paciente=id).all()
    lista_tratamientos = []
    for t in tratamientos_db:
        trat_info, doc_info = Tratamiento.query.get(t.id_tratamiento), Doctor.query.get(t.id_doctor)
        lista_tratamientos.append({
            'dosis_valor': t.dosis_valor, 'dosis_unidad': t.dosis_unidad, 'frecuencia_valor': t.frecuencia_valor, 'frecuencia_unidad': t.frecuencia_unidad,
            'fecha_inicio': t.fecha_inicio, 'fecha_fin': t.fecha_fin, 'nombre': trat_info.nombre if trat_info else 'Desconocido', 'tipo': trat_info.tipo if trat_info else 'Medicamento',
            'descripcion': trat_info.descripcion if trat_info else 'Sin descripcion', 'doctor_nombre': f"Dr. {doc_info.nombre} {doc_info.apellido}" if doc_info else 'No registrado'
        })

    doctores_disponibles = Doctor.query.all()
    enfermedades_disponibles = Enfermedad.query.all()
    subtipos_actuales = SubtipoEnfermedad.query.all()
    usuario_paciente = Usuario.query.get(paciente.id_usuario)
    
    gps_ocupados = [a.id_gps for a in AsignacionGPS.query.filter(AsignacionGPS.fecha_retiro.is_(None)).all() if a.id_gps != current_gps]
    gps_lista = DispositivoGPS.query.filter(~DispositivoGPS.id.in_(gps_ocupados)).all() if gps_ocupados else DispositivoGPS.query.all()
    
    bea_ocupados = [a.id_beacon for a in AsignacionBeacon.query.filter(AsignacionBeacon.fecha_retiro.is_(None)).all() if a.id_beacon != current_beacon]
    bea_lista = DispositivoBeacon.query.filter(~DispositivoBeacon.id.in_(bea_ocupados)).all() if bea_ocupados else DispositivoBeacon.query.all()

    nfc_ocupados = [a.id_nfc for a in AsignacionNFC.query.filter(AsignacionNFC.fecha_retiro.is_(None)).all() if a.id_nfc != current_nfc]
    nfc_lista = DispositivoNFC.query.filter(~DispositivoNFC.id.in_(nfc_ocupados)).all() if nfc_ocupados else DispositivoNFC.query.all()

    return render_template('admin/perfil_paciente.html', 
                           paciente=paciente, estado=estado_actual, enfermedad=enfermedad_nombre, subtipo=subtipo_desc, 
                           doctores=doctores, familiares=familiares, beacons=lista_beacons, gps=lista_gps, nfc=lista_nfc, 
                           controles=lista_controles, tratamientos=lista_tratamientos, doctores_disponibles=doctores_disponibles, 
                           doctores_para_asignar=doctores_para_asignar, # AQUI PASAMOS LOS DOCTORES LIBRES
                           enfermedades_disponibles=enfermedades_disponibles, subtipos_actuales=subtipos_actuales, 
                           paciente_enf=paciente_enf, familiar_actual=familiar_actual, relacion_actual=relacion_actual, 
                           usuario_paciente=usuario_paciente, gps_lista=gps_lista, bea_lista=bea_lista, nfc_lista=nfc_lista, 
                           current_gps=current_gps, current_beacon=current_beacon, current_nfc=current_nfc)

@admin_bp.route('/paciente/<int:id>/editar', methods=['POST'])
def editar_paciente(id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    
    paciente = Paciente.query.get_or_404(id)
    try:
        paciente.nombre = request.form.get('nombre')
        paciente.apellido = request.form.get('apellido')
        paciente.fecha_nacimiento = request.form.get('fecha_nacimiento')
        paciente.telefono = request.form.get('telefono')
        
        email_val = request.form.get('email', '').strip()
        paciente.email = email_val if email_val else None
        
        val_act = request.form.get('actividad_minima')
        paciente.actividad_minima = int(val_act) if val_act else 0

        usuario = Usuario.query.get(paciente.id_usuario)
        usuario.username = request.form.get('username')
        if request.form.get('password'): 
            usuario.password = request.form.get('password')

        paciente.doctores = [] 
        for doc_id in request.form.getlist('doctores_asignados'):
            doctor = Doctor.query.get(doc_id)
            if doctor: paciente.doctores.append(doctor)

        pac_enf = PacienteEnfermedad.query.filter_by(id_paciente=id).first()
        nuevo_id_enf = request.form.get('id_enfermedad')
        nuevo_id_sub = request.form.get('id_subtipo') or None

        if pac_enf:
            if str(pac_enf.id_enfermedad) != str(nuevo_id_enf):
                fecha_diag = pac_enf.fecha_diagnostico
                db.session.delete(pac_enf)
                db.session.flush()
                db.session.add(PacienteEnfermedad(id_paciente=id, id_enfermedad=nuevo_id_enf, id_subtipo=nuevo_id_sub, fecha_diagnostico=fecha_diag))
            else:
                pac_enf.id_subtipo = nuevo_id_sub
        elif nuevo_id_enf:
            db.session.add(PacienteEnfermedad(id_paciente=id, id_enfermedad=nuevo_id_enf, id_subtipo=nuevo_id_sub, fecha_diagnostico=date.today()))

        rel_fam = PacienteFamiliar.query.filter_by(id_paciente=id).order_by(PacienteFamiliar.id_familiar.asc()).first()
        email_fam_val = request.form.get('email_fam', '').strip()
        fam_email = email_fam_val if email_fam_val else None

        if rel_fam:
            fam = Familiar.query.get(rel_fam.id_familiar)
            if request.form.get('nombre_fam'): 
                fam.nombre = request.form.get('nombre_fam')
                fam.apellido = request.form.get('apellido_fam')
                fam.email = fam_email
                fam.numero = request.form.get('telefono_fam')
                rel_fam.relacion = request.form.get('relacion_fam')
        elif request.form.get('nombre_fam'):
            nuevo_fam = Familiar(nombre=request.form.get('nombre_fam'), apellido=request.form.get('apellido_fam'), email=fam_email, numero=request.form.get('telefono_fam'))
            db.session.add(nuevo_fam)
            db.session.flush()
            db.session.add(PacienteFamiliar(id_paciente=id, id_familiar=nuevo_fam.id, relacion=request.form.get('relacion_fam'), fecha_creacion_cuenta=date.today()))

        nuevo_gps = request.form.get('id_gps')
        asig_gps = AsignacionGPS.query.filter_by(id_paciente=id, fecha_retiro=None).first()
        if asig_gps and str(asig_gps.id_gps) != str(nuevo_gps): asig_gps.fecha_retiro = datetime.now()
        if nuevo_gps and (not asig_gps or str(asig_gps.id_gps) != str(nuevo_gps)): db.session.add(AsignacionGPS(fecha_asignacion=datetime.now(), id_paciente=id, id_gps=nuevo_gps))

        nuevo_beacon = request.form.get('id_beacon')
        asig_beacon = AsignacionBeacon.query.filter_by(id_paciente=id, fecha_retiro=None).first()
        if asig_beacon and str(asig_beacon.id_beacon) != str(nuevo_beacon): asig_beacon.fecha_retiro = datetime.now()
        if nuevo_beacon and (not asig_beacon or str(asig_beacon.id_beacon) != str(nuevo_beacon)): db.session.add(AsignacionBeacon(fecha_asignacion=datetime.now(), id_paciente=id, id_beacon=nuevo_beacon))

        nuevo_nfc = request.form.get('id_nfc')
        asig_nfc = AsignacionNFC.query.filter_by(id_paciente=id, fecha_retiro=None).first()
        if asig_nfc and str(asig_nfc.id_nfc) != str(nuevo_nfc): asig_nfc.fecha_retiro = date.today()
        if nuevo_nfc and (not asig_nfc or str(asig_nfc.id_nfc) != str(nuevo_nfc)): db.session.add(AsignacionNFC(fecha_asignacion=date.today(), id_paciente=id, id_nfc=nuevo_nfc))

        db.session.commit()
        flash('Datos del paciente actualizados exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar: {str(e)}', 'error')

    return redirect(url_for('admin.perfil_paciente', id=id))

@admin_bp.route('/paciente/<int:id>/eliminar', methods=['POST'])
def eliminar_paciente(id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    paciente = Paciente.query.get_or_404(id)
    try:
        HistorialEstado.query.filter_by(id_paciente=id).delete()
        PacienteEnfermedad.query.filter_by(id_paciente=id).delete()
        PacienteFamiliar.query.filter_by(id_paciente=id).delete()
        PacienteTratamiento.query.filter_by(id_paciente=id).delete()
        AsignacionGPS.query.filter_by(id_paciente=id).delete()
        AsignacionBeacon.query.filter_by(id_paciente=id).delete()
        AsignacionNFC.query.filter_by(id_paciente=id).delete()
        controles = ControlMedico.query.filter_by(id_paciente=id).all()
        for c in controles:
            RegistroIndicador.query.filter_by(id_control=c.id).delete()
            db.session.delete(c)
        paciente.doctores = []
        id_usuario = paciente.id_usuario
        db.session.delete(paciente)
        usuario = Usuario.query.get(id_usuario)
        if usuario: db.session.delete(usuario)
        db.session.commit()
        flash('El paciente y todo su historial han sido eliminados permanentemente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el paciente: {str(e)}', 'error')
    return redirect(url_for('admin.pacientes'))

# --- NUEVAS RUTAS DE DOCTORES ---
@admin_bp.route('/paciente/<int:id>/asignar_doctor', methods=['POST'])
def asignar_doctor(id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    paciente = Paciente.query.get_or_404(id)
    doc_id = request.form.get('id_doctor')
    
    try:
        if doc_id:
            doctor = Doctor.query.get(doc_id)
            if doctor and doctor not in paciente.doctores:
                paciente.doctores.append(doctor)
                db.session.commit()
                flash(f'El Dr. {doctor.nombre} {doctor.apellido} fue asignado exitosamente.', 'success')
            else:
                flash('El doctor ya esta asignado o no existe.', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al asignar doctor: {str(e)}', 'error')
        
    return redirect(url_for('admin.perfil_paciente', id=id))

@admin_bp.route('/paciente/<int:id_paciente>/quitar_doctor/<int:id_doctor>', methods=['POST'])
def quitar_doctor(id_paciente, id_doctor):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    paciente = Paciente.query.get_or_404(id_paciente)
    doctor = Doctor.query.get_or_404(id_doctor)
    
    try:
        if doctor in paciente.doctores:
            paciente.doctores.remove(doctor)
            db.session.commit()
            flash(f'El Dr. {doctor.nombre} {doctor.apellido} ha sido removido del expediente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al quitar doctor: {str(e)}', 'error')
        
    return redirect(url_for('admin.perfil_paciente', id=id_paciente))