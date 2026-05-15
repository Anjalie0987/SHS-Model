from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    for table in ['state', 'districts', 'village']:
        print(f"\nSample from {table}:")
        try:
            res = conn.execute(text(f"SELECT * FROM {table} LIMIT 1")).fetchone()
            print(res)
        except Exception as e:
            print(f"Error: {e}")
