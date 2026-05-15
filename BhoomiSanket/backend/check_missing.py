import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

# Check districts with ZERO subdistricts colored
cur.execute("""
    SELECT DISTINCT d.name 
    FROM district d 
    JOIN state s ON d.state_id = s.state_id 
    WHERE s.name = 'Maharashtra' 
    AND d.name NOT IN (SELECT DISTINCT district_name FROM latlon_suitability WHERE state_name = 'Maharashtra' AND village_name IS NOT NULL)
""")
missing_districts = [r[0] for r in cur.fetchall()]
print(f"Districts with NO colored subdistricts: {missing_districts}")

# Check coordinates of points that failed to match a village
cur.execute("SELECT lat, lon FROM latlon_suitability WHERE village_name IS NULL LIMIT 10")
print("Sample coordinates that failed to match:")
for r in cur.fetchall():
    print(f"  {r[0]}, {r[1]}")

conn.close()
