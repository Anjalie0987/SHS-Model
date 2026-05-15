import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Renaming old_soil_sample_new to soil_sample_germination...")
    cur.execute("ALTER TABLE old_soil_sample_new RENAME TO soil_sample_germination")
    
    print("Deleting unused duplicate tables...")
    cur.execute("DROP TABLE IF EXISTS old_farm_crop CASCADE")
    cur.execute("DROP TABLE IF EXISTS old_soil_samples CASCADE")
    cur.execute("DROP TABLE IF EXISTS old_soil_parameter_master CASCADE")
    
    conn.commit()
    print("All changes applied successfully!")
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
