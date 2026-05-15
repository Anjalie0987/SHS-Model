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
            print(f"Checking records for Batch ID: {batch[0]} (File: {batch[1]})")
            
            # Get first 5 records with all parameters
            result = conn.execute(text(f"SELECT nitrogen, phosphorus, potassium, moisture, ph, organic_carbon, temperature, ndvi, shs_score FROM uploaded_csv_data WHERE batch_id = {batch[0]} LIMIT 5;"))
            rows = result.fetchall()
            for row in rows:
                print(f"N: {row[0]}, P: {row[1]}, K: {row[2]}, M: {row[3]}, pH: {row[4]}, OC: {row[5]}, T: {row[6]}, NDVI: {row[7]}, SHS: {row[8]}")
    except Exception as e:
        print(f"Error: {e}")
