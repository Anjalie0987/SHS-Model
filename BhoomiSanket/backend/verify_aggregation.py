import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Checking aggregated subdistrict stats...")
    cur.execute("""
        SELECT v.name, AVG(sh.score_value) as avg_shs
        FROM old_village v
        JOIN soil_sample s ON v.village_id = s.village_id
        JOIN soil_health_score sh ON s.soil_sample_id = sh.soil_sample_id
        WHERE s.stage ILIKE 'Germination'
        GROUP BY v.name
        LIMIT 20
    """)
    results = cur.fetchall()
    for r in results:
        print(f"  {r[0]}: {r[1]}%")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
