from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        # Truncate the table to give the user a fresh start
        conn.execute(text("TRUNCATE TABLE uploaded_csv_data CASCADE;"))
        conn.commit()
        print("Truncated table 'uploaded_csv_data'. Ready for fresh upload.")
    except Exception as e:
        print(f"Error: {e}")
