from sqlalchemy import create_engine, text
import os

DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"

def check_columns():
    engine = create_engine(DATABASE_URL)
    tables = ['state', 'districts', 'village', 'village_boundary']
    with engine.connect() as conn:
        for t in tables:
            print(f"\nColumns for {t}:")
            res = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'"))
            for row in res:
                print(f" - {row[0]}")

if __name__ == "__main__":
    check_columns()
