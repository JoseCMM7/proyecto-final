from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

paciente_doctor = db.Table('paciente_doctor',
    db.Column('id_paciente', db.Integer, db.ForeignKey('pacientes.id'), primary_key=True),
    db.Column('id_doctor', db.Integer, db.ForeignKey('doctores.id'), primary_key=True)
)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False)
    fecha_alta = db.Column(db.Date, nullable=False)
    fecha_baja = db.Column(db.Date)

class Administrador(db.Model):
    __tablename__ = 'administradores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, unique=True)

class Doctor(db.Model):
    __tablename__ = 'doctores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    especialidad = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(150), unique=True)
    cedula = db.Column(db.String(20), nullable=False, unique=True)
    fecha_contratacion = db.Column(db.Date, nullable=False)
    fecha_baja_doctor = db.Column(db.Date)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, unique=True)
    id_admin = db.Column(db.Integer, db.ForeignKey('administradores.id'), nullable=False)

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(150), unique=True)
    fecha_ingreso = db.Column(db.Date, nullable=False)
    actividad_minima = db.Column(db.Integer, nullable=False, default=100)
    fecha_baja_paciente = db.Column(db.Date)
    id_admin = db.Column(db.Integer, db.ForeignKey('administradores.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, unique=True)
    doctores = db.relationship('Doctor', secondary=paciente_doctor, backref=db.backref('pacientes', lazy='dynamic'))

class Familiar(db.Model):
    __tablename__ = 'familiares'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True)
    numero = db.Column(db.String(20))
    fecha_baja = db.Column(db.Date)

class Enfermedad(db.Model):
    __tablename__ = 'enfermedades'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)

class SubtipoEnfermedad(db.Model):
    __tablename__ = 'subtipos_enfermedad'
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(100), nullable=False)
    id_enfermedad = db.Column(db.Integer, db.ForeignKey('enfermedades.id'), nullable=False)

class Tratamiento(db.Model):
    __tablename__ = 'tratamientos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False, unique=True)
    tipo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text)

class IndicadorClinico(db.Model):
    __tablename__ = 'indicadores_clinicos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    unidad_medida = db.Column(db.String(20), nullable=False)
    valor_min_normal = db.Column(db.Numeric(8, 2))
    valor_max_normal = db.Column(db.Numeric(8, 2))

class ControlMedico(db.Model):
    __tablename__ = 'controles_medicos'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    estado_clinico = db.Column(db.String(50), nullable=False)
    fecha_control = db.Column(db.DateTime, nullable=False)
    notas = db.Column(db.Text)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    id_doctor = db.Column(db.Integer, db.ForeignKey('doctores.id'), nullable=False)

class HistorialEstado(db.Model):
    __tablename__ = 'historial_estados'
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(20), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)

class DispositivoBeacon(db.Model):
    __tablename__ = 'dispositivos_beacon'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tx_power = db.Column(db.String(10))
    intervalo_adv = db.Column(db.String(10))
    estado_beacon = db.Column(db.String(20), nullable=False, default='Activo')
    fecha_registro_beacon = db.Column(db.Date, nullable=False)
    fecha_baja_beacon = db.Column(db.Date)

class DispositivoGPS(db.Model):
    __tablename__ = 'dispositivos_gps'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    freq_gps = db.Column(db.String(10))
    estado_gps = db.Column(db.String(20), nullable=False, default='Activo')
    fecha_registro_gps = db.Column(db.Date, nullable=False)
    fecha_baja_gps = db.Column(db.Date)

class DispositivoNFC(db.Model):
    __tablename__ = 'dispositivos_nfc'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo_nfc = db.Column(db.String(50), nullable=False, unique=True)
    estado_nfc = db.Column(db.String(20), nullable=False, default='Activo')
    fecha_registro_nfc = db.Column(db.Date, nullable=False)
    fecha_baja_nfc = db.Column(db.Date)

class RegistroIndicador(db.Model):
    __tablename__ = 'registros_indicadores'
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Numeric(8, 2), nullable=False)
    fecha_registro = db.Column(db.Date, nullable=False)
    id_control = db.Column(db.Integer, db.ForeignKey('controles_medicos.id'), nullable=False)
    id_indicador = db.Column(db.Integer, db.ForeignKey('indicadores_clinicos.id'), nullable=False)

