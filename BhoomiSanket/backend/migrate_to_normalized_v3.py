import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Step 0: Updating soil_sample table structure...")
    cur.execute("ALTER TABLE soil_sample ADD COLUMN IF NOT EXISTS village_id INTEGER")
    conn.commit()

    print("Step 1: Migrating 2,000 research points to normalized tables...")
    cur.execute("""
        SELECT village_id, lat, lon, nitrogen, phosphorus, potassium, ph, organic_carbon, moisture, temperature
        FROM latlon_suitability
        WHERE stage = 'Germination' AND village_id IS NOT NULL
        LIMIT 2000
    """)
    rows = cur.fetchall()
    
    cur.execute("SELECT parameter_id, name FROM soil_parameter_master")
    param_map = {name: pid for pid, name in cur.fetchall()}
    
    count = 0
    for r in rows:
        v_id, lat, lon, n, p, k, ph, oc, moist, temp = r
        
        # Insert Sample
        cur.execute("""
            INSERT INTO soil_sample (village_id, stage, geom, sample_date)
            VALUES (%s, 'Germination', ST_SetSRID(ST_Point(%s, %s), 4326), NOW())
            RETURNING soil_sample_id
        """, (v_id, lon, lat))
        ss_id = cur.fetchone()[0]
        
        # Insert Values
        v_list = [(param_map.get('N'), n), (param_map.get('P'), p), (param_map.get('K'), k),
                  (param_map.get('pH'), ph), (param_map.get('OC'), oc), (param_map.get('Moisture'), moist),
                  (param_map.get('Temp'), temp)]
        
        for p_id, val in v_list:
            if p_id and val is not None:
                cur.execute("INSERT INTO soil_parameter_value (soil_sample_id, parameter_id, value) VALUES (%s, %s, %s)", (ss_id, p_id, val))
        count += 1

    conn.commit()
    print(f"Migration Successful! {count} research points are now fully normalized in soil_sample and soil_parameter_value.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
