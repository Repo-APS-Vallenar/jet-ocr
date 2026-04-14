import psycopg2
import sys
import json

# URL de conexión a Supabase
DB_URI = "postgresql://postgres.afusiddjuczrkzltnfae:1J3e9t8b.$$.@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

def run_sql(sql):
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute(sql)
        
        # Si la consulta devuelve resultados (SELECT)
        if cur.description:
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            result = [dict(zip(colnames, row)) for row in rows]
        else:
            # Si es un INSERT/UPDATE/DELETE
            conn.commit()
            result = {"status": "Ejecutado con éxito"}
            
        cur.close()
        conn.close()
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: py query_db.py \"SELECT * FROM ...\"")
    else:
        sql = sys.argv[1]
        print(json.dumps(run_sql(sql), indent=2, default=str))
