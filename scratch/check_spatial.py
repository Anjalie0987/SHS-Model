from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("Villages with GEOM:", conn.execute(text("SELECT count(*) FROM village WHERE geom IS NOT NULL")).scalar())
    
    # Check if there's any other spatial table
    res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%boundary%'")).fetchall()
    print("Boundary tables:", res)
