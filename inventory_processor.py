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
    print(f"🚀 Iniciando proceso de catastro experto...")
    # Leer el Excel sin asumir cabecera para buscarla manualmente
    df_raw = pd.read_excel(file_path, header=None)
    
    header_row = 0
    for i, row in df_raw.iterrows():
        # Buscamos una fila que tenga palabras clave de nuestro inventario
        row_str = " ".join([str(x).upper() for x in row.values])
        if 'MARCA' in row_str or 'SERIE' in row_str or 'UBICACION' in row_str or 'UBICACIÓN' in row_str:
            header_row = i
            break
    
    print(f"📍 Cabecera detectada en la fila: {header_row}")
    # Volver a cargar el DF desde la fila correcta
    df = pd.read_excel(file_path, header=header_row)
    
    # Normalización de columnas: quitar espacios y pasar a mayúsculas para evitar fallos
    df.columns = [str(c).strip().upper() for c in df.columns]
    print(f"📊 Columnas reales detectadas: {list(df.columns)}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    summary = {"created": 0, "errors": 0}
    
    for _, row in df.iterrows():
        try:
            # Si toda la fila está vacía, saltar
            if row.isnull().all():
                continue

            # Mapeo según imagen (ahora en MAYÚSCULAS y sin espacios)
            marca = str(row.get('MARCA', '')).replace('nan', '').strip()
            modelo = str(row.get('MODELO', '')).replace('nan', '').strip()
            nombre = f"{marca} {modelo}".strip() or "Equipo Desconocido"
            
            serial = str(row.get('N. SERIE', row.get('N SERIE', 'N/A'))).replace('/', '-').replace('nan', 'N/A').strip()
            # Si el serial sigue siendo N/A o vacío, intentamos con alguna otra columna que se le parezca
            if serial in ['N/A', '', 'None']:
                 serial = str(row.get('SERIE', 'N/A')).replace('nan', 'N/A').strip()
            
            # Si no hay nombre ni serial válido, saltamos la fila (posible fila de adorno en Excel)
            if nombre == "Equipo Desconocido" and serial == 'N/A':
                continue

            ubicacion = str(row.get('UBICACIÓN', row.get('UBICACION', 'N/A'))).replace('nan', 'N/A').strip()
            usuario = str(row.get('USUARIO', 'N/A')).replace('nan', 'N/A').strip()
            
            # Buscar Workstation vinculada por Ubicación (ya que no hay código de puesto explícito)
            cur.execute("SELECT id FROM workstations WHERE codigo_puesto ILIKE %s OR inherited_zone ILIKE %s", 
                       (f"%{ubicacion}%", f"%{ubicacion}%"))
            ws_res = cur.fetchone()
            ws_id = ws_res[0] if ws_res else None
            
            # Capturar TODO el resto de columnas para datos_dinamicos
            full_data = row.to_dict()
            # Convertir fechas a string para JSON si existen
            for k, v in full_data.items():
                if pd.api.types.is_datetime64_any_dtype(v) or hasattr(v, 'isoformat'):
                    full_data[k] = str(v)
                elif pd.isna(v):
                    full_data[k] = None

            full_data["fecha_catastro"] = str(datetime.now().date())
            full_data["responsabilidad_legal"] = "Fianza CESFAM"
            
            datos_dinamicos = json.dumps(full_data)
            
            sql = """
                INSERT INTO equipos (nombre, sn, workstation_id, datos_dinamicos, categoria, estado)
                VALUES (%s, %s, %s, %s, 'Hardware', 'Operativo')
                ON CONFLICT (sn) DO UPDATE SET 
                workstation_id = EXCLUDED.workstation_id,
                datos_dinamicos = EXCLUDED.datos_dinamicos
                RETURNING id
            """
            cur.execute(sql, (nombre, serial, ws_id, datos_dinamicos))
            final_id = cur.fetchone()[0]
            
            # Generar QR (limpiando el nombre del archivo de caracteres raros)
            safe_serial = "".join([c for c in serial if c.isalnum()])
            qr_link = f"{BASE_URL}/equipo/{final_id}"
            qr_file = os.path.join(QR_OUTPUT_DIR, f"QR_{safe_serial}.png")
            
            generate_styled_qr(qr_link, qr_file, f"{nombre} | {serial}")
            
            summary["created"] += 1
            print(f"✅ Procesado: {nombre} [{serial}] en {ubicacion}")
            
        except Exception as e:
            summary["errors"] += 1
            print(f"❌ Error en fila: {e}")

    conn.commit()
    cur.close()
    conn.close()
    print(f"\n✨ RESUMEN: {summary['created']} equipos procesados, {summary['errors']} errores.")

if __name__ == "__main__":
    init_process()
    print("🚀 Iniciando procesamiento automático de INVENTARIO_AN.xlsx...")
    process_excel('INVENTARIO_AN.xlsx')

