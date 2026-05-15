import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Removing foreign key constraints...")
    # Drop constraints that point to the tables we are about to delete
    cur.execute("ALTER TABLE farm DROP CONSTRAINT IF EXISTS farm_village_id_fkey")
    cur.execute("ALTER TABLE farm DROP CONSTRAINT IF EXISTS farm_village_id_fkey1")
    cur.execute("ALTER TABLE district_soil_summary DROP CONSTRAINT IF EXISTS district_soil_summary_district_id_fkey")
    cur.execute("ALTER TABLE district DROP CONSTRAINT IF EXISTS district_state_id_fkey")
    cur.execute("ALTER TABLE village DROP CONSTRAINT IF EXISTS village_district_id_fkey")
    cur.execute("ALTER TABLE state DROP CONSTRAINT IF EXISTS state_country_id_fkey")

    print("Deleting duplicate tables: state, district, village...")
    cur.execute("DROP TABLE IF EXISTS village CASCADE")
    cur.execute("DROP TABLE IF EXISTS district CASCADE")
    cur.execute("DROP TABLE IF EXISTS state CASCADE")

    conn.commit()
    print("Cleanup successful! Duplicate admin tables removed.")
except Exception as e:
    conn.rollback()
    print(f"Error during cleanup: {e}")
finally:
    conn.close()