class RegistroBeacon(db.Model):
    __tablename__ = 'registros_beacon'
    id = db.Column(db.Integer, primary_key=True)
    fecha_beacon_log = db.Column(db.DateTime, nullable=False)
    distancia_calculada_beacon = db.Column(db.Numeric(8, 2))
    id_beacon = db.Column(db.Integer, db.ForeignKey('dispositivos_beacon.id'), nullable=False)

class RegistroGPS(db.Model):
    __tablename__ = 'registros_gps'
    id = db.Column(db.Integer, primary_key=True)
    fecha_gps_log = db.Column(db.DateTime, nullable=False)
    latitud = db.Column(db.Numeric(10, 7), nullable=False)
    longitud = db.Column(db.Numeric(10, 7), nullable=False)
    distancia_calculada_gps = db.Column(db.Numeric(10, 2))
    id_gps = db.Column(db.Integer, db.ForeignKey('dispositivos_gps.id'), nullable=False)

class RegistroNFC(db.Model):
    __tablename__ = 'registros_nfc'
    id = db.Column(db.Integer, primary_key=True)
    fecha_nfc_log = db.Column(db.DateTime, nullable=False)
    motivo_escaneo = db.Column(db.String(200))
    id_nfc = db.Column(db.Integer, db.ForeignKey('dispositivos_nfc.id'), nullable=False)
    id_doctor = db.Column(db.Integer, db.ForeignKey('doctores.id'), nullable=False)

class AsignacionBeacon(db.Model):
    __tablename__ = 'asignaciones_beacon'
    id = db.Column(db.Integer, primary_key=True)
    fecha_asignacion = db.Column(db.DateTime, nullable=False)
    fecha_retiro = db.Column(db.DateTime)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    id_beacon = db.Column(db.Integer, db.ForeignKey('dispositivos_beacon.id'), nullable=False)

class AsignacionGPS(db.Model):
    __tablename__ = 'asignaciones_gps'
    id = db.Column(db.Integer, primary_key=True)
    fecha_asignacion = db.Column(db.DateTime, nullable=False)
    fecha_retiro = db.Column(db.DateTime)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    id_gps = db.Column(db.Integer, db.ForeignKey('dispositivos_gps.id'), nullable=False)

class AsignacionNFC(db.Model):
    __tablename__ = 'asignaciones_nfc'
    id = db.Column(db.Integer, primary_key=True)
    fecha_asignacion = db.Column(db.Date, nullable=False)
    fecha_retiro = db.Column(db.Date)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    id_nfc = db.Column(db.Integer, db.ForeignKey('dispositivos_nfc.id'), nullable=False)

class PacienteEnfermedad(db.Model):
    __tablename__ = 'paciente_enfermedad'
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id'), primary_key=True)
    id_enfermedad = db.Column(db.Integer, db.ForeignKey('enfermedades.id'), primary_key=True)
    id_subtipo = db.Column(db.Integer, db.ForeignKey('subtipos_enfermedad.id'))
    fecha_diagnostico = db.Column(db.Date, nullable=False)

class PacienteFamiliar(db.Model):
    __tablename__ = 'paciente_familiar'
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id'), primary_key=True)
    id_familiar = db.Column(db.Integer, db.ForeignKey('familiares.id'), primary_key=True)
    relacion = db.Column(db.String(50), nullable=False)
    fecha_creacion_cuenta = db.Column(db.Date, nullable=False)

class PacienteTratamiento(db.Model):
    __tablename__ = 'paciente_tratamiento'
    id = db.Column(db.Integer, primary_key=True)
    dosis_valor = db.Column(db.Numeric(8, 2))
    dosis_unidad = db.Column(db.String(50))
    frecuencia_valor = db.Column(db.Integer)
    frecuencia_unidad = db.Column(db.String(20))
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date)
    id_paciente = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    id_tratamiento = db.Column(db.Integer, db.ForeignKey('tratamientos.id'), nullable=False)
    id_doctor = db.Column(db.Integer, db.ForeignKey('doctores.id'), nullable=False)