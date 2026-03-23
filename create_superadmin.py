import uuid
from app import app, db, Company, Usuario
from werkzeug.security import generate_password_hash

def crear_superadmin():
    with open("create_log.txt", "w") as f_log:
        f_log.write("Iniciando creación de superadmin...\n")
        try:
            with app.app_context():
                f_log.write("Contexto de app cargado.\n")
                
                nombre_empresa = "SaaS Management & Support"
                empresa = Company.query.filter_by(name=nombre_empresa).first()
                f_log.write(f"Empresa encontrada: {empresa is not None}\n")
                
                if not empresa:
                    empresa = Company(
                        id=uuid.uuid4(),
                        name=nombre_empresa,
                        plan_type='Premium',
                        scans_quota=99999,
                        operadores_limit=999
                    )
                    db.session.add(empresa)
                    db.session.commit()
                    f_log.write(f"Empresa '{nombre_empresa}' creada.\n")

                correo_master = "businesswolsmart@gmail.com"
                clave_master = "1j3e9t8b"

                usuario = Usuario.query.filter_by(correo=correo_master).first()
                f_log.write(f"Usuario encontrado: {usuario is not None}\n")
                
                if not usuario:
                    usuario = Usuario(
                        correo=correo_master,
                        password_hash=generate_password_hash(clave_master),
                        rol='Admin',
                        company_id=empresa.id
                    )
                    db.session.add(usuario)
                    db.session.commit()
                    f_log.write(f"SuperAdmin {correo_master} creado existosamente.\n")
                else:
                    usuario.password_hash = generate_password_hash(clave_master)
                    usuario.company_id = empresa.id
                    db.session.commit()
                    f_log.write(f"SuperAdmin {correo_master} actualizado.\n")
                    
        except Exception as e:
            f_log.write(f"ERROR: {str(e)}\n")

if __name__ == '__main__':
    crear_superadmin()
