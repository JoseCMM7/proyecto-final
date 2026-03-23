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

# Asegúrate de tener estas importaciones al inicio si no las tienes:
from models import (
    db, Doctor, Paciente, HistorialEstado, PacienteEnfermedad, Enfermedad, 
    SubtipoEnfermedad, Familiar, PacienteFamiliar, AsignacionBeacon, 
    AsignacionGPS, AsignacionNFC, DispositivoBeacon, DispositivoGPS, 
    DispositivoNFC, ControlMedico, PacienteTratamiento, Tratamiento
)

@doctor_bp.route('/mi_paciente/<int:id>')
def perfil_paciente(id):
    if session.get('rol') != 'doctor': return redirect(url_for('auth.login'))
    
    doctor = Doctor.query.filter_by(id_usuario=session['user_id']).first()
    paciente = Paciente.query.get_or_404(id)
    
    # 1. Seguridad: Verificar que el paciente pertenece a este doctor
    if doctor not in paciente.doctores:
        return "Acceso denegado: Este paciente no está en tu lista.", 403

    # 2. Resumen Clínico (Estado y Enfermedad)
    estado_obj = HistorialEstado.query.filter_by(id_paciente=id, fecha_fin=None).first()
    estado_actual = estado_obj.estado if estado_obj else 'INDEFINIDO'
    
    paciente_enf = PacienteEnfermedad.query.filter_by(id_paciente=id).first()
    enfermedad_nombre, subtipo_desc = "No registrada", "N/A"
    if paciente_enf:
        enf = Enfermedad.query.get(paciente_enf.id_enfermedad)
        sub = SubtipoEnfermedad.query.get(paciente_enf.id_subtipo) if paciente_enf.id_subtipo else None
        enfermedad_nombre = enf.nombre if enf else "No registrada"
        subtipo_desc = sub.descripcion if sub else "N/A"

    # 3. Contactos de Emergencia (Familiares)
    relaciones_fam = PacienteFamiliar.query.filter_by(id_paciente=id).all()
    familiares = []
    for rel in relaciones_fam:
        fam = Familiar.query.get(rel.id_familiar)
        if fam: familiares.append({'datos': fam, 'relacion': rel.relacion})

    # 4. Dispositivos Activos (Solo lectura)
    beacons = [DispositivoBeacon.query.get(b.id_beacon) for b in AsignacionBeacon.query.filter_by(id_paciente=id, fecha_retiro=None).all()]
    gps = [DispositivoGPS.query.get(g.id_gps) for g in AsignacionGPS.query.filter_by(id_paciente=id, fecha_retiro=None).all()]
    nfc = [DispositivoNFC.query.get(n.id_nfc) for n in AsignacionNFC.query.filter_by(id_paciente=id, fecha_retiro=None).all()]

    # 5. Controles Médicos Históricos
    controles_db = ControlMedico.query.filter_by(id_paciente=id).order_by(ControlMedico.fecha_control.desc()).all()
    lista_controles = [{'fecha': c.fecha_control.strftime('%d %b %Y'), 'doctor': f"Dr. {Doctor.query.get(c.id_doctor).nombre} {Doctor.query.get(c.id_doctor).apellido}" if Doctor.query.get(c.id_doctor) else "Desconocido", 'notas': c.notas} for c in controles_db]

    # 6. Tratamientos Activos
    tratamientos_db = PacienteTratamiento.query.filter_by(id_paciente=id).all()
    lista_tratamientos = []
    for t in tratamientos_db:
        trat_info, doc_info = Tratamiento.query.get(t.id_tratamiento), Doctor.query.get(t.id_doctor)
        lista_tratamientos.append({
            'dosis_valor': t.dosis_valor, 'dosis_unidad': t.dosis_unidad, 'frecuencia_valor': t.frecuencia_valor, 'frecuencia_unidad': t.frecuencia_unidad,
            'fecha_inicio': t.fecha_inicio, 'fecha_fin': t.fecha_fin, 'nombre': trat_info.nombre if trat_info else 'Desconocido', 'tipo': trat_info.tipo if trat_info else 'Medicamento',
            'descripcion': trat_info.descripcion if trat_info else 'Sin descripcion', 'doctor_nombre': f"Dr. {doc_info.nombre} {doc_info.apellido}" if doc_info else 'No registrado'
        })

    return render_template('doctor/perfil_paciente.html', 
                           doctor=doctor, paciente=paciente, estado=estado_actual, 
                           enfermedad=enfermedad_nombre, subtipo=subtipo_desc, 
                           familiares=familiares, beacons=beacons, gps=gps, nfc=nfc, 
                           controles=lista_controles, tratamientos=lista_tratamientos)