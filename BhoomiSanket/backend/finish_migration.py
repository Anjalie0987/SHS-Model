import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    # 1. Get current count
    cur.execute("SELECT count(*) FROM soil_parameter_value")
    current_count = cur.fetchone()[0]
    print(f"Current rows in soil_parameter_value: {current_count}")

    # 2. Identify remaining points in latlon_suitability that aren't in soil_sample yet
    # We use geom and stage as unique identifiers
    cur.execute("""
        SELECT l.village_id, l.stage, l.lat, l.lon, l.nitrogen, l.phosphorus, l.potassium, l.ph, l.organic_carbon, l.moisture, l.temperature, l.shs_score, l.shs_category
        FROM latlon_suitability l
        WHERE l.village_id IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM soil_sample s 
            WHERE ST_Equals(s.geom, l.geom) AND s.stage = l.stage
        )
    """)
    remaining_rows = cur.fetchall()
    print(f"Found {len(remaining_rows)} remaining points to migrate...")

    cur.execute("SELECT parameter_id, name FROM soil_parameter_master")
    param_map = {name: pid for pid, name in cur.fetchall()}

    # 3. Migrate the rest
    count = 0
    for r in remaining_rows:
        v_id, stage, lat, lon, n, p, k, ph, oc, moist, temp, score, cat = r
        
        cur.execute("""
            INSERT INTO soil_sample (village_id, stage, geom, sample_date)
            VALUES (%s, %s, ST_SetSRID(ST_Point(%s, %s), 4326), NOW())
            RETURNING soil_sample_id
        """, (v_id, stage, lon, lat))
        ss_id = cur.fetchone()[0]
        
        v_list = [(param_map.get('N'), n), (param_map.get('P'), p), (param_map.get('K'), k),
                  (param_map.get('pH'), ph), (param_map.get('OC'), oc), (param_map.get('Moisture'), moist),
                  (param_map.get('Temp'), temp)]
        
        for p_id, val in v_list:
            if p_id and val is not None:
                cur.execute("INSERT INTO soil_parameter_value (soil_sample_id, parameter_id, value) VALUES (%s, %s, %s)", (ss_id, p_id, val))
        
        cur.execute("INSERT INTO soil_health_score (soil_sample_id, score_value, score_category, created_at) VALUES (%s, %s, %s, NOW())", (ss_id, score, cat))
        count += 1
        
        # Commit every 1000 samples to keep it stable
        if count % 1000 == 0:
            conn.commit()
            print(f"  ... migrated {count} samples")

    conn.commit()
    print(f"Migration finished! Total samples migrated in this run: {count}")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
