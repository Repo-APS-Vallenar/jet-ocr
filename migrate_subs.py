import psycopg2
from datetime import datetime, timedelta

DB_URI = "postgresql://postgres.afusiddjuczrkzltnfae:1J3e9t8b.$$.@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

def migrate():
    try:
        conn = psycopg2.connect(DB_URI)
        cursor = conn.cursor()
        
        # Agregar columnas si no existen
        queries = [
            "ALTER TABLE companies ADD COLUMN IF NOT EXISTS plan_type VARCHAR(20) DEFAULT 'Freemium';",
            "ALTER TABLE companies ADD COLUMN IF NOT EXISTS scans_quota INTEGER DEFAULT 30;",
            "ALTER TABLE companies ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP;",
            "ALTER TABLE companies ADD COLUMN IF NOT EXISTS admins_limit INTEGER DEFAULT 1;",
            "ALTER TABLE companies ADD COLUMN IF NOT EXISTS operadores_limit INTEGER DEFAULT 2;"
        ]
        
        for q in queries:
            try:
                cursor.execute(q)
                print(f"Executed: {q}")
            except Exception as e:
                print(f"Error executing {q}: {e}")
                conn.rollback()
        
        # Poblar trial_ends_at para cuentas existentes (14 días desde ahora)
        future_date = datetime.now() + timedelta(days=14)
        cursor.execute("UPDATE companies SET trial_ends_at = %s WHERE trial_ends_at IS NULL;", (future_date,))
        print("Updated existing companies with trial date.")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Migration completed successfully.")
        
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == '__main__':
    migrate()
