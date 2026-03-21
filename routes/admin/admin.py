from datetime import date, datetime
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models import (
    db, Usuario, Paciente, Administrador, HistorialEstado, 
    DispositivoGPS, DispositivoBeacon, DispositivoNFC, 
    Doctor, Enfermedad, Familiar, PacienteFamiliar,
    AsignacionGPS, AsignacionBeacon, AsignacionNFC, PacienteEnfermedad
)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/home_admin')
def home():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    total_p = Paciente.query.count()
    gps = DispositivoGPS.query.filter_by(estado_gps='Activo').count()
    beacons = DispositivoBeacon.query.filter_by(estado_beacon='Activo').count()
    nfc = DispositivoNFC.query.filter_by(estado_nfc='Activo').count()
    
    rojos = Paciente.query.join(HistorialEstado).filter(HistorialEstado.estado == 'ROJO', HistorialEstado.fecha_fin == None).all()
    amarillos = Paciente.query.join(HistorialEstado).filter(HistorialEstado.estado == 'AMARILLO', HistorialEstado.fecha_fin == None).all()

    return render_template('admin/home_admin.html', 
                           admin_nombre=admin.nombre if admin else "Admin",
                           total_pacientes="{:,}".format(total_p),
                           total_dispositivos="{:,}".format(gps+beacons+nfc),
                           pacientes_rojos_count=len(rojos),
                           pacientes_rojos=rojos,
                           pacientes_amarillos=amarillos)

@admin_bp.route('/pacientes')
def pacientes():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    pacientes_db = Paciente.query.all()
    lista = []
    for p in pacientes_db:
        est = HistorialEstado.query.filter_by(id_paciente=p.id, fecha_fin=None).first()
        lista.append({
            'nombre': f"{p.nombre} {p.apellido}",
            'fecha_ingreso': p.fecha_ingreso.strftime('%d/%m/%Y'),
            'estado': est.estado.lower() if est else 'verde'
        })

    doctores_disponibles = Doctor.query.all()
    enfermedades_disponibles = Enfermedad.query.all()
    
    # Buscamos dispositivos libres (aquellos que NO tienen una asignación activa)
    gps_asignados = [a.id_gps for a in AsignacionGPS.query.filter(AsignacionGPS.fecha_retiro == None).all()]
    gps_libres = DispositivoGPS.query.filter(DispositivoGPS.id.notin_(gps_asignados)).all() if gps_asignados else DispositivoGPS.query.all()

    beacons_asignados = [a.id_beacon for a in AsignacionBeacon.query.filter(AsignacionBeacon.fecha_retiro == None).all()]
    beacons_libres = DispositivoBeacon.query.filter(DispositivoBeacon.id.notin_(beacons_asignados)).all() if beacons_asignados else DispositivoBeacon.query.all()

    nfcs_asignados = [a.id_nfc for a in AsignacionNFC.query.filter(AsignacionNFC.fecha_retiro == None).all()]
    nfcs_libres = DispositivoNFC.query.filter(DispositivoNFC.id.notin_(nfcs_asignados)).all() if nfcs_asignados else DispositivoNFC.query.all()

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
        # 1. Crear Usuario
        nuevo_usuario = Usuario(
            username=request.form.get('username'),
            password=request.form.get('password'),
            rol='paciente',
            fecha_alta=date.today()
        )
        db.session.add(nuevo_usuario)
        db.session.flush()

        # 2. Crear Paciente (Solo las columnas de su tabla)
        nuevo_paciente = Paciente(
            nombre=request.form.get('nombre'),
            apellido=request.form.get('apellido'),
            fecha_nacimiento=request.form.get('fecha_nacimiento'),
            telefono=request.form.get('telefono'),
            email=request.form.get('email'),
            fecha_ingreso=date.today(),
            actividad_minima=request.form.get('actividad_minima', 0),
            id_admin=admin.id,
            id_usuario=nuevo_usuario.id
        )
        db.session.add(nuevo_paciente)
        db.session.flush()

        # 3. Registrar Enfermedad y Fecha en su tabla intermedia
        id_enf = request.form.get('id_enfermedad')
        fecha_diag = request.form.get('fecha_diagnostico')
        if id_enf and fecha_diag:
            paciente_enf = PacienteEnfermedad(
                id_paciente=nuevo_paciente.id,
                id_enfermedad=id_enf,
                fecha_diagnostico=fecha_diag
                # Nota: El 'grado' no se inserta porque en tu modelo dependes de id_subtipo (SubtipoEnfermedad)
            )
            db.session.add(paciente_enf)

        # 4. Asignar Doctores
        doctores_ids = request.form.getlist('doctores_asignados')
        for doc_id in doctores_ids:
            doctor = Doctor.query.get(doc_id)
            if doctor: nuevo_paciente.doctores.append(doctor)

        # 5. Asignar Dispositivos IOT en sus tablas de asignación
        ahora = datetime.now()
        hoy = date.today()

        id_gps = request.form.get('id_gps')
        if id_gps:
            asig_gps = AsignacionGPS(fecha_asignacion=ahora, id_paciente=nuevo_paciente.id, id_gps=id_gps)
            db.session.add(asig_gps)

        id_beacon = request.form.get('id_beacon')
        if id_beacon:
            asig_beacon = AsignacionBeacon(fecha_asignacion=ahora, id_paciente=nuevo_paciente.id, id_beacon=id_beacon)
            db.session.add(asig_beacon)

        id_nfc = request.form.get('id_nfc')
        if id_nfc:
            asig_nfc = AsignacionNFC(fecha_asignacion=hoy, id_paciente=nuevo_paciente.id, id_nfc=id_nfc)
            db.session.add(asig_nfc)

        # 6. Crear Familiar
        if request.form.get('nombre_fam'):
            nuevo_familiar = Familiar(
                nombre=request.form.get('nombre_fam'),
                apellido=request.form.get('apellido_fam'),
                email=request.form.get('email_fam'),
                numero=request.form.get('telefono_fam')
            )
            db.session.add(nuevo_familiar)
            db.session.flush()

            relacion = PacienteFamiliar(
                id_paciente=nuevo_paciente.id,
                id_familiar=nuevo_familiar.id,
                relacion=request.form.get('relacion_fam'),
                fecha_creacion_cuenta=date.today()
            )
            db.session.add(relacion)

        # 7. Estado Inicial
        estado_inicial = HistorialEstado(estado='VERDE', fecha_inicio=date.today(), id_paciente=nuevo_paciente.id)
        db.session.add(estado_inicial)

        db.session.commit()
        flash('Paciente dado de alta exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al guardar: {str(e)}', 'error')

    return redirect(url_for('admin.pacientes'))

