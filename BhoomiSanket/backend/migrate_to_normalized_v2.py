import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Step 0: Adding village_id column to latlon_suitability...")
    cur.execute("ALTER TABLE latlon_suitability ADD COLUMN IF NOT EXISTS village_id INTEGER")
    conn.commit()

    print("Step 1: Updating village_id in latlon_suitability from old_village...")
    cur.execute("""
        UPDATE latlon_suitability l
        SET village_id = v.village_id
        FROM old_village v
        WHERE UPPER(l.village_name) = UPPER(v.name)
        AND l.village_id IS NULL
    """)
    conn.commit()
    print(f"  Linked {cur.rowcount} records to villages.")

    print("Step 2: Migrating data to normalized tables...")
    cur.execute("""
        SELECT id, village_id, lat, lon, nitrogen, phosphorus, potassium, ph, organic_carbon, moisture, temperature, shs_score, shs_category
        FROM latlon_suitability
        WHERE stage = 'Germination' AND village_id IS NOT NULL
        LIMIT 2000 -- Processing in smaller batches to avoid timeout
    """)
    rows = cur.fetchall()
    
    cur.execute("SELECT parameter_id, name FROM soil_parameter_master")
    param_map = {name: pid for pid, name in cur.fetchall()}
    
    count = 0
    for r in rows:
        ls_id, v_id, lat, lon, n, p, k, ph, oc, moist, temp, score, cat = r
        
        cur.execute("""
            INSERT INTO soil_sample (farm_id, village_id, stage, geom, sample_date)
            VALUES (NULL, %s, 'Germination', ST_SetSRID(ST_Point(%s, %s), 4326), NOW())
            RETURNING soil_sample_id
        """, (v_id, lon, lat))
        ss_id = cur.fetchone()[0]
        
        values_to_insert = [
            (param_map.get('N'), n), (param_map.get('P'), p), (param_map.get('K'), k),
            (param_map.get('pH'), ph), (param_map.get('OC'), oc), (param_map.get('Moisture'), moist),
            (param_map.get('Temp'), temp)
        ]
        
        for p_id, val in values_to_insert:
            if p_id and val is not None:
                cur.execute("INSERT INTO soil_parameter_value (soil_sample_id, parameter_id, value) VALUES (%s, %s, %s)", (ss_id, p_id, val))
        count += 1

    conn.commit()
    print(f"Migration Complete! {count} samples migrated to normalized schema.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
