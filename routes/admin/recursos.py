from flask import render_template, session, redirect, url_for
from models import Administrador, DispositivoGPS, DispositivoBeacon, DispositivoNFC
from . import admin_bp

@admin_bp.route('/recursos')
def recursos():
    if session.get('rol') != 'admin': return redirect(url_for('auth.login'))
    admin = Administrador.query.filter_by(id_usuario=session['user_id']).first()
    
    gps = DispositivoGPS.query.all()
    beacons = DispositivoBeacon.query.all()
    nfcs = DispositivoNFC.query.all()

    lista_dispositivos = []

    for g in gps: lista_dispositivos.append({'nombre': g.nombre, 'tipo': 'gps', 'icono': 'fas fa-map-marker-alt', 'fecha_registro': g.fecha_registro_gps.strftime('%d/%m/%Y') if g.fecha_registro_gps else "N/A"})
    for b in beacons: lista_dispositivos.append({'nombre': b.nombre, 'tipo': 'beacon', 'icono': 'fab fa-bluetooth-b', 'fecha_registro': b.fecha_registro_beacon.strftime('%d/%m/%Y') if b.fecha_registro_beacon else "N/A"})
    for n in nfcs: lista_dispositivos.append({'nombre': n.nombre, 'tipo': 'nfc', 'icono': 'fas fa-wifi', 'fecha_registro': n.fecha_registro_nfc.strftime('%d/%m/%Y') if n.fecha_registro_nfc else "N/A"})

    return render_template('admin/admin_recursos.html', admin_nombre=admin.nombre if admin else "Admin", dispositivos=lista_dispositivos)