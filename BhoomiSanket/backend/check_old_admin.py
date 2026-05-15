import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

def check_table(name):
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{name}'")
    print(f"\n--- {name} ---")
    for r in cur.fetchall():
        print(f"  {r[0]} ({r[1]})")

for t in ['state', 'districts', 'village']:
    check_table(t)

conn.close()
