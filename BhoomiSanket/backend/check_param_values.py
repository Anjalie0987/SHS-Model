import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

cur.execute("SELECT count(*) FROM soil_parameter_value")
print(f"Total rows in soil_parameter_value: {cur.fetchone()[0]}")

cur.execute("SELECT sp.name, count(*) FROM soil_parameter_value sv JOIN soil_parameter_master sp ON sv.parameter_id = sp.parameter_id GROUP BY sp.name")
print("Data breakdown by parameter:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} entries")

conn.close()
