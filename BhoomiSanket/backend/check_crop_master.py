import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'crop_master'")
print("Columns in crop_master:")
for r in cur.fetchall():
    print(f"  {r[0]} ({r[1]})")
conn.close()
