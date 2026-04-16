import json
import os
from app import app, db, InfraElement, InfraPort
from sqlalchemy import text

def get_abs_path(relative_path):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

# MAPA DE SERVICIOS Y COLORES (Basado en leyenda de la imagen)
COLOR_SERVICE = {
    "AP": "#00ffff",        # Cyan
    "BIOMETRICO": "#00ff00", # VERDE (Reloj)
    "WAP": "#00ffff",       # Cyan
    "DATOS": "#ffa500",     # Naranja (Punto de datos)
    "TELEFONIA": "#0000ff", # Azul (FortiVoice)
    "FORTIVOICE": "#0000ff"
}

def import_infra_fisica():
    with app.app_context():
        print("🚀 Iniciando Importación Topológica basada en Diagrama...")
        
        # 1. Limpiar datos previos
        db.session.query(InfraPort).delete()
        db.session.query(InfraElement).delete()
        db.session.commit()

        # 2. Crear Elementos del Rack (Exactamente 5 Switches y 9 Patch Panels)
        elementos = {}
        
        # Creación de Switches (48 puertos cada uno según diagrama)
        for i in range(1, 6):
            piso = 1 if i <= 3 else 2
            sw = InfraElement(nombre=f"Switch {i}", tipo="SWITCH", total_puertos=48, piso=piso)
            db.session.add(sw)
            elementos[f"SW{i}"] = sw

        # Creación de Patch Panels (24 bocas c/u)
        for i in range(1, 10):
            piso = 1 if i <= 5 else 2
            pp = InfraElement(nombre=f"Patch Panel {i}", tipo="PATCH_PANEL", total_puertos=24, piso=piso)
            db.session.add(pp)
            elementos[f"PP{i}"] = pp
        
        # Elementos Especiales
        fw = InfraElement(nombre="Firewall FG-60F", tipo="OTRO", total_puertos=8, piso=2)
        voip = InfraElement(nombre="FortiVoice 200 F8", tipo="OTRO", total_puertos=4, piso=2)
        db.session.add_all([fw, voip])
        db.session.flush()

        # 3. Cargar datos del JSON (La fuente de los puntos reales)
        json_path = get_abs_path('uploads/PUNTOS POR BOX.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            puntos_json = json.load(f)

        # Helper para encontrar un punto especifico en el JSON
        def buscar_punto(id_punto, pasillo, piso):
            for p in puntos_json:
                # Normalizamos pasillo y piso para la búsqueda
                if str(p.get("ID_PUNTO")) == str(id_punto) and \
                   pasillo.upper() in p.get("PASILLO", "").upper() and \
                   int(p.get("PISO", 1)) == int(piso):
                    return p
            return None

        def crear_puerto(element, num, punto_data=None, conectado_a_id=None):
            tag = f"P{punto_data['ID_PUNTO']}" if punto_data else ""
            destino = f"Box {punto_data['BOX']} - {punto_data['PASILLO']}" if punto_data else "Libre"
            servicio = (punto_data['SERVICIO'] or "DATOS").upper() if punto_data else "VAC"
            color = COLOR_SERVICE.get(servicio, "#ffffff")
            
            port = InfraPort(
                element_id=element.id,
                numero_puerto=num,
                tipo_servicio=servicio,
                destino=destino,
                color_hex=color,
                tag=tag,
                conectado_a_id=conectado_a_id
            )
            db.session.add(port)
            return port

        # 4. IMPLEMENTACIÓN DEL MAPEADO FÍSICO (LA MAGIA)
        
        # --- SWITCH 1 ---
        # 1-24 -> PP1 (P1-P24 de Pasillo 1)
        # 25-27 -> PP2 (P25-P27 de Pasillo 1)
        # 28-48 -> PP2 (P1-P21 de Pasillo 2)
        for i in range(1, 25):
            p = buscar_punto(i, "PASILLO 1", 1)
            sw_p = crear_puerto(elementos["SW1"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP1"], i, p, sw_p.id)

        for i, tag_val in enumerate(range(25, 28), 25):
            p = buscar_punto(tag_val, "PASILLO 1", 1)
            sw_p = crear_puerto(elementos["SW1"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP2"], i-24, p, sw_p.id)

        for i, tag_val in enumerate(range(1, 22), 28):
            p = buscar_punto(tag_val, "PASILLO 2", 1)
            sw_p = crear_puerto(elementos["SW1"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP2"], (i-28)+4, p, sw_p.id)

        # --- SWITCH 2 ---
        # 1-9 -> PP3 (P22-P30 de Pasillo 2)
        # 10-24 -> PP3 (P1-P15 de Pasillo 3)
        # 25-48 -> PP4 (P16-P39 de Pasillo 3)
        for i, tag_val in enumerate(range(22, 31), 1):
            p = buscar_punto(tag_val, "PASILLO 2", 1)
            sw_p = crear_puerto(elementos["SW2"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP3"], i, p, sw_p.id)

        for i, tag_val in enumerate(range(1, 16), 10):
            p = buscar_punto(tag_val, "PASILLO 3", 1)
            sw_p = crear_puerto(elementos["SW2"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP3"], (i-10)+10, p, sw_p.id)

        for i, tag_val in enumerate(range(16, 40), 25):
            p = buscar_punto(tag_val, "PASILLO 3", 1)
            sw_p = crear_puerto(elementos["SW2"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP4"], i-24, p, sw_p.id)

        # --- SWITCH 3 ---
        for i, tag_val in enumerate(range(40, 44), 1):
            p = buscar_punto(tag_val, "PASILLO 3", 1)
            sw_p = crear_puerto(elementos["SW3"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP5"], i, p, sw_p.id)
        
        # 5-6 VAC
        crear_puerto(elementos["SW3"], 5)
        crear_puerto(elementos["SW3"], 6)

        for i, tag_val in enumerate(range(1, 19), 7):
            p = buscar_punto(tag_val, "PASILLO 1", 2)
            sw_p = crear_puerto(elementos["SW3"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP5"], (i-7)+7, p, sw_p.id)

        for i, tag_val in enumerate(range(19, 43), 25):
            p = buscar_punto(tag_val, "PASILLO 1", 2)
            sw_p = crear_puerto(elementos["SW3"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP6"], i-24, p, sw_p.id)

        # --- SWITCH 4 ---
        for i, tag_val in enumerate(range(43, 61), 1):
            p = buscar_punto(tag_val, "PASILLO 1", 2)
            sw_p = crear_puerto(elementos["SW4"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP7"], i, p, sw_p.id)

        for i, tag_val in enumerate(range(1, 7), 19):
            p = buscar_punto(tag_val, "PASILLO 2", 2)
            sw_p = crear_puerto(elementos["SW4"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP7"], (i-19)+19, p, sw_p.id)

        for i, tag_val in enumerate(range(7, 19), 25):
            p = buscar_punto(tag_val, "PASILLO 2", 2)
            sw_p = crear_puerto(elementos["SW4"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP8"], i-24, p, sw_p.id)
        
        # 37-38 VAC
        crear_puerto(elementos["SW4"], 37)
        crear_puerto(elementos["SW4"], 38)

        for i, tag_val in enumerate(range(1, 11), 39):
            p = buscar_punto(tag_val, "PASILLO 3", 2)
            sw_p = crear_puerto(elementos["SW4"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP8"], (i-39)+15, p, sw_p.id)

        # --- SWITCH 5 ---
        for i, tag_val in enumerate(range(13, 30), 1):
            p = buscar_punto(tag_val, "PASILLO 3", 2)
            sw_p = crear_puerto(elementos["SW5"], i, p)
            db.session.flush()
            crear_puerto(elementos["PP9"], (i-1)+12, p, sw_p.id)

        # Conexiones Especiales del SW5
        fw_p = InfraPort(element_id=fw.id, numero_puerto=1, destino="UPLINK SW5:35", tag="PORT A", color_hex="#0000ff")
        db.session.add(fw_p)
        db.session.flush()
        crear_puerto(elementos["SW5"], 35, { "ID_PUNTO": "A", "BOX": "FW", "PASILLO": "RACK", "SERVICIO": "TELEFONIA" }, fw_p.id)

        voip_p = InfraPort(element_id=voip.id, numero_puerto=1, destino="UPLINK SW5:36", tag="PORT 1", color_hex="#0000ff")
        db.session.add(voip_p)
        db.session.flush()
        crear_puerto(elementos["SW5"], 36, { "ID_PUNTO": "1", "BOX": "VOIP", "PASILLO": "RACK", "SERVICIO": "TELEFONIA" }, voip_p.id)

        db.session.commit()
        print("✅ ¡Topología completada! Tu red digital es ahora un espejo de tu rack físico.")

if __name__ == "__main__":
    import_infra_fisica()
