import json
import os
from app import app, db, InfraElement, InfraPort
from sqlalchemy import text

def get_abs_path(relative_path):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

COLOR_SERVICE = {
    "AP": "#00ffff", "BIOMETRICO": "#22c55e", "RELOJ": "#22c55e",
    "DATOS": "#f97316", "FORTINET": "#eab308", "TELEFONIA": "#3b82f6",
    "VOZ": "#3b82f6", "VAC": "#f1f5f9"
}

def import_infra_fisica_v3():
    with app.app_context():
        print("🧹 Limpiando base de datos a fondo...")
        db.session.execute(text("TRUNCATE TABLE infra_ports CASCADE"))
        db.session.execute(text("DELETE FROM infra_elements"))
        db.session.commit()

        # 1. Crear Equipos
        sws = {}
        for i in range(1, 6):
            sw = InfraElement(nombre=f"Switch {i}", tipo="SWITCH", total_puertos=48, piso=(1 if i <= 3 else 2))
            db.session.add(sw)
            db.session.flush() # Para tener el ID ya
            sws[f"SW{i}"] = sw

        pps = {}
        for i in range(1, 10):
            pp = InfraElement(nombre=f"Patch Panel {i}", tipo="PATCH_PANEL", total_puertos=24, piso=(1 if i <= 5 else 2))
            db.session.add(pp)
            db.session.flush()
            pps[f"PP{i}"] = pp
        
        fw = InfraElement(nombre="Firewall", tipo="OTRO", total_puertos=8, piso=2)
        voip = InfraElement(nombre="FortiVoice", tipo="OTRO", total_puertos=4, piso=2)
        db.session.add_all([fw, voip])
        db.session.commit()

        with open(get_abs_path('uploads/PUNTOS POR BOX.json'), 'r', encoding='utf-8') as f:
            puntos_json = json.load(f)

        def find_p(id_punto, pasillo, piso):
            buscado = pasillo.strip().upper()
            for p in puntos_json:
                p_id = str(p.get("ID_PUNTO"))
                p_pas = str(p.get("PASILLO", "")).strip().upper()
                p_piso = int(p.get("PISO", 1))
                # BUSQUEDA EXACTA PARA EVITAR CRUCES (Pasillo 1 != Pasillo 10)
                if p_id == str(id_punto) and p_pas == buscado and p_piso == int(piso):
                    return p
            return None

        def Link(sw_name, sw_port, pp_name, pp_port, tag_id, pasillo, piso):
            p_data = find_p(tag_id, pasillo, piso)
            tag_str = f"P{tag_id}" if tag_id else ""
            
            servicio = (p_data['SERVICIO'] or "DATOS").upper() if p_data else "VAC"
            destino = f"Box {p_data['BOX']} - {p_data['PASILLO']}" if p_data else "Libre"
            color = COLOR_SERVICE.get(servicio, "#f97316")

            # 1. Crear puerto en Switch
            psw = InfraPort(element_id=sws[sw_name].id, numero_puerto=sw_port, tipo_servicio=servicio, destino=destino, color_hex=color, tag=tag_str)
            db.session.add(psw)
            db.session.flush()

            # 2. Crear puerto en Patch Panel y conectarlo al Switch
            if pp_name:
                ppp = InfraPort(element_id=pps[pp_name].id, numero_puerto=pp_port, tipo_servicio=servicio, destino=destino, color_hex=color, tag=tag_str, conectado_a_id=psw.id)
                db.session.add(ppp)
                db.session.flush()
                # Link bidireccional
                psw.conectado_a_id = ppp.id
            
            if tag_str:
                print(f"🔗 Conectado: {pp_name}:{pp_port} ({tag_str} {pasillo}) -> {sw_name}:{sw_port}")

        # --- APLICANDO TOPOLOGÍA DEL DIAGRAMA ---
        print("\n🔧 Mapeando Switch 1...")
        for p in range(1, 25): Link("SW1", p, "PP1", p, p, "PASILLO 1", 1)
        for p in range(1, 4):  Link("SW1", 24+p, "PP2", p, 24+p, "PASILLO 1", 1)
        for p in range(1, 22): Link("SW1", 27+p, "PP2", 3+p, p, "PASILLO 2", 1)

        print("\n🔧 Mapeando Switch 2...")
        for p in range(1, 10): Link("SW2", p, "PP3", p, 21+p, "PASILLO 2", 1)
        for p in range(1, 16): Link("SW2", 9+p, "PP3", 9+p, p, "PASILLO 3", 1)
        for p in range(1, 25): Link("SW2", 24+p, "PP4", p, 15+p, "PASILLO 3", 1)

        print("\n🔧 Mapeando Switch 3...")
        for p in range(1, 5):  Link("SW3", p, "PP5", p, 39+p, "PASILLO 3", 1)
        # Holes 5-6
        for p in range(1, 19): Link("SW3", 6+p, "PP5", 6+p, p, "PASILLO 1", 2)
        for p in range(1, 25): Link("SW3", 24+p, "PP6", p, 18+p, "PASILLO 1", 2)

        print("\n🔧 Mapeando Switch 4...")
        for p in range(1, 19): Link("SW4", p, "PP7", p, 42+p, "PASILLO 1", 2)
        for p in range(1, 7):  Link("SW4", 18+p, "PP7", 18+p, p, "PASILLO 2", 2)
        for p in range(1, 13): Link("SW4", 24+p, "PP8", p, 6+p, "PASILLO 2", 2)
        for p in range(1, 11): Link("SW4", 38+p, "PP8", 14+p, p, "PASILLO 3", 2)

        print("\n🔧 Mapeando Switch 5...")
        for p in range(1, 18): Link("SW5", p, "PP9", p, 12+p, "PASILLO 3", 2)

        db.session.commit()
        print("\n✅ ¡Sincronización Perfecta Completada!")

if __name__ == "__main__":
    import_infra_fisica_v3()
