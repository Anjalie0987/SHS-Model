import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Step 1: Adding soil_sample_id to soil_health_score for better linking...")
    cur.execute("ALTER TABLE soil_health_score ADD COLUMN IF NOT EXISTS soil_sample_id INTEGER")
    
    # Link scores to samples based on creation date and farm_id (or just link them all)
    cur.execute("""
        UPDATE soil_health_score sh
        SET soil_sample_id = s.soil_sample_id
        FROM soil_sample s
        WHERE sh.created_at = s.sample_date AND sh.soil_sample_id IS NULL
    """)
    conn.commit()
    print("Step 1 Complete.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
