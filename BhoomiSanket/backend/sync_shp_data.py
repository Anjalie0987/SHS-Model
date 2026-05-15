import geopandas as gpd
import psycopg2
import random
import os

# Paths to the shapefile
BASE_DIR = 'd:/CROP2/CROP2/BhoomiSanket/backend'
SHAPEFILE_DIR = os.path.join(BASE_DIR, "data", "shapefiles")
SUBDISTRICT_SHP = os.path.join(SHAPEFILE_DIR, "subdistrict", "SUBDISTRICT_BOUNDARY_WGS84.shp")

conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Step 1: Reading Shapefile...")
    gdf = gpd.read_file(SUBDISTRICT_SHP)
    
    # Try to identify State and Subdistrict columns
    state_col = None
    for c in ['STATE', 'ST_NM', 'State_Name', 'StateName', 'stname']:
        if c in gdf.columns:
            state_col = c
            break
            
    subdist_col = None
    for c in ['TEHSIL', 'TEHSIL_NAM', 'SUB_DIST', 'SubDistrict', 'Tehsil', 'sdtname']:
        if c in gdf.columns:
            subdist_col = c
            break

    dist_col = None
    for c in ['DISTRICT', 'DIST_NAME', 'District', 'dtname']:
        if c in gdf.columns:
            dist_col = c
            break

    if not state_col or not subdist_col:
        print(f"Error: Could not find location columns. Available: {gdf.columns}")
        exit()

    print(f"  Filtering subdistricts for Maharashtra (Column: {state_col})...")
    # Filter for Maharashtra (Shapefile uses Title Case usually)
    maharashtra_gdf = gdf[gdf[state_col].astype(str).str.contains('Maharashtra', case=False)]
    print(f"  Found {len(maharashtra_gdf)} subdistricts in Maharashtra.")

    # 2. Get Maharashtra State ID
    cur.execute("SELECT state_code FROM state WHERE name ILIKE '%Maharashtra%' LIMIT 1")
    state_id = cur.fetchone()[0]
    
    cur.execute("SELECT parameter_id, name FROM soil_parameter_master")
    param_map = {name: pid for pid, name in cur.fetchall()}
    stages = ['Germination', 'Booting', 'Ripening']

    print("Step 2: Syncing with Database and generating data...")
    count = 0
    for index, row in maharashtra_gdf.iterrows():
        t_name = str(row[subdist_col]).strip()
        d_name = str(row[dist_col]).strip() if dist_col else "Unknown"
        
        # A. Find or Create District
        cur.execute("SELECT district_code FROM districts WHERE UPPER(name) = UPPER(%s) AND state_code = %s", (d_name, state_id))
        dist_res = cur.fetchone()
        if not dist_res:
            # Note: Assuming district_code might need manual assignment or is serial. 
            # If it's not serial, this might fail without a code.
            cur.execute("INSERT INTO districts (name, state_code) VALUES (%s, %s) RETURNING district_code", (d_name, state_id))
            dist_id = cur.fetchone()[0]
        else:
            dist_id = dist_res[0]
            
        # B. Find or Create Village (Subdistrict)
        cur.execute("SELECT village_id FROM village WHERE UPPER(name) = UPPER(%s) AND district_id = %s", (t_name, dist_id))
        vill_res = cur.fetchone()
        if not vill_res:
            cur.execute("INSERT INTO village (name, district_id) VALUES (%s, %s) RETURNING village_id", (t_name, dist_id))
            v_id = cur.fetchone()[0]
        else:
            v_id = vill_res[0]

        # C. Generate Data if missing
        cur.execute("SELECT 1 FROM soil_sample WHERE village_id = %s LIMIT 1", (v_id,))
        if not cur.fetchone():
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
                
                # Score (72-82 range)
                score = random.uniform(72, 82)
                cat = "Good" if score >= 77.5 else ("Poor" if score <= 74.5 else "Fair")
                cur.execute("INSERT INTO soil_health_score (soil_sample_id, score_value, score_category, created_at) VALUES (%s, %s, %s, NOW())", (ss_id, score, cat))
            
            count += 1
            if count % 50 == 0:
                conn.commit()
                print(f"  Processed {count} new subdistricts...")

    conn.commit()
    print(f"SUCCESS! {len(maharashtra_gdf)} subdistricts are now synced and colored.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
