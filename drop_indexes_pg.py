import psycopg2

conn = psycopg2.connect("postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db")
conn.autocommit = True
cur = conn.cursor()
indexes = [
    'idx_district_soil_summary_geom',
    'idx_farm_geom',
    'idx_soil_sample_geom',
    'idx_latlon_suitability_geom',
]

for idx in indexes:
    try:
        cur.execute(f"DROP INDEX IF EXISTS {idx} CASCADE;")
        print(f"Dropped {idx}")
    except Exception as e:
        print(f"Failed to drop {idx}: {e}")

cur.close()
conn.close()
