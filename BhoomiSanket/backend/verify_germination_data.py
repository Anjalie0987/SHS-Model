import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'soil_sample_germination'")
cols = [r[0] for r in cur.fetchall()]
print(f"Columns in soil_sample_germination: {cols}")

cur.execute("SELECT * FROM soil_sample_germination LIMIT 1")
print(f"Sample data: {cur.fetchone()}")

conn.close()
