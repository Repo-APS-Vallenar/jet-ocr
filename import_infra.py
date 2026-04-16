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

        # 2. Crear los 5 Switches por defecto si no existen
        switches = {}
        for i in range(1, 6):
            nombre = f"Switch {i}"
            sw = InfraElement.query.filter_by(nombre=nombre, company_id=company.id).first()
            if not sw:
                sw = InfraElement(nombre=nombre, tipo='SWITCH', total_puertos=48, company_id=company.id)
                db.session.add(sw)
                db.session.commit()
            switches[f"SW{i}"] = sw

        # 3. Procesar cada box y sus puntos
        for item in data:
            ubicacion = item['ubicacion']
            for punto in item.get('puntos_red', []):
                etiqueta = punto['etiqueta_sugerida']
                # Etiqueta format: P30-30-SW2 -> [PatchPort, SwitchPort, SwitchName]
                parts = etiqueta.split('-')
                if len(parts) >= 3:
                    try:
                        p_patch = parts[0].replace('P', '')
                        p_switch = int(parts[1])
                        sw_key = parts[2]
                        
                        if sw_key in switches:
                            sw_obj = switches[sw_key]
                            
                            # Crear el puerto en el switch si no existe
                            port_obj = InfraPort.query.filter_by(
                                element_id=sw_obj.id, 
                                numero_puerto=p_switch
                            ).first()
                            
                            if not port_obj:
                                # Determinar color por uso
                                color = "#ffa500" # Naranja (Datos) por defecto
                                serv = "Datos"
                                if "WAP" in str(item.get('uso', '')):
                                    color = "#00ffff" # Cian (AP)
                                    serv = "AP"
                                
                                port_obj = InfraPort(
                                    element_id=sw_obj.id,
                                    numero_puerto=p_switch,
                                    tipo_servicio=serv,
                                    destino=f"{ubicacion} (PP {p_patch})",
                                    color_hex=color
                                )
                                db.session.add(port_obj)
                    except Exception as e:
                        print(f"⚠️ Error procesando {etiqueta}: {e}")

        db.session.commit()
        print("✅ Importación de Red completada con éxito!")

if __name__ == '__main__':
    importar_red()
