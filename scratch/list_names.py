from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- Districts ---")
    res = conn.execute(text("SELECT name FROM districts LIMIT 20")).fetchall()
    for r in res: print(r[0])
    
    print("\n--- States ---")
    res = conn.execute(text("SELECT name FROM state LIMIT 20")).fetchall()
    for r in res: print(r[0])
    
    print("\n--- Village Sample ---")
    res = conn.execute(text("SELECT name, district_name, state_name FROM village LIMIT 20")).fetchall()
    for r in res: print(r)
