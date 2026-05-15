from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("Min ID:", conn.execute(text("SELECT min(soil_sample_id) FROM soil_sample")).scalar())
    print("Max ID:", conn.execute(text("SELECT max(soil_sample_id) FROM soil_sample")).scalar())
    
    # Check if there's any mismatch in types
    res = conn.execute(text("SELECT soil_sample_id FROM soil_sample LIMIT 5")).fetchall()
    print("Sample IDs from DB:", [r[0] for r in res])
