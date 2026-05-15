import json
import psycopg2
import random
import os

# Paths
GEOJSON_PATH = 'BhoomiSanket/frontend/public/data/maharashtra_tehsil.json' # Default common path
if not os.path.exists(GEOJSON_PATH):
    # Fallback to searching
    for root, dirs, files in os.walk('d:/CROP2/CROP2'):
        if 'maharashtra_tehsil.json' in files:
            GEOJSON_PATH = os.path.join(root, 'maharashtra_tehsil.json')
            break

print(f"Using GeoJSON: {GEOJSON_PATH}")

conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    # 1. Get Maharashtra State ID
    cur.execute("SELECT state_code FROM state WHERE name ILIKE '%Maharashtra%' LIMIT 1")
    state_id = cur.fetchone()[0]
    
    # 2. Get a default district ID to link new villages to if we can't find their parent
    cur.execute("SELECT district_code FROM districts WHERE state_code = %s LIMIT 1", (state_id,))
    default_dist_id = cur.fetchone()[0]

    # 3. Read GeoJSON
    with open(GEOJSON_PATH, 'r') as f:
        data = json.load(f)
    
    features = data['features']
    print(f"Found {len(features)} subdistricts in Map.")

    cur.execute("SELECT parameter_id, name FROM soil_parameter_master")
    param_map = {name: pid for pid, name in cur.fetchall()}
    stages = ['Germination', 'Booting', 'Ripening']

    count = 0
    for f in features:
        props = f['properties']
        # Try different possible keys for the subdistrict name
        t_name = (props.get('TEHSIL') or props.get('SUB_DIST') or props.get('TEHSIL_NAM') or props.get('Tehsil') or props.get('dtname') or "Unknown").strip()
        d_name = (props.get('DISTRICT') or props.get('dtname') or "Unknown").strip()
        
        # 4. Find or Create District
        cur.execute("SELECT district_code FROM districts WHERE UPPER(name) = UPPER(%s) AND state_code = %s", (d_name, state_id))
        dist_res = cur.fetchone()
        dist_id = dist_res[0] if dist_res else default_dist_id
        
        # 5. Find or Create Village (Subdistrict)
        cur.execute("SELECT village_id FROM village WHERE UPPER(name) = UPPER(%s) AND district_id = %s", (t_name, dist_id))
        vill_res = cur.fetchone()
        
        if not vill_res:
            cur.execute("INSERT INTO village (name, district_id) VALUES (%s, %s) RETURNING village_id", (t_name, dist_id))
            v_id = cur.fetchone()[0]
        else:
            v_id = vill_res[0]

        # 6. Check if data exists for this village
        cur.execute("SELECT 1 FROM soil_sample WHERE village_id = %s LIMIT 1", (v_id,))
        if not cur.fetchone():
            # Generate data for all 3 stages
            for stage in stages:
                cur.execute("INSERT INTO soil_sample (village_id, stage, sample_date) VALUES (%s, %s, NOW()) RETURNING soil_sample_id", (v_id, stage))
                ss_id = cur.fetchone()[0]
                
                # Parameters
                p_list = [('N', random.uniform(220, 300)), ('P', random.uniform(15, 35)), ('K', random.uniform(120, 250)),
                          ('pH', random.uniform(6.2, 7.8)), ('OC', random.uniform(0.5, 1.0)), 
                          ('Moisture', random.uniform(12, 25)), ('Temp', random.uniform(22, 32))]
                
                for p_name, val in p_list:
                    p_id = param_map.get(p_name)
                    if p_id:
                        cur.execute("INSERT INTO soil_parameter_value (soil_sample_id, parameter_id, value) VALUES (%s, %s, %s)", (ss_id, p_id, val))
                
                # Score
                score = random.uniform(72, 82)
                cat = "Good" if score >= 77.5 else ("Poor" if score <= 74.5 else "Fair")
                cur.execute("INSERT INTO soil_health_score (soil_sample_id, score_value, score_category, created_at) VALUES (%s, %s, %s, NOW())", (ss_id, score, cat))
            
            count += 1
            if count % 50 == 0:
                conn.commit()
                print(f"  Processed {count} new subdistricts from map...")

    conn.commit()
    print(f"COMPLETED! Synchronized {len(features)} map regions with database data.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
