import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()
cur.execute("SELECT count(DISTINCT v.village_id) FROM village v JOIN district d ON v.district_id = d.district_id JOIN state s ON d.state_id = s.state_id WHERE s.name = 'Maharashtra'")
print(f"Total Tehsils in Maharashtra: {cur.fetchone()[0]}")
cur.execute("SELECT count(DISTINCT l.village_name) FROM latlon_suitability l WHERE l.state_name = 'Maharashtra' AND l.village_name IS NOT NULL")
print(f"Tehsils in MH with data: {cur.fetchone()[0]}")
cur.execute("SELECT district_name, count(DISTINCT village_name) FROM latlon_suitability WHERE state_name = 'Maharashtra' GROUP BY district_name")
print("Data per District:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} tehsils with data")
