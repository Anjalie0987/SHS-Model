import os
import sys
from sqlalchemy import text
from sqlalchemy import create_engine

def enable_postgis(db_url):
    print(f"Connecting to {db_url}")
    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            print("PostGIS enabled successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    db_url_1 = "postgresql://postgres:post123@127.0.0.1:5432/bhoomisanket_db"
    db_url_2 = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
    
    print("Trying 5432...")
    enable_postgis(db_url_1)
    
    print("Trying 5433...")
    enable_postgis(db_url_2)
