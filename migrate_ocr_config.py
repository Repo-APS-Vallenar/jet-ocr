from app import app, db, OcrConfig

with app.app_context():
    # Solo crea tablas que no existen. No borra nada.
    db.create_all()
    print("Tabla ocr_configs asegurada en la Base de Datos.")
