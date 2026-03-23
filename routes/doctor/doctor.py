from flask import Blueprint, render_template, session, redirect, url_for, request
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

@doctor_bp.route('/mis_pacientes')
def pacientes():
    if session.get('rol') != 'doctor': return redirect(url_for('auth.login'))
    
    doctor = Doctor.query.filter_by(id_usuario=session['user_id']).first()
    if not doctor: return "Error: Perfil no encontrado.", 404

    # 1. Capturar parámetros de búsqueda y filtro desde la URL (Cero JS)
    busqueda = request.args.get('q', '').lower()
    filtro_estado = request.args.get('estado', 'todos')
    orden = request.args.get('orden', 'nombre')

    # 2. Obtener lista dinámica de pacientes del doctor (Cero Hardcode)
    pacientes_brutos = doctor.pacientes.all()
    lista_filtrada = []
    
    # 3. Procesamiento y Filtrado en Backend
    for p in pacientes_brutos:
        est = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
        estado_str = est.estado.lower() if est else 'verde'
        
        # Aplicar búsqueda por nombre/apellido
        nombre_completo = f"{p.nombre} {p.apellido}".lower()
        if busqueda and busqueda not in nombre_completo:
            continue
            
        # Aplicar filtro de estado
        if filtro_estado != 'todos' and estado_str != filtro_estado:
            continue
            
        lista_filtrada.append({
            'id': p.id,
            'nombre': f"{p.nombre} {p.apellido}",
            'fecha_ingreso_str': p.fecha_ingreso.strftime('%d/%m/%Y'),
            'fecha_raw': p.fecha_ingreso,
            'estado': estado_str
        })
        
    # 4. Ordenamiento puramente en Python
    if orden == 'nombre':
        lista_filtrada.sort(key=lambda x: x['nombre'])
    elif orden == 'fecha_reciente':
        lista_filtrada.sort(key=lambda x: x['fecha_raw'], reverse=True)
    elif orden == 'fecha_antigua':
        lista_filtrada.sort(key=lambda x: x['fecha_raw'])

    return render_template('doctor/pacientes.html', 
                           doctor=doctor, 
                           pacientes=lista_filtrada,
                           busqueda=busqueda,
                           filtro_estado=filtro_estado,
                           orden=orden)