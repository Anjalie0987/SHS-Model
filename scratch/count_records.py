from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("SoilHealthScore count:", conn.execute(text("SELECT count(*) FROM soil_health_score")).scalar())
    print("SoilSample count:", conn.execute(text("SELECT count(*) FROM soil_sample")).scalar())
    print("Village count:", conn.execute(text("SELECT count(*) FROM village")).scalar())
    print("LatLonSuitability count:", conn.execute(text("SELECT count(*) FROM latlon_suitability")).scalar())
