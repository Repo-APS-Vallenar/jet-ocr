import json
import os
from app import app, db, InfraElement, InfraPort
from sqlalchemy import text

def get_abs_path(relative_path):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

COLOR_SERVICE = {
    "AP": "#00ffff",        # Cyan
    "BIOMETRICO": "#00ff00", # Verde (Reloj)
    "RELOJ": "#00ff00",
    "DATOS": "#ffa500",     # Naranja
    "FORTINET": "#ffff00",  # Amarillo (Punto Fortinet)
    "TELEFONIA": "#0000ff", # Azul
    "VOZ": "#0000ff",
    "VAC": "#ffffff"
}

def import_infra_fisica_v2():
    with app.app_context():
        print("🚀 Iniciando Importación Topológica de Alta Precisión (v2)...")
        db.session.query(InfraPort).delete()
        db.session.query(InfraElement).delete()
        db.session.commit()

        # 1. Crear Equipos Principal
        sws = {}
        for i in range(1, 6):
            sw = InfraElement(nombre=f"Switch {i}", tipo="SWITCH", total_puertos=48, piso=(1 if i <= 3 else 2))
            db.session.add(sw)
            sws[f"SW{i}"] = sw

        pps = {}
        for i in range(1, 10):
            pp = InfraElement(nombre=f"Patch Panel {i}", tipo="PATCH_PANEL", total_puertos=24, piso=(1 if i <= 5 else 2))
            db.session.add(pp)
            pps[f"PP{i}"] = pp
        
        fw = InfraElement(nombre="Firewall FG-60F", tipo="OTRO", total_puertos=8, piso=2)
        voip = InfraElement(nombre="FortiVoice 200 F8", tipo="OTRO", total_puertos=4, piso=2)
        db.session.add_all([fw, voip])
        db.session.flush()

        # 2. Cargar JSON
        with open(get_abs_path('uploads/PUNTOS POR BOX.json'), 'r', encoding='utf-8') as f:
            puntos_json = json.load(f)

        def find_p(id_punto, pasillo, piso):
            for p in puntos_json:
                p_id = str(p.get("ID_PUNTO"))
                p_pas = p.get("PASILLO", "").upper()
                p_piso = int(p.get("PISO", 1))
                if p_id == str(id_punto) and pasillo.upper() in p_pas and p_piso == int(piso):
                    return p
            return None

        # Helper para crear los dos extremos de la conexión
        def Link(sw_name, sw_port, pp_name, pp_port, tag_id, pasillo, piso):
            p_data = find_p(tag_id, pasillo, piso)
            tag_str = f"P{tag_id}" if tag_id else ""
            
            # Datos del Switch
            sw_obj = sws[sw_name]
            servicio = (p_data['SERVICIO'] or "DATOS").upper() if p_data else "VAC"
            destino = f"Box {p_data['BOX']} - {p_data['PASILLO']}" if p_data else "Libre"
            color = COLOR_SERVICE.get(servicio, "#ffa500")

            # Puerto en Switch
            psw = InfraPort(element_id=sw_obj.id, numero_puerto=sw_port, tipo_servicio=servicio, destino=destino, color_hex=color, tag=tag_str)
            db.session.add(psw)
            db.session.flush()

            # Puerto en Patch Panel
            if pp_name:
                ppp = InfraPort(element_id=pps[pp_name].id, numero_puerto=pp_port, tipo_servicio=servicio, destino=destino, color_hex=color, tag=tag_str, conectado_a_id=psw.id)
                db.session.add(ppp)
                psw.conectado_a_id = ppp.id # Bidireccional

        # --- REGLAS DE ORO DEL DIAGRAMA ---

        # SW1 (Precisión 100%)
        for p in range(1, 25): Link("SW1", p, "PP1", p, p, "PASILLO 1", 1)
        for p in range(1, 4):  Link("SW1", 24+p, "PP2", p, 24+p, "PASILLO 1", 1)
        for p in range(1, 22): Link("SW1", 27+p, "PP2", 3+p, p, "PASILLO 2", 1)

        # SW2 (Mapeo Pasillo 2 y 3)
        for p in range(1, 10): Link("SW2", p, "PP3", p, 21+p, "PASILLO 2", 1)
        for p in range(1, 16): Link("SW2", 9+p, "PP3", 9+p, p, "PASILLO 3", 1)
        for p in range(1, 25): Link("SW2", 24+p, "PP4", p, 15+p, "PASILLO 3", 1)

        # SW3 (El desafío de los VAC)
        for p in range(1, 5):  Link("SW3", p, "PP5", p, 39+p, "PASILLO 3", 1)
        # 5 y 6 son VAC en Switch y PP
        db.session.add(InfraPort(element_id=sws["SW3"].id, numero_puerto=5, tipo_servicio="VAC"))
        db.session.add(InfraPort(element_id=sws["SW3"].id, numero_puerto=6, tipo_servicio="VAC"))
        db.session.add(InfraPort(element_id=pps["PP5"].id, numero_puerto=5, tipo_servicio="VAC"))
        db.session.add(InfraPort(element_id=pps["PP5"].id, numero_puerto=6, tipo_servicio="VAC"))
        
        for p in range(1, 19): Link("SW3", 6+p, "PP5", 6+p, p, "PASILLO 1", 2)
        for p in range(1, 25): Link("SW3", 24+p, "PP6", p, 18+p, "PASILLO 1", 2)

        # SW4
        for p in range(1, 19): Link("SW4", p, "PP7", p, 42+p, "PASILLO 1", 2)
        for p in range(1, 7):  Link("SW4", 18+p, "PP7", 18+p, p, "PASILLO 2", 2)
        for p in range(1, 13): Link("SW4", 24+p, "PP8", p, 6+p, "PASILLO 2", 2)
        
        # 37-38 VAC en SW4 y PP8
        db.session.add(InfraPort(element_id=sws["SW4"].id, numero_puerto=37, tipo_servicio="VAC"))
        db.session.add(InfraPort(element_id=sws["SW4"].id, numero_puerto=38, tipo_servicio="VAC"))
        db.session.add(InfraPort(element_id=pps["PP8"].id, numero_puerto=13, tipo_servicio="VAC"))
        db.session.add(InfraPort(element_id=pps["PP8"].id, numero_puerto=14, tipo_servicio="VAC"))

        for p in range(1, 11): Link("SW4", 38+p, "PP8", 14+p, p, "PASILLO 3", 2)

        # SW5 (Final: FW y VoIP)
        for p in range(1, 18): Link("SW5", p, "PP9", p, 12+p, "PASILLO 3", 2)
        
        # Conexión Firewall
        sw5_35 = InfraPort(element_id=sws["SW5"].id, numero_puerto=35, tipo_servicio="TELEFONIA", destino="UPLINK FIREWALL", color_hex="#0000ff", tag="FW")
        db.session.add(sw5_35)
        db.session.flush()
        fw_1 = InfraPort(element_id=fw.id, numero_puerto=1, tipo_servicio="TELEFONIA", destino="SW5:35", tag="PORT A", color_hex="#0000ff", conectado_a_id=sw5_35.id)
        db.session.add(fw_1)
        sw5_35.conectado_a_id = fw_1.id

        # Conexión VoIP
        sw5_36 = InfraPort(element_id=sws["SW5"].id, numero_puerto=36, tipo_servicio="TELEFONIA", destino="UPLINK VOIP", color_hex="#0000ff", tag="VOIP")
        db.session.add(sw5_36)
        db.session.flush()
        voip_1 = InfraPort(element_id=voip.id, numero_puerto=1, tipo_servicio="TELEFONIA", destino="SW5:36", tag="PORT 1", color_hex="#0000ff", conectado_a_id=sw5_36.id)
        db.session.add(voip_1)
        sw5_36.conectado_a_id = voip_1.id

        db.session.commit()
        print("✅ Importación de Alta Precisión completada. ¡Rack sincronizado!")

if __name__ == "__main__":
    import_infra_fisica_v2()
