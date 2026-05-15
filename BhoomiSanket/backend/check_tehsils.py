import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()
cur.execute("SELECT v.name FROM village v JOIN district d ON v.district_id = d.district_id JOIN state s ON d.state_id = s.state_id WHERE s.name = 'Maharashtra' LIMIT 20")
print("Sample Tehsils in Village Table:")
for r in cur.fetchall():
    print(f"  {r[0]}")
