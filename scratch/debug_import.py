import pandas as pd
from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

df = pd.read_csv('d:/CROP2/CROP2/shs-backend/app/outputs/germination_output_with_shs_avg_category.csv')
csv_ids = df['Pixel_ID'].unique().tolist()

with engine.connect() as conn:
    print(f"Total Unique Pixel_IDs in CSV: {len(csv_ids)}")
    
    # Check first 50
    subset = csv_ids[:50]
    res = conn.execute(text("SELECT soil_sample_id FROM soil_sample WHERE soil_sample_id IN :ids"), {"ids": tuple(subset)}).fetchall()
    found_ids = [r[0] for r in res]
    print(f"Matches in first 50: {len(found_ids)}")
    print(f"Found IDs: {found_ids}")
    print(f"Missing IDs from first 50: {set(subset) - set(found_ids)}")
