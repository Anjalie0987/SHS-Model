import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

def analyze_table(name):
    cur.execute(f"SELECT count(*) FROM {name}")
    count = cur.fetchone()[0]
    
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{name}'")
    cols = cur.fetchall()
    
    cur.execute(f"SELECT * FROM {name} LIMIT 5")
    samples = cur.fetchall()
    
    print(f"\n--- Analysis of {name} ---")
    print(f"Total Rows: {count}")
    print("Columns:")
    for c in cols:
        print(f"  {c[0]} ({c[1]})")
    print("Sample Rows:")
    for s in samples:
        print(f"  {s}")

analyze_table('farm')
analyze_table('old_farm')

conn.close()
