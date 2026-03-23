import sys
sys.path.append('.')
from app import app, db, Equipo, RegistroOCR
from sqlalchemy import func

with app.app_context():
    print("Iniciando Sincronización Manual...")
    # Buscar todos los registros OCR exitosos
    registros = RegistroOCR.query.filter(RegistroOCR.estado_escaneo.in_(['success', 'Registrado', 'Encontrado'])).all()
    
    actualizados = 0
    nuevos = 0
    
    for reg in registros:
        sn_val = reg.sn.strip().upper()
        mac_val = reg.mac.strip().upper()
        
        # Buscar el equipo
        equipo = Equipo.query.filter(func.upper(Equipo.sn) == sn_val).first()
        
        if equipo:
            if equipo.mac != mac_val:
                equipo.mac = mac_val
                actualizados += 1
        else:
            # Si no existe, lo creamos (aunque deberían existir por la migración del excel)
            nuevo = Equipo(sn=sn_val, mac=mac_val, nombre=reg.equipo_nombre, 
                           ubicacion=reg.ubicacion_enviada, usuario=reg.usuario_enviado,
                           proyecto_id=reg.proyecto_id)
            db.session.add(nuevo)
            nuevos += 1
            
    db.session.commit()
    print(f"Sincronización terminada: {actualizados} actualizados, {nuevos} nuevos.")
