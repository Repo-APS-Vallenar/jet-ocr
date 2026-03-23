import sys
sys.path.append('.')
from app import app, db
from sqlalchemy import text

with app.app_context():
    print("Creando nuevas tablas si no existen...")
    db.create_all()
    
    print("Agregando columnas a tablas existentes...")
    
    # Agregar workstation_id a equipos
    try:
        db.session.execute(text('ALTER TABLE equipos ADD COLUMN workstation_id UUID;'))
        # Asegurarnos de que sea foránea (opcional si SQLAlchemy lo maneja, pero en BD real es mejor)
        db.session.execute(text('ALTER TABLE equipos ADD CONSTRAINT fk_equipos_workstation FOREIGN KEY (workstation_id) REFERENCES workstations(id);'))
        db.session.commit()
        print("Columna workstation_id en equipos añadida con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Bypass equipos.workstation_id (probablemente ya existe): {e}")

    # Agregar company_id a usuarios
    try:
        db.session.execute(text('ALTER TABLE usuarios ADD COLUMN company_id UUID;'))
        db.session.execute(text('ALTER TABLE usuarios ADD CONSTRAINT fk_usuarios_company FOREIGN KEY (company_id) REFERENCES companies(id);'))
        db.session.commit()
        print("Columna company_id en usuarios añadida con éxito.")
    except Exception as e:
        db.session.rollback()
        print(f"Bypass usuarios.company_id (probablemente ya existe): {e}")
        
    print("Migración de esquema completada.")
