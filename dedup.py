import sys
sys.path.append('.')
from app import app, db, Equipo

with app.app_context():
    print("Deduplicando Equipos...")
    equipos = Equipo.query.all()
    
    # Agrupar por SN en mayúsculas
    from collections import defaultdict
    sn_map = defaultdict(list)
    
    for eq in equipos:
        sn_map[eq.sn.strip().upper()].append(eq)
        
    deletes = 0
    for sn_upper, lista in sn_map.items():
        if len(lista) > 1:
            # Preferir el registro que tenga nombre, o que tenga ID menor (más antiguo, probablemente el original del Excel)
            def score(e):
                sc = 0
                if e.nombre and e.nombre != '-': sc -= 100
                if 'h' in e.sn: sc -= 50 # El excel solía traerlos con 'h' minúscula
                sc += e.id
                return sc
                
            lista.sort(key=score)
            
            keep = lista[0]
            for other in lista[1:]:
                # Fusionar datos
                if not keep.mac and other.mac: keep.mac = other.mac
                if not keep.nombre and other.nombre: keep.nombre = other.nombre
                
                db.session.delete(other)
                deletes += 1

    db.session.commit()
    print(f"Borrados {deletes} duplicados.")
    macs_count = Equipo.query.filter(Equipo.mac != None, Equipo.mac != '').count()
    print(f"Total Equipos con MAC ahora: {macs_count}")
