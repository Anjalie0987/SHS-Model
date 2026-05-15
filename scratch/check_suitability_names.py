from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- LatLonSuitability Names ---")
    res = conn.execute(text("SELECT district_name, state_name FROM latlon_suitability LIMIT 20")).fetchall()
    for r in res: print(r)
