import sys
sys.path.append('.')
from app import app, db
from sqlalchemy import text
import os

with app.app_context():
    print("Agregando columna 'categoria' a la tabla equipos...")
    try:
        db.session.execute(text('ALTER TABLE equipos ADD COLUMN categoria VARCHAR(50) DEFAULT \'TELEFONO\';'))
        db.session.commit()
        print("Columna 'categoria' añadida con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Bypass: {e}")
    
    print("Migración completada.")
