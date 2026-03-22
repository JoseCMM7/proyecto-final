from flask import render_template, session, redirect, url_for
from models import Administrador, Doctor
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
            'fecha_ingreso': d.fecha_contratacion.strftime('%d/%m/%Y') if d.fecha_contratacion else "Sin registro"
        })

    return render_template('admin/admin_doctores.html', 
                           admin_nombre=admin.nombre if admin else "Admin", 
                           doctores=lista_doctores)