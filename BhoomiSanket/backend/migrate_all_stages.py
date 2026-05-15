import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Migrating Booting and Ripening data to normalized schema...")
    
    # We select Booting and Ripening stages that haven't been migrated yet
    cur.execute("""
        SELECT village_id, stage, lat, lon, nitrogen, phosphorus, potassium, ph, organic_carbon, moisture, temperature, shs_score, shs_category
        FROM latlon_suitability
        WHERE stage IN ('Booting', 'Ripening') AND village_id IS NOT NULL
        LIMIT 4000 -- Batch size
    """)
    rows = cur.fetchall()
    
    cur.execute("SELECT parameter_id, name FROM soil_parameter_master")
    param_map = {name: pid for pid, name in cur.fetchall()}
    
    count = 0
    for r in rows:
        v_id, stage, lat, lon, n, p, k, ph, oc, moist, temp, score, cat = r
        
        # 1. Insert Sample
        cur.execute("""
            INSERT INTO soil_sample (village_id, stage, geom, sample_date)
            VALUES (%s, %s, ST_SetSRID(ST_Point(%s, %s), 4326), NOW())
            RETURNING soil_sample_id
        """, (v_id, stage, lon, lat))
        ss_id = cur.fetchone()[0]
        
        # 2. Insert Values
        v_list = [(param_map.get('N'), n), (param_map.get('P'), p), (param_map.get('K'), k),
                  (param_map.get('pH'), ph), (param_map.get('OC'), oc), (param_map.get('Moisture'), moist),
                  (param_map.get('Temp'), temp)]
        
        for p_id, val in v_list:
            if p_id and val is not None:
                cur.execute("INSERT INTO soil_parameter_value (soil_sample_id, parameter_id, value) VALUES (%s, %s, %s)", (ss_id, p_id, val))
        
        # 3. Insert Score
        cur.execute("""
            INSERT INTO soil_health_score (soil_sample_id, score_value, score_category, created_at)
            VALUES (%s, %s, %s, NOW())
        """, (ss_id, score, cat))
        
        count += 1

    conn.commit()
    print(f"Success! {count} additional Booting and Ripening points have been normalized.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
