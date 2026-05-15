import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

def check_group(primary, duplicates):
    print(f"\n=== Group: {primary} ===")
    for name in [primary] + duplicates:
        try:
            cur.execute(f"SELECT count(*) FROM {name}")
            count = cur.fetchone()[0]
            print(f"Table: {name} | Rows: {count}")
        except:
            print(f"Table: {name} | (Error checking - maybe doesn't exist)")
            conn.rollback()

check_group('farm_crop', ['old_farm_crop'])
check_group('soil_sample', ['old_soil_samples', 'old_soil_sample_new'])
check_group('soil_parameter_master', ['old_soil_parameter_master'])

conn.close()
