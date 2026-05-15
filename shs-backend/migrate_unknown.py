from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        # Update Unknown states to Maharashtra
        result = conn.execute(text("UPDATE uploaded_csv_data SET state = 'Maharashtra' WHERE state = 'Unknown';"))
        conn.commit()
        print(f"Updated {result.rowcount} records from 'Unknown' to 'Maharashtra'.")
    except Exception as e:
        print(f"Error: {e}")
