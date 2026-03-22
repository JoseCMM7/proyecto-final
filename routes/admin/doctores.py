from datetime import date, datetime
from flask import render_template, session, redirect, url_for, request, flash
from models import (
    db, Administrador, Doctor, Usuario, Especialidad, 
    Paciente, HistorialEstado, PacienteEnfermedad, 
    Enfermedad, ControlMedico
)
from . import admin_bp

@admin_bp.route('/doctores')
def doctores():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    doctores_db = Doctor.query.all()
    lista_doctores = []

    for d in doctores_db:
        # Determinamos si está activo o inactivo basado en si tiene fecha de baja
        estado = 'inactivos' if d.fecha_baja_doctor else 'activos'

        lista_doctores.append({
            'id': d.id, # <-- NUEVO: Agregamos el ID
            'nombre': f"Dr. {d.nombre} {d.apellido}",
            'especialidad': d.especialidad_rel.nombre if d.especialidad_rel else "Sin especialidad",
            'fecha_ingreso': d.fecha_contratacion.strftime('%d/%m/%Y') if d.fecha_contratacion else "Sin registro",
            'fecha_raw': d.fecha_contratacion.strftime('%Y-%m-%d') if d.fecha_contratacion else "1970-01-01",
            'estado': estado
        })

    especialidades_disponibles = Especialidad.query.all()

    return render_template('admin/admin_doctores.html', 
                           admin_nombre=admin.nombre if admin else "Admin", 
                           doctores=lista_doctores,
                           especialidades=especialidades_disponibles)

@admin_bp.route('/doctores/alta', methods=['POST'])
def alta_doctor():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()

    try:
        nuevo_usuario = Usuario(
            username=request.form.get('username'),
            password=request.form.get('password'),
            rol='doctor',
            fecha_alta=date.today()
        )
        db.session.add(nuevo_usuario)
        db.session.flush()

        nuevo_doctor = Doctor(
            nombre=request.form.get('nombre'),
            apellido=request.form.get('apellido'),
            id_especialidad=request.form.get('id_especialidad'),
            telefono=request.form.get('telefono'),
            email=request.form.get('email'),
            cedula=request.form.get('cedula'),
            fecha_contratacion=date.today(),
            id_usuario=nuevo_usuario.id,
            id_admin=admin.id
        )
        db.session.add(nuevo_doctor)
        db.session.commit()
        
        flash('Doctor dado de alta exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {str(e)}', 'error')

    return redirect(url_for('admin.doctores'))

@admin_bp.route('/doctor/<int:id>')
def perfil_doctor(id):
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    
    # 1. Datos principales del doctor
    doctor = Doctor.query.get_or_404(id)
    especialidad = doctor.especialidad_rel.nombre if doctor.especialidad_rel else 'General'

    # 2. Pacientes asignados al doctor
    pacientes_asignados = doctor.pacientes.all() 
    lista_pacientes = []
    
    for p in pacientes_asignados:
        # Buscar estado actual
        est = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
        estado_actual = est.estado.lower() if est else 'verde'
        
        # Buscar enfermedad principal
        pac_enf = PacienteEnfermedad.query.filter_by(id_paciente=p.id).first()
        enfermedad_nombre = "No registrada"
        if pac_enf:
            enf = Enfermedad.query.get(pac_enf.id_enfermedad)
            enfermedad_nombre = enf.nombre if enf else "No registrada"

        lista_pacientes.append({
            'nombre': f"{p.nombre} {p.apellido}",
            'estado': estado_actual,
            'enfermedad': enfermedad_nombre,
            'fecha_ingreso': p.fecha_ingreso.strftime('%d/%m/%Y')
        })

    # 3. Controles médicos realizados
    controles = ControlMedico.query.filter_by(id_doctor=id).order_by(ControlMedico.fecha_control.desc()).all()
    
    # Calcula cuántos se hicieron este mes
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)
    controles_mes_count = sum(1 for c in controles if c.fecha_control.date() >= primer_dia_mes)
    
    # Formatear la lista de controles para la vista
    lista_controles = []
    for c in controles[:5]: # Mostramos los 5 más recientes en esta tabla
        paciente_ctrl = Paciente.query.get(c.id_paciente)
        lista_controles.append({
            'fecha': c.fecha_control.strftime('%d/%m/%Y'),
            'paciente_nombre': f"{paciente_ctrl.nombre} {paciente_ctrl.apellido}" if paciente_ctrl else "Desconocido",
            'notas': c.notas or "Sin notas adicionales"
        })

    return render_template('admin/perfil_doctor.html', 
                           doctor=doctor,
                           especialidad=especialidad,
                           pacientes=lista_pacientes,
                           pacientes_activos=len(pacientes_asignados),
                           controles_mes=controles_mes_count,
                           controles=lista_controles)