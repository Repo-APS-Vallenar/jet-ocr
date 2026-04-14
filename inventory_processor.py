from datetime import datetime
import pandas as pd
import qrcode
import os
import uuid
import json
import psycopg2
from PIL import Image, ImageDraw, ImageFont

# Configuración - AJUSTA TU DOMINIO AQUÍ
BASE_URL = "https://wolsmartbusiness.com" 
QR_OUTPUT_DIR = "static/qrcodes_catastro"
DB_URI = "postgresql://postgres.afusiddjuczrkzltnfae:1J3e9t8b.$$.@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

def init_process():
    if not os.path.exists(QR_OUTPUT_DIR):
        os.makedirs(QR_OUTPUT_DIR)

def get_db_connection():
    return psycopg2.connect(DB_URI)

def generate_styled_qr(data, filename, label):
    """Genera un QR con una etiqueta de texto abajo para fácil identificación física"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Añadir margen para el texto
    width, height = qr_img.size
    new_height = height + 50
    final_img = Image.new('RGB', (width, new_height), 'white')
    final_img.paste(qr_img, (0, 0))
    
    # Añadir texto
    draw = ImageDraw.Draw(final_img)
    try:
        # Intenta usar una fuente del sistema, si no usa la default
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        
    text_bbox = draw.textbbox((0, 0), label, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    draw.text(((width - text_width) / 2, height - 5), label, fill="black", font=font)
    
    final_img.save(filename)

def process_excel(file_path):
    print(f"🚀 Iniciando buscador de inventario multi-hoja...")
    xls = pd.ExcelFile(file_path)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    summary = {"created": 0, "errors": 0}
    
    for sheet_name in xls.sheet_names:
        print(f"\n📖 Procesando hoja: [{sheet_name}]")
        df_raw = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        # Buscar cabecera en esta hoja
        header_row = -1
        for i, row in df_raw.iterrows():
            row_str = " ".join([str(x).upper() for x in row.values])
            if any(k in row_str for k in ['MARCA', 'MODELO', 'SERIAL', 'SERIE', 'ROUTER', 'UBICACION']):
                header_row = i
                break
        
        if header_row == -1:
            print(f"⚠️ No se encontró cabecera válida en '{sheet_name}', saltando...")
            continue
            
        print(f"📍 Cabecera detectada en fila: {header_row}")
        df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        for _, row in df.iterrows():
            try:
                if row.isnull().all(): continue

                # Función de limpieza robusta
                def clean(val, default=''):
                    v = str(val).strip()
                    if v.lower() in ['nan', 'none', 'n/a', 'null', '']:
                        return default
                    return v

                marca = clean(row.get('MARCA', row.get('ROUTER', row.get('UNIDAD', ''))))
                modelo = clean(row.get('MODELO', ''))
                serial = clean(row.get('N. SERIE', row.get('N SERIE', row.get('SERIE', row.get('SERIAL', '')))), 'N/A')
                
                # Inteligencia: Si el modelo parece un serial y el serial está vacío, moverlo
                # Un serial suele tener letras y números y no tiene espacios
                if serial == 'N/A' and len(modelo) > 5 and any(c.isdigit() for c in modelo) and any(c.isalpha() for c in modelo) and ' ' not in modelo:
                    serial = modelo
                    modelo = 'Modelo Genérico'
                
                # Nombre final
                if marca and modelo:
                    nombre = f"{marca} {modelo}"
                elif marca or modelo:
                    nombre = marca or modelo
                else:
                    nombre = f"Equipo {serial}" if serial != 'N/A' else "Equipo Desconocido"
                
                # Si sigue siendo basura, saltamos
                if serial == 'N/A' and nombre == "Equipo Desconocido":
                    continue

                ubicacion = clean(row.get('UBICACIÓN', row.get('UBICACION', 'N/A')), 'N/A')
                
                # Capturar TODO técnicamente
                full_data = {}
                for col in df.columns:
                    val = row.get(col)
                    val_clean = clean(val, None)
                    if val_clean and "UNNAMED" not in str(col).upper():
                        if pd.api.types.is_datetime64_any_dtype(val) or hasattr(val, 'isoformat'):
                            full_data[str(col).lower()] = str(val)
                        else:
                            full_data[str(col).lower()] = val_clean

                full_data["fecha_catastro"] = str(datetime.now().date())
                full_data["hoja_origen"] = sheet_name
                
                datos_dinamicos = json.dumps(full_data)
                
                # Buscar Workstation vinculada
                cur.execute("SELECT id FROM workstations WHERE codigo_puesto ILIKE %s OR inherited_zone ILIKE %s", 
                           (f"%{ubicacion}%", f"%{ubicacion}%"))
                ws_res = cur.fetchone()
                ws_id = ws_res[0] if ws_res else None
                
                sql = """
                    INSERT INTO equipos (nombre, sn, workstation_id, datos_dinamicos, categoria, estado)
                    VALUES (%s, %s, %s, %s, 'Hardware', 'Operativo')
                    ON CONFLICT (sn) DO UPDATE SET 
                    nombre = EXCLUDED.nombre,
                    workstation_id = COALESCE(EXCLUDED.workstation_id, equipos.workstation_id),
                    datos_dinamicos = EXCLUDED.datos_dinamicos
                    RETURNING id
                """
                cur.execute(sql, (nombre, serial, ws_id, datos_dinamicos))
                final_id = cur.fetchone()[0]
                
                # Generar QR
                safe_serial = "".join([c for c in serial if c.isalnum()]) or str(final_id)
                qr_link = f"{BASE_URL}/equipo/{final_id}"
                qr_file = os.path.join(QR_OUTPUT_DIR, f"QR_{safe_serial}.png")
                generate_styled_qr(qr_link, qr_file, f"{nombre} | {serial}")
                
                summary["created"] += 1
                print(f"   ✅ {nombre} [{serial}]")
                
            except Exception as e:
                summary["errors"] += 1
                row_data = {k: v for k, v in row.to_dict().items() if pd.notna(v)}
                print(f"   ❌ Error en fila {_+1}: {e}")
                print(f"      📝 Datos conflictivos: {row_data}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✨ FINALIZADO: {summary['created']} procesados, {summary['errors']} errores.")

if __name__ == "__main__":
    init_process()
    print("🚀 Iniciando procesamiento automático de INVENTARIO_AN.xlsx...")
    process_excel('INVENTARIO_AN.xlsx')
