from app import app, db, Company, OcrConfig

with app.app_context():
    companies = Company.query.all()
    created_count = 0
    for c in companies:
        # Verificar si ya tiene config
        existente = OcrConfig.query.filter_by(company_id=c.id).first()
        if not existente:
            config = OcrConfig(
                company_id=c.id, 
                sn_prefix=None, 
                sn_length=None, 
                require_mac=True, # Mantener compatibilidad anterior
                require_pn=False,
                require_ean=False
            )
            db.session.add(config)
            created_count += 1
            
    db.session.commit()
    print(f"OK: Se inicializo la configuracion OCR para {created_count} empresas.")
