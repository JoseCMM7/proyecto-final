from datetime import date
from flask import render_template, session, redirect, url_for, request, flash
from models import db, Administrador, DispositivoGPS, DispositivoBeacon, DispositivoNFC
from . import admin_bp

@admin_bp.route('/recursos')
def recursos():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    gps = DispositivoGPS.query.all()
    beacons = DispositivoBeacon.query.all()
    nfcs = DispositivoNFC.query.all()

    lista_dispositivos = []

    for g in gps:
        lista_dispositivos.append({
            'id': g.id, 'nombre': g.nombre, 'tipo': 'gps', 'icono': 'fas fa-map-marker-alt', 
            'fecha_registro': g.fecha_registro_gps.strftime('%d/%m/%Y') if g.fecha_registro_gps else "N/A",
            'fecha_raw': g.fecha_registro_gps.strftime('%Y-%m-%d') if g.fecha_registro_gps else "1970-01-01"
        })
    for b in beacons:
        lista_dispositivos.append({
            'id': b.id, 'nombre': b.nombre, 'tipo': 'beacon', 'icono': 'fab fa-bluetooth-b', 
            'fecha_registro': b.fecha_registro_beacon.strftime('%d/%m/%Y') if b.fecha_registro_beacon else "N/A",
            'fecha_raw': b.fecha_registro_beacon.strftime('%Y-%m-%d') if b.fecha_registro_beacon else "1970-01-01"
        })
    for n in nfcs:
        lista_dispositivos.append({
            'id': n.id, 'nombre': n.nombre, 'tipo': 'nfc', 'icono': 'fas fa-wifi', 
            'fecha_registro': n.fecha_registro_nfc.strftime('%d/%m/%Y') if n.fecha_registro_nfc else "N/A",
            'fecha_raw': n.fecha_registro_nfc.strftime('%Y-%m-%d') if n.fecha_registro_nfc else "1970-01-01"
        })

    return render_template('admin/admin_recursos.html', admin_nombre=admin.nombre if admin else "Admin", dispositivos=lista_dispositivos)

@admin_bp.route('/recursos/alta', methods=['POST'])
def alta_recurso():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))

    tipo = request.form.get('tipo_dispositivo')
    nombre = request.form.get('nombre')

    try:
        if tipo == 'gps':
            nuevo_gps = DispositivoGPS(nombre=nombre, freq_gps=request.form.get('freq_gps'), fecha_registro_gps=date.today())
            db.session.add(nuevo_gps)
        elif tipo == 'beacon':
            nuevo_beacon = DispositivoBeacon(nombre=nombre, tx_power=request.form.get('tx_power'), intervalo_adv=request.form.get('intervalo_adv'), fecha_registro_beacon=date.today())
            db.session.add(nuevo_beacon)
        elif tipo == 'nfc':
            nuevo_nfc = DispositivoNFC(nombre=nombre, codigo_nfc=request.form.get('codigo_nfc'), fecha_registro_nfc=date.today())
            db.session.add(nuevo_nfc)

        db.session.commit()
        flash('Dispositivo registrado en el inventario correctamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al registrar el dispositivo: {str(e)}', 'error')

    return redirect(url_for('admin.recursos'))