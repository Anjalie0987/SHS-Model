from sqlalchemy import create_engine, text
import os

DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        result = conn.execute(text("SELECT stage, state, COUNT(*) FROM uploaded_csv_data GROUP BY stage, state;"))
        rows = result.fetchall()
        if not rows:
            print("Table 'uploaded_csv_data' is empty.")
        else:
            print("Data in 'uploaded_csv_data':")
            for row in rows:
                print(f"Stage: {row[0]}, State: {row[1]}, Count: {row[2]}")
    except Exception as e:
        print(f"Error: {e}")
