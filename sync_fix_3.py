import sys
sys.path.append('.')
from app import app, db, Equipo, RegistroOCR

with app.app_context():
    print("Forzando restauración de MACs correctos desde LOG a Inventario Oficial...")
    # Get all logs
    qs = RegistroOCR.query.order_by(RegistroOCR.fecha_hora.asc()).all()
    updates = 0
    
    # We will only assign MACs to Equipos whose SN starts with 301044H
    for r in qs:
        sn = r.sn.strip().upper()
        mac = r.mac.strip().upper() if r.mac else ""
        
        # Ignoramos la basura como 1107... o COMPATIBLE... en el SN del log
        if not sn.startswith('301044H') and mac:
            # Quizás leímos mal el SN pero tenemos la MAC buena.
            # Veamos si hay algún registro en este mismo log con la misma MAC pero con SN bueno.
            good_log = RegistroOCR.query.filter(RegistroOCR.mac == r.mac, RegistroOCR.sn.like('301044H%')).first()
            if good_log:
                sn = good_log.sn.strip().upper()
            else:
                # Si el SN 301044XXXXX se leyó como 30104411XXXXX..
                if sn.startswith('30104411'):
                    sn = sn.replace('30104411', '301044H', 1)
                elif sn.startswith('201C44H'):
                    sn = sn.replace('201C44H', '301044H', 1)
        
        if mac and sn.startswith('301044H'):
            e = Equipo.query.filter_by(sn=sn).first()
            if e:
                if e.mac != mac:
                    e.mac = mac
                    updates += 1
                    print(f"Restaurado MAC {mac} para el Equipo {sn}")
            else:
                # Si de verdad no existe, lo creamos
                print(f"Creando equipo faltante {sn} con MAC {mac}")
                e = Equipo(sn=sn, mac=mac)
                db.session.add(e)
                updates += 1
                
    db.session.commit()
    print(f"Total MACs restauradas: {updates}")
