import sys
sys.path.append('.')
from app import app, db, Equipo, RegistroOCR
from sqlalchemy import func

with app.app_context():
    # Paso 1: Obtener la mejor MAC para cada verdadero S/N desde el Log
    # Si la MAC está amarrada a basura, buscamos su par válido o transcribimos su S/N.
    logs = RegistroOCR.query.order_by(RegistroOCR.fecha_hora.asc()).all()
    mac_to_sn = {}
    for r in logs:
        mac = r.mac.strip().upper() if r.mac else ''
        sn = r.sn.strip().upper()
        if not mac: continue
        
        # Corrección visual del OCR de aquellos días oscuros
        if sn.startswith('30104411'): sn = sn.replace('30104411', '301044H', 1)
        elif sn.startswith('201C44H'): sn = sn.replace('201C44H', '301044H', 1)
        
        if sn.startswith('301044H'):
            mac_to_sn[mac] = sn

    # Ahora mac_to_sn tiene el S/N real para cada una de esas 29 MACs únicas.
    print(f"Total únicas validas: {len(mac_to_sn)}")
    
    # Vamos a limpiar cualquier equipo basura recién creado que no sea de la lista excel
    basuras = Equipo.query.filter(~func.upper(Equipo.sn).startswith('301') & ~func.upper(Equipo.sn).startswith('N/A')).all()
    for b in basuras: 
        print("Borrando basura:", b.sn)
        db.session.delete(b)
        
    db.session.commit()

    updates = 0
    # Asignamos las MACs a su correcto Equipo en DB
    for mac, true_sn in mac_to_sn.items():
        # Busca case-insensitive
        e = Equipo.query.filter(func.upper(Equipo.sn) == true_sn).first()
        if e:
            if e.mac != mac:
                e.mac = mac
                updates += 1
        else:
            print("EXTRAÑO: No existe en Equipos el S/N verdadero:", true_sn)
            # si realmente no existe, se crea pero debería existir por el excel.
            nuevo = Equipo(sn=true_sn, mac=mac)
            db.session.add(nuevo)
            updates += 1

    db.session.commit()
    print("Actualizados:", updates)
    total_macs = Equipo.query.filter(Equipo.mac != None, Equipo.mac != '').count()
    print("Total Equipos con MAC en DB ahora:", total_macs)
