from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

def check_districts():
    with engine.connect() as conn:
        query = text("""
            SELECT state_code, district_code, name 
            FROM districts 
            WHERE name ILIKE '%vadodara%'
        """)
        res = conn.execute(query)
        for row in res:
            print(row)

if __name__ == "__main__":
    check_districts()
