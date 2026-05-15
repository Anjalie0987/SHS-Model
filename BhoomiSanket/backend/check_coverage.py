import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("--- Data Coverage Analysis ---")
    
    # 1. Total Villages vs Villages with Data
    cur.execute("SELECT count(*) FROM village")
    total_villages = cur.fetchone()[0]
    
    cur.execute("SELECT count(DISTINCT village_id) FROM soil_sample WHERE village_id IS NOT NULL")
    villages_with_data = cur.fetchone()[0]
    
    print(f"Total Subdistricts in DB: {total_villages}")
    print(f"Subdistricts with Soil Data: {villages_with_data}")
    print(f"Coverage: {round((villages_with_data/total_villages)*100, 2)}%")

    # 2. List some districts that have NO data
    cur.execute("""
        SELECT d.name, count(s.soil_sample_id) as sample_count
        FROM districts d
        LEFT JOIN village v ON d.district_code = v.district_id
        LEFT JOIN soil_sample s ON v.village_id = s.village_id
        GROUP BY d.name
        ORDER BY sample_count ASC
        LIMIT 10
    """)
    print("\nDistricts with the least data (will appear white):")
    for r in cur.fetchall():
        print(f"  {r[0]}: {r[1]} samples")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