@admin_bp.route('/doctores')
def doctores():
    if session.get('rol') != 'admin':
        return redirect(url_for('auth.login'))

    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    # Consulta a la tabla Doctor
    doctores_db = Doctor.query.all()
    lista_doctores = []

    for d in doctores_db:
        lista_doctores.append({
            'nombre': f"Dr. {d.nombre} {d.apellido}",
            # Validamos que haya fecha para evitar errores en la pantalla
            'fecha_ingreso': d.fecha_contratacion.strftime('%d/%m/%Y') if d.fecha_contratacion else "Sin registro"
        })

    # IMPORTANTE: Flask buscará el archivo con este nombre exacto
    return render_template('admin/admin_doctores.html', 
                           admin_nombre=admin.nombre if admin else "Admin", 
                           doctores=lista_doctores)

@admin_bp.route('/recursos')
def recursos():
    if session.get('rol') != 'admin':
        return redirect(url_for('auth.login'))

    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    # Obtenemos todos los dispositivos de sus respectivas tablas
    gps = DispositivoGPS.query.all()
    beacons = DispositivoBeacon.query.all()
    nfcs = DispositivoNFC.query.all()

    lista_dispositivos = []

    # Procesamos GPS
    for g in gps:
        lista_dispositivos.append({
            'nombre': g.nombre,
            'tipo': 'gps',
            'icono': 'fas fa-map-marker-alt',
            'fecha_registro': g.fecha_registro_gps.strftime('%d/%m/%Y')
        })

    # Procesamos Beacons
    for b in beacons:
        lista_dispositivos.append({
            'nombre': b.nombre,
            'tipo': 'beacon',
            'icono': 'fab fa-bluetooth-b',
            'fecha_registro': b.fecha_registro_beacon.strftime('%d/%m/%Y')
        })

    # Procesamos NFCs
    for n in nfcs:
        lista_dispositivos.append({
            'nombre': n.nombre,
            'tipo': 'nfc',
            'icono': 'fas fa-wifi',
            'fecha_registro': n.fecha_registro_nfc.strftime('%d/%m/%Y')
        })

    return render_template('admin/admin_recursos.html', 
                           admin_nombre=admin.nombre if admin else "Admin", 
                           dispositivos=lista_dispositivos)