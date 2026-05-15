from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("Total Samples:", conn.execute(text("SELECT count(*) FROM soil_sample")).scalar())
    print("Samples with GEOM:", conn.execute(text("SELECT count(*) FROM soil_sample WHERE geom IS NOT NULL")).scalar())
    
    # Check if geom is in Farm table instead
    print("Farms with GEOM:", conn.execute(text("SELECT count(*) FROM farm WHERE geom IS NOT NULL")).scalar())
