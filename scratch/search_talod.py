from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

def search_talod():
    with engine.connect() as conn:
        query = text("""
            SELECT name, district_name, state_name 
            FROM village 
            WHERE name ILIKE '%talod%'
        """)
        res = conn.execute(query)
        for row in res:
            print(row)

if __name__ == "__main__":
    search_talod()
