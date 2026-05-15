import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

# Define the broken character mapping
# < -> A, > -> A, @ -> U, | -> E, { -> I
# These are common in some old GIS shapefile encodings
replacements = [
    ("<", "A"),
    (">", "A"),
    ("@", "U"),
    ("|", "I"),
    ("{", "E"),
    ("(", ""),
    (")", "")
]

print("--- Cleaning Village Names in latlon_suitability ---")
for char, replacement in replacements:
    query = f"UPDATE latlon_suitability SET village_name = REPLACE(village_name, '{char}', '{replacement}') WHERE village_name LIKE '%{char}%'"
    cur.execute(query)
    print(f"  Fixed character: {char} -> {replacement}")

# Remove double As if any were created (e.g. AMAR>VATI -> AMARAVATI -> AMRAVATI)
# Note: Usually just clean up.
cur.execute("UPDATE latlon_suitability SET village_name = UPPER(TRIM(village_name))")

# One specific fix for common MH districts
cur.execute("UPDATE latlon_suitability SET village_name = 'AMRAVATI' WHERE village_name = 'AMARAVATI'")

conn.commit()
print("--- Cleaning Complete! ---")

cur.execute("SELECT village_name, count(*) FROM latlon_suitability WHERE state_name = 'Maharashtra' GROUP BY village_name LIMIT 10")
print("New Sample Names:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} rows")

conn.close()
