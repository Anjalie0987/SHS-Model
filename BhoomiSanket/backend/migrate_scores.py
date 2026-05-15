import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

try:
    print("Step 1: Migrating SHS Scores to the normalized 'soil_health_score' table...")
    # First, we need to make sure our soil_sample records have their scores in the right table
    # Link: latlon_suitability -> soil_sample (via geom/stage) -> soil_health_score
    
    cur.execute("""
        INSERT INTO soil_health_score (farm_id, score_value, score_category, created_at)
        SELECT s.farm_id, l.shs_score, l.shs_category, s.sample_date
        FROM soil_sample s
        JOIN latlon_suitability l ON ST_Equals(s.geom, l.geom) AND s.stage = l.stage
        WHERE NOT EXISTS (SELECT 1 FROM soil_health_score sh WHERE sh.created_at = s.sample_date)
    """)
    print(f"  Migrated {cur.rowcount} scores to the 'soil_health_score' table.")
    
    conn.commit()
    print("Scores are now stored in the normalized schema.")

except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    conn.close()
