from app import app, db, Equipo, RegistroOCR
from sqlalchemy import func

with app.app_context():
    print("Corrigiendo Equipos...")
    qs = RegistroOCR.query.all()
    for q in qs:
        sn = q.sn.strip().upper()
        mac = str(q.mac).strip().upper() if q.mac else ""
        if mac and sn:
            eq = Equipo.query.filter(func.upper(Equipo.sn) == sn).first()
            if not eq:
                # buscar por MAC
                eq = Equipo.query.filter(func.upper(Equipo.mac) == mac).first()
                if eq:
                    print(f"Encontrado por MAC! Cambiando SN de {eq.sn} a {sn}")
                    eq.sn = sn
                else:
                    print(f"Agregando nuevo: {sn} -> {mac}")
                    new_eq = Equipo(sn=sn, mac=mac)
                    db.session.add(new_eq)
            else:
                if eq.mac != mac:
                    print(f"Actualizando MAC de {sn} de {eq.mac} a {mac}")
                    eq.mac = mac
    db.session.commit()
    print("Fix completado")
