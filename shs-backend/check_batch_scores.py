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
            print(f"Checking scores for Batch ID: {batch[0]} (File: {batch[1]})")
            
            # Get avg score and category by district
            result = conn.execute(text(f"SELECT district, AVG(shs_score), MAX(shs_category) FROM uploaded_csv_data WHERE batch_id = {batch[0]} GROUP BY district;"))
            rows = result.fetchall()
            for row in rows:
                print(f"District: {row[0]}, Avg SHS: {row[1]:.2f}, Category: {row[2]}")
    except Exception as e:
        print(f"Error: {e}")
