import os
import psycopg2
from dotenv import load_dotenv

# Load from backend/.env
env_path = r'd:\CROP2\CROP2\BhoomiSanket\backend\.env'
load_dotenv(env_path)

db_url = os.getenv('DATABASE_URL')
print(f"Connecting to: {db_url}")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT count(*), count(germ_shs), count(boot_shs), count(rip_shs) FROM latlon_suitability;")
    counts = cur.fetchone()
    print(f"Total rows: {counts[0]}")
    print(f"Rows with germ_shs: {counts[1]}")
    print(f"Rows with boot_shs: {counts[2]}")
    print(f"Rows with rip_shs: {counts[3]}")
    
    cur.execute("SELECT rip_shs FROM latlon_suitability WHERE rip_shs IS NOT NULL LIMIT 5;")
    sample = cur.fetchall()
    print(f"Sample rip_shs: {sample}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
