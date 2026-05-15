import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()
cur.execute("SELECT conname, confrelid::regclass FROM pg_constraint WHERE conrelid = 'farm'::regclass AND contype = 'f'")
print("Foreign Keys on farm:")
for r in cur.fetchall():
    print(f"  {r[0]} -> {r[1]}")
conn.close()
