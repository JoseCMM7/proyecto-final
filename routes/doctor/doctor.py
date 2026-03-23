from flask import Blueprint, render_template, session, redirect, url_for
from models import (
    db, Doctor, HistorialEstado,
    AsignacionGPS, AsignacionBeacon, AsignacionNFC
)

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/home_doctor')
def home():
    if session.get('rol') != 'doctor': return redirect(url_for('auth.login'))
    
    # 1. Identificamos al doctor que inició sesión
    doctor = Doctor.query.filter_by(id_usuario=session['user_id']).first()
    if not doctor:
        return "Error: Perfil de doctor no encontrado.", 404

    # 2. Obtenemos ÚNICAMENTE a los pacientes de este doctor
    pacientes_del_doctor = doctor.pacientes.all()
    
    rojos = []
    amarillos = []
    dispositivos_activos = 0
    
    # 3. Clasificamos a sus pacientes y contamos dispositivos
    for p in pacientes_del_doctor:
        # Verificamos su estado en el semáforo clínico
        est = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
        if est:
            if est.estado == 'ROJO':
                rojos.append(p)
            elif est.estado == 'AMARILLO':
                amarillos.append(p)
                
        # Sumamos los dispositivos que el paciente tiene actualmente en uso
        if AsignacionGPS.query.filter_by(id_paciente=p.id, fecha_retiro=None).first(): dispositivos_activos += 1
        if AsignacionBeacon.query.filter_by(id_paciente=p.id, fecha_retiro=None).first(): dispositivos_activos += 1
        if AsignacionNFC.query.filter_by(id_paciente=p.id, fecha_retiro=None).first(): dispositivos_activos += 1

    return render_template('doctor/home_doctor.html', 
                           doctor=doctor,
                           total_pacientes=len(pacientes_del_doctor),
                           total_dispositivos=dispositivos_activos,
                           pacientes_rojos_count=len(rojos),
                           pacientes_rojos=rojos,
                           pacientes_amarillos=amarillos)