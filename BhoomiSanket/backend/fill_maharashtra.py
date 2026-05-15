import psycopg2
import random
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Step 1: Finding Maharashtra State ID...")
    cur.execute("SELECT state_code FROM state WHERE name ILIKE '%Maharashtra%' LIMIT 1")
    res = cur.fetchone()
    if not res:
        print("Error: Maharashtra not found in state table.")
        exit()
    state_id = res[0]
    print(f"  Maharashtra State ID: {state_id}")

    print("Step 2: Identifying empty subdistricts in Maharashtra...")
    cur.execute("""
        SELECT v.village_id, v.name 
        FROM village v
        JOIN districts d ON v.district_id = d.district_code
        WHERE d.state_code = %s
        AND NOT EXISTS (SELECT 1 FROM soil_sample s WHERE s.village_id = v.village_id)
    """, (state_id,))
    empty_villages = cur.fetchall()
    print(f"  Found {len(empty_villages)} empty subdistricts.")

    cur.execute("SELECT parameter_id, name FROM soil_parameter_master")
    param_map = {name: pid for pid, name in cur.fetchall()}

    print("Step 3: Generating synthetic data...")
    count = 0
    stages = ['Germination', 'Booting', 'Ripening']
    
    for v_id, v_name in empty_villages:
        # Generate data for all 3 stages for each subdistrict
        for stage in stages:
            # 1. Insert Sample
            cur.execute("""
                INSERT INTO soil_sample (village_id, stage, sample_date)
                VALUES (%s, %s, NOW())
                RETURNING soil_sample_id
            """, (v_id, stage))
            ss_id = cur.fetchone()[0]
            
            # 2. Generate Realistic Parameter Values
            # N: 200-350, P: 10-40, K: 150-400, pH: 6.0-8.0, OC: 0.4-1.2, Moist: 10-30, Temp: 20-35
            n_val = random.uniform(200, 350)
            p_val = random.uniform(10, 40)
            k_val = random.uniform(150, 400)
            ph_val = random.uniform(6.0, 8.0)
            oc_val = random.uniform(0.4, 1.2)
            moist_val = random.uniform(10, 30)
            temp_val = random.uniform(20, 35)
            
            p_list = [('N', n_val), ('P', p_val), ('K', k_val), ('pH', ph_val), 
                      ('OC', oc_val), ('Moisture', moist_val), ('Temp', temp_val)]
            
            for p_name, val in p_list:
                p_id = param_map.get(p_name)
                if p_id:
                    cur.execute("INSERT INTO soil_parameter_value (soil_sample_id, parameter_id, value) VALUES (%s, %s, %s)", (ss_id, p_id, val))
            
            # 3. Generate a Random Score (70 - 85 to show different colors)
            score = random.uniform(70, 85)
            cat = "Good" if score >= 77.5 else ("Poor" if score <= 74.5 else "Fair")
            
            cur.execute("""
                INSERT INTO soil_health_score (soil_sample_id, score_value, score_category, created_at)
                VALUES (%s, %s, %s, NOW())
            """, (ss_id, score, cat))
            
        count += 1
        if count % 100 == 0:
            conn.commit()
            print(f"  Processed {count} subdistricts...")

    conn.commit()
    print(f"Success! Generated data for {count} subdistricts across all 3 growth stages.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
