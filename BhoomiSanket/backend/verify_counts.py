import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

cur.execute("SELECT count(*) FROM soil_parameter_value")
print(f"ACTUAL COUNT in soil_parameter_value: {cur.fetchone()[0]}")

cur.execute("SELECT count(*) FROM soil_sample")
print(f"ACTUAL COUNT in soil_sample: {cur.fetchone()[0]}")

cur.execute("SELECT count(*) FROM soil_health_score")
print(f"ACTUAL COUNT in soil_health_score: {cur.fetchone()[0]}")

conn.close()
