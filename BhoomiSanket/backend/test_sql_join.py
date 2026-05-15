import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Testing SQL Join for subdistricts...")
    cur.execute("""
        SELECT v.name, count(sh.soil_health_score_id)
        FROM old_village v
        JOIN soil_sample s ON v.village_id = s.village_id
        JOIN soil_health_score sh ON s.soil_sample_id = sh.soil_sample_id
        WHERE s.stage = 'Germination'
        GROUP BY v.name
        LIMIT 10
    """)
    res = cur.fetchall()
    print(f"Aggregation Result: {res}")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
