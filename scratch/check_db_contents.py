from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"

def check_db():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("--- MAHARASHTRA ---")
        res = conn.execute(text("SELECT * FROM state WHERE name ILIKE '%maharashtra%'"))
        for row in res:
            print(row)
        
        print("\n--- STATES ---")
        res = conn.execute(text("SELECT * FROM state LIMIT 5"))
        for row in res:
            print(row)

        print("\n--- VILLAGE SAMPLE ---")
        res = conn.execute(text("SELECT * FROM village LIMIT 5"))
        for row in res:
            print(row)

if __name__ == "__main__":
    check_db()
