import os
import psycopg2
from dotenv import load_dotenv

# Load from backend/.env
env_path = r'd:\CROP2\CROP2\BhoomiSanket\backend\.env'
load_dotenv(env_path)

db_url = os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Check Germination distribution in 5% buckets to find the "peak"
    cur.execute("""
        SELECT floor(germ_shs/5)*5 as bucket, count(*) 
        FROM latlon_suitability 
        WHERE germ_shs > 0 
        GROUP BY bucket 
        ORDER BY bucket DESC;
    """)
    print("Germination Distribution (5% buckets):", cur.fetchall())
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
