from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    try:
        # Get the most recent batch
        batch_id_query = conn.execute(text("SELECT id, filename FROM upload_batch ORDER BY created_at DESC LIMIT 1;"))
        batch = batch_id_query.fetchone()
        if not batch:
            print("No upload batches found.")
        else:
            print(f"Checking data for Batch ID: {batch[0]} (File: {batch[1]})")
            
            # Count records by district
            result = conn.execute(text(f"SELECT district, COUNT(*) FROM uploaded_csv_data WHERE batch_id = {batch[0]} GROUP BY district;"))
            rows = result.fetchall()
            print(f"Found {len(rows)} distinct districts in this batch.")
            for row in rows:
                print(f"District: '{row[0]}', Count: {row[1]}")
    except Exception as e:
        print(f"Error: {e}")
