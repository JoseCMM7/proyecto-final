from datetime import date
from flask import render_template, session, redirect, url_for, request, flash
from models import db, Administrador, Doctor, Usuario, Especialidad
from . import admin_bp

@admin_bp.route('/doctores')
def doctores():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    doctores_db = Doctor.query.all()
    lista_doctores = []

    for d in doctores_db:
        lista_doctores.append({
            'nombre': f"Dr. {d.nombre} {d.apellido}",
            # Ahora accedemos al nombre de la especialidad a través de la relación
            'especialidad': d.especialidad_rel.nombre if d.especialidad_rel else "Sin especialidad",
            'fecha_ingreso': d.fecha_contratacion.strftime('%d/%m/%Y') if d.fecha_contratacion else "Sin registro"
        })

    # Consultamos las especialidades para llenar el <select> del formulario
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
            # Recibimos el ID desde el formulario
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