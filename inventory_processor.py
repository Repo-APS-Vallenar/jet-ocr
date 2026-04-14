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
    print(f"🚀 Iniciando proceso de catastro experto...")
    df = pd.read_excel(file_path)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    summary = {"created": 0, "errors": 0}
    
    for _, row in df.iterrows():
        try:
            nombre = str(row.get('Nombre_Equipo', 'Equipo Desconocido'))
            serial = str(row.get('Serie', 'N/A'))
            modelo = str(row.get('Modelo', 'N/A'))
            codigo_puesto = str(row.get('Codigo_Puesto', ''))
            boca_red = str(row.get('Boca_Red', ''))
            categoria = str(row.get('Categoria', 'Hardware'))
            
            # Buscar Workstation vinculada
            cur.execute("SELECT id FROM workstations WHERE codigo_puesto = %s", (codigo_puesto,))
            ws_res = cur.fetchone()
            ws_id = ws_res[0] if ws_res else None
            
            datos_dinamicos = json.dumps({
                "modelo": modelo,
                "boca_red": boca_red, 
                "fecha_catastro": str(datetime.now().date()),
                "responsabilidad_legal": "Fianza CESFAM"
            })
            
            # Dejamos que el ID sea autoincremental (serial)
            sql = """
                INSERT INTO equipos (nombre, sn, workstation_id, datos_dinamicos, categoria, estado)
                VALUES (%s, %s, %s, %s, %s, 'Operativo')
                ON CONFLICT (sn) DO UPDATE SET 
                workstation_id = EXCLUDED.workstation_id,
                datos_dinamicos = EXCLUDED.datos_dinamicos
                RETURNING id
            """
            cur.execute(sql, (nombre, serial, ws_id, datos_dinamicos, categoria))
            final_id = cur.fetchone()[0]
            
            # Generar QR con el ID numérico
            qr_link = f"{BASE_URL}/equipo/{final_id}"
            qr_file = f"{QR_OUTPUT_DIR}/{codigo_puesto}_{serial}.png"
            generate_styled_qr(qr_link, qr_file, f"{codigo_puesto} | {serial}")

            
            summary["created"] += 1
            print(f"✅ Procesado: {nombre} [{codigo_puesto}]")
            
        except Exception as e:
            summary["errors"] += 1
            print(f"❌ Error en fila: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✨ RESUMEN: {summary['created']} equipos procesados, {summary['errors']} errores.")

if __name__ == "__main__":
    from datetime import datetime
    init_process()
    print("🚀 Iniciando procesamiento automático de INVENTARIO_AN.xlsx...")
    process_excel('INVENTARIO_AN.xlsx')

