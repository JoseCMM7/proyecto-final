from datetime import date, datetime
from flask import render_template, session, redirect, url_for, request, flash, jsonify
from models import (
    db, Usuario, Paciente, Administrador, HistorialEstado, 
    DispositivoGPS, DispositivoBeacon, DispositivoNFC, 
    Doctor, Enfermedad, SubtipoEnfermedad, Familiar, PacienteFamiliar,
    AsignacionGPS, AsignacionBeacon, AsignacionNFC, PacienteEnfermedad, ControlMedico, PacienteTratamiento, Tratamiento
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
    
    # Dentro de def pacientes():
    pacientes_db = Paciente.query.all()
    lista = []
    for p in pacientes_db:
        est = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
        lista.append({
            'id': p.id, # <-- NUEVO: Agregamos el ID del paciente aquí
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
                           pacientes=lista,
                           doctores=doctores_disponibles,
                           enfermedades=enfermedades_disponibles,
                           gps_libres=gps_libres,
                           beacons_libres=beacons_libres,
                           nfcs_libres=nfcs_libres)

@admin_bp.route('/pacientes/alta', methods=['POST'])
def alta_paciente():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()

    try:
        nuevo_usuario = Usuario(username=request.form.get('username'), password=request.form.get('password'), rol='paciente', fecha_alta=date.today())
        db.session.add(nuevo_usuario)
        db.session.flush()

        nuevo_paciente = Paciente(
            nombre=request.form.get('nombre'), apellido=request.form.get('apellido'), fecha_nacimiento=request.form.get('fecha_nacimiento'),
            telefono=request.form.get('telefono'), email=request.form.get('email'), fecha_ingreso=date.today(),
            actividad_minima=request.form.get('actividad_minima', 0), id_admin=admin.id, id_usuario=nuevo_usuario.id
        )
        db.session.add(nuevo_paciente)
        db.session.flush()

        id_enf = request.form.get('id_enfermedad')
        id_sub = request.form.get('id_subtipo')
        fecha_diag = request.form.get('fecha_diagnostico')
        if id_enf and fecha_diag:
            db.session.add(PacienteEnfermedad(id_paciente=nuevo_paciente.id, id_enfermedad=id_enf, id_subtipo=id_sub if id_sub else None, fecha_diagnostico=fecha_diag))

        doctores_ids = request.form.getlist('doctores_asignados')
        for doc_id in doctores_ids:
            doctor = Doctor.query.get(doc_id)
            if doctor: nuevo_paciente.doctores.append(doctor)

        ahora = datetime.now()
        hoy = date.today()

        if request.form.get('id_gps'): db.session.add(AsignacionGPS(fecha_asignacion=ahora, id_paciente=nuevo_paciente.id, id_gps=request.form.get('id_gps')))
        if request.form.get('id_beacon'): db.session.add(AsignacionBeacon(fecha_asignacion=ahora, id_paciente=nuevo_paciente.id, id_beacon=request.form.get('id_beacon')))
        if request.form.get('id_nfc'): db.session.add(AsignacionNFC(fecha_asignacion=hoy, id_paciente=nuevo_paciente.id, id_nfc=request.form.get('id_nfc')))

        if request.form.get('nombre_fam'):
            nuevo_familiar = Familiar(nombre=request.form.get('nombre_fam'), apellido=request.form.get('apellido_fam'), email=request.form.get('email_fam'), numero=request.form.get('telefono_fam'))
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
    
    # 1. Datos principales del paciente y su estado
    paciente = Paciente.query.get_or_404(id)
    estado_obj = HistorialEstado.query.filter_by(id_paciente=id, fecha_fin=None).first()
    estado_actual = estado_obj.estado if estado_obj else 'INDEFINIDO'
    
    # 2. Resumen Clinico (Enfermedad y Subtipo)
    paciente_enf = PacienteEnfermedad.query.filter_by(id_paciente=id).first()
    enfermedad_nombre = "No registrada"
    subtipo_desc = "N/A"
    if paciente_enf:
        enf = Enfermedad.query.get(paciente_enf.id_enfermedad)
        sub = SubtipoEnfermedad.query.get(paciente_enf.id_subtipo) if paciente_enf.id_subtipo else None
        enfermedad_nombre = enf.nombre if enf else "No registrada"
        subtipo_desc = sub.descripcion if sub else "N/A"

    # 3. Doctores asignados
    doctores = paciente.doctores

    # 4. Familiares
    relaciones_fam = PacienteFamiliar.query.filter_by(id_paciente=id).all()
    familiares = []
    for rel in relaciones_fam:
        fam = Familiar.query.get(rel.id_familiar)
        if fam:
            familiares.append({'datos': fam, 'relacion': rel.relacion})

    # 5. Dispositivos (Beacons y GPS activos)
    beacons_asignados = AsignacionBeacon.query.filter_by(id_paciente=id, fecha_retiro=None).all()
    gps_asignados = AsignacionGPS.query.filter_by(id_paciente=id, fecha_retiro=None).all()
    
    lista_beacons = [DispositivoBeacon.query.get(b.id_beacon) for b in beacons_asignados]
    lista_gps = [DispositivoGPS.query.get(g.id_gps) for g in gps_asignados]

    # 6. Controles Medicos
    controles = ControlMedico.query.filter_by(id_paciente=id).order_by(ControlMedico.fecha_control.desc()).all()

    # 7. Tratamientos
    tratamientos_db = PacienteTratamiento.query.filter_by(id_paciente=id).all()
    lista_tratamientos = []
    
    for t in tratamientos_db:
        trat_info = Tratamiento.query.get(t.id_tratamiento)
        doc_info = Doctor.query.get(t.id_doctor)
        
        lista_tratamientos.append({
            'dosis_valor': t.dosis_valor,
            'dosis_unidad': t.dosis_unidad,
            'frecuencia_valor': t.frecuencia_valor,
            'frecuencia_unidad': t.frecuencia_unidad,
            'fecha_inicio': t.fecha_inicio,
            'fecha_fin': t.fecha_fin,
            'nombre': trat_info.nombre if trat_info else 'Desconocido',
            'tipo': trat_info.tipo if trat_info else 'Medicamento',
            'descripcion': trat_info.descripcion if trat_info else 'Sin descripcion',
            'doctor_nombre': f"Dr. {doc_info.nombre} {doc_info.apellido}" if doc_info else 'No registrado'
        })

    return render_template('admin/perfil_paciente.html', 
                           paciente=paciente, 
                           estado=estado_actual,
                           enfermedad=enfermedad_nombre,
                           subtipo=subtipo_desc,
                           doctores=doctores,
                           familiares=familiares,
                           beacons=lista_beacons,
                           gps=lista_gps,
                           tratamientos=lista_tratamientos) # <-- Pasamos la nueva lista