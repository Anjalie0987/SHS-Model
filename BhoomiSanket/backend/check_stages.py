import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

cur.execute("SELECT stage, count(*) FROM soil_sample GROUP BY stage")
res = cur.fetchall()
for r in res:
    print(f"STAGE: |{r[0]}| COUNT: {r[1]}")

conn.close()
