import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Deep Cleaning Village Names in Database...")
    # Update all village names to be UPPERCASE and TRIMMED
    cur.execute("UPDATE old_village SET name = UPPER(TRIM(name))")
    print(f"  Cleaned {cur.rowcount} village names.")
    
    # Let's check 'BHADRAVATI' specifically
    cur.execute("SELECT village_id, name FROM old_village WHERE name = 'BHADRAVATI'")
    res = cur.fetchall()
    print(f"  Bhadravati search result: {res}")
    
    if res:
        v_id = res[0][0]
        cur.execute("SELECT count(*) FROM soil_sample WHERE village_id = %s", (v_id,))
        sample_count = cur.fetchone()[0]
        print(f"  Samples for Bhadravati: {sample_count}")

    conn.commit()
    print("Success! Database names are now standardized.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
