import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()
cur.execute("DROP TABLE IF EXISTS old_farm CASCADE")
conn.commit()
print("Table old_farm dropped successfully.")
conn.close()
