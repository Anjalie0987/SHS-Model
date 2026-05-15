import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Master Name Repair: Fixing corrupted characters...")
    
    # 1. Fix common corruptions in village names
    replacements = [
        ('<', 'A'), ('>', 'A'), ('|', 'I'), ('\\', 'I'), ('@', 'U'), ('#', 'U')
    ]
    
    for old, new in replacements:
        cur.execute(f"UPDATE old_village SET name = REPLACE(name, '{old}', '{new}')")
        print(f"  Fixed {cur.rowcount} instances of '{old}' -> '{new}' in villages.")
        
        cur.execute(f"UPDATE old_district SET name = REPLACE(name, '{old}', '{new}')")
        print(f"  Fixed {cur.rowcount} instances of '{old}' -> '{new}' in districts.")

    # 2. Trim and Uppercase again
    cur.execute("UPDATE old_village SET name = UPPER(TRIM(name))")
    cur.execute("UPDATE old_district SET name = UPPER(TRIM(name))")

    # 3. Final verification for Bhadravati and Nanded
    cur.execute("SELECT name FROM old_village WHERE name LIKE '%NANDED%' OR name LIKE '%BHADRAVATI%' LIMIT 5")
    print(f"  Verification Result: {cur.fetchall()}")

    conn.commit()
    print("SUCCESS! All names have been repaired and standardized.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
