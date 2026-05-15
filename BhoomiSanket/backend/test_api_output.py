import requests
import json

try:
    print("Checking API output for subdistricts...")
    r = requests.get('http://127.0.0.1:8001/api/subdistricts')
    data = r.json()
    
    # Check if BHADRAVATI is in the keys
    found = "BHADRAVATI" in data
    print(f"  Is 'BHADRAVATI' in API response? {found}")
    
    if found:
        print(f"  Data for BHADRAVATI: {data['BHADRAVATI']}")
    else:
        # Print some keys to see the format
        print(f"  Sample keys: {list(data.keys())[:10]}")

except Exception as e:
    # If requests fails, use a direct DB check of the aggregation
    import psycopg2
    conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
    cur=conn.cursor()
    cur.execute("""
        SELECT UPPER(TRIM(v.name)) as vname, AVG(sh.score_value)
        FROM old_village v
        JOIN soil_sample s ON v.village_id = s.village_id
        JOIN soil_health_score sh ON s.soil_sample_id = sh.soil_sample_id
        WHERE UPPER(TRIM(v.name)) = 'BHADRAVATI'
        GROUP BY vname
    """)
    res = cur.fetchone()
    print(f"  Direct DB Aggregation for BHADRAVATI: {res}")
    conn.close()
