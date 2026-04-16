import json
import os
import uuid
from flask import Flask
from app import db, InfraElement, InfraPort, Company

# Usamos la misma DB que la app principal importándola de app.py
from app import app, db, InfraElement, InfraPort, Company

def importar_red():
    with app.app_context():
        # 1. Obtener la compañía por defecto (o crearla)
        company = Company.query.first()
        if not company:
            print("❌ No se encontró compañía.")
            return

        # Calcular ruta absoluta del JSON
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, 'uploads', 'PUNTOS POR BOX.json')
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📦 Cargando {len(data)} ubicaciones...")

        # 2. Crear Elementos (5 Switches y 9 Patch Panels) si no existen
        elementos = {}
        for i in range(1, 6):
            name = f"Switch {i}"
            sw = InfraElement.query.filter_by(nombre=name, company_id=company.id).first()
            if not sw:
                sw = InfraElement(nombre=name, tipo='SWITCH', total_puertos=48, company_id=company.id, piso='1')
                db.session.add(sw)
            elementos[f"SW{i}"] = sw
            
        for i in range(1, 10):
            name = f"Patch Panel {i}"
            pp = InfraElement.query.filter_by(nombre=name, company_id=company.id).first()
            if not pp:
                # Los patch panels suelen ser de 24 o superior, usemos 24 por defecto o 48 segun necesidad
                pp = InfraElement(nombre=name, tipo='PATCH_PANEL', total_puertos=24, company_id=company.id, piso='1')
                db.session.add(pp)
            elementos[f"PP{i}"] = pp
        
        db.session.commit()

        # 3. Procesar cada box y sus puntos (Cableado)
        for item in data:
            ubicacion = item['ubicacion']
            for punto in item.get('puntos_red', []):
                etiqueta = punto['etiqueta_sugerida']
                # P30-30-SW2
                parts = etiqueta.split('-')
                if len(parts) >= 3:
                    try:
                        p_patch_num = int(parts[0].replace('P', ''))
                        p_switch_num = int(parts[1])
                        sw_key = parts[2]
                        
                        # Buscamos el switch (Destino Logico)
                        sw_obj = elementos.get(sw_key)
                        # Buscamos un Patch Panel (Origen Fisico) -> Asumimos PP1 como base si no hay mas info
                        # O mejor, podriamos inferir el PP si el numero de puerto patch es >24 etc.
                        # Para este ejemplo, usaremos PP1 o PP2 segun el numero de puerto
                        pp_key = "PP1" if p_patch_num <= 24 else "PP2" 
                        pp_obj = elementos.get(pp_key)

                        if sw_obj and pp_obj:
                            # Determinar color por uso
                            color = "#ffa500" # Naranja (Datos) por defecto
                            serv = "Datos"
                            usos = str(item.get('uso', '')).upper()
                            if "WAP" in usos or "WIFI" in usos:
                                color = "#00ffff" # Cian (AP)
                                serv = "AP"
                            elif "VOICE" in usos or "VOZ" in usos:
                                color = "#0000ff" # Azul (FortiVoice)
                                serv = "Voz"

                            # 1. Creamos puerto en Switch (con color y servicio)
                            p_sw = InfraPort.query.filter_by(element_id=sw_obj.id, numero_puerto=p_switch_num).first()
                            if not p_sw:
                                p_sw = InfraPort(element_id=sw_obj.id, numero_puerto=p_switch_num, tipo_servicio=serv, destino=ubicacion, color_hex=color)
                                db.session.add(p_sw)
                                db.session.commit()

                            # 2. Creamos puerto en Patch Panel y los conectamos
                            p_pp = InfraPort.query.filter_by(element_id=pp_obj.id, numero_puerto=p_patch_num).first()
                            if not p_pp:
                                p_pp = InfraPort(
                                    element_id=pp_obj.id, 
                                    numero_puerto=p_patch_num, 
                                    tipo_servicio=serv, 
                                    destino=ubicacion, 
                                    color_hex=color,
                                    tag=f"P{p_patch_num}",
                                    conectado_a_id=p_sw.id
                                )
                                db.session.add(p_pp)
                            
                        print(f"🔗 Conectado: Box {ubicacion} -> {sw_key}:{p_switch_num}")
                    except Exception as e:
                        print(f"⚠️ Error procesando {etiqueta}: {e}")

        db.session.commit()
        print("✅ Importación de Red y Cableado completada!")

if __name__ == '__main__':
    importar_red()
