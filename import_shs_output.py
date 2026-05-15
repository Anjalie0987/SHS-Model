import pandas as pd
from sqlalchemy import create_engine, text
import os

# Database Configuration
DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

# File paths for your output files
GERMINATION_CSV = "d:/CROP2/CROP2/shs-backend/app/outputs/germination_output_with_shs_avg_category.csv"
BOOTING_CSV = "d:/CROP2/CROP2/shs-backend/app/outputs/booting_output_with_shs_avg_category.csv"
RIPENING_CSV = "d:/CROP2/CROP2/shs-backend/app/outputs/ripening_output_with_shs_avg_category.csv"

def import_stage_data(csv_path, stage_name):
    print(f"\n--- Processing Stage: {stage_name} ---")
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    total_rows = len(df)
    print(f"Found {total_rows} rows.")

    with engine.connect() as conn:
        # 1. Clear existing cache for this stage to avoid duplicates
        print(f"Cleaning existing cache for {stage_name}...")
        conn.execute(text("DELETE FROM latlon_suitability WHERE stage = :stage"), {"stage": stage_name})
        conn.execute(text("DELETE FROM soil_health_score WHERE score_category = :stage"), {"stage": stage_name})
        
        # 2. Batch Import to latlon_suitability (Fast)
        print(f"Importing data into latlon_suitability for {stage_name}...")
        
        # We need coordinates from soil_sample table
        # We join the CSV data with soil_sample in SQL to be efficient
        # First, we'll create a temporary table for the CSV data
        conn.execute(text("DROP TABLE IF EXISTS temp_import"))
        df.to_sql('temp_import', engine, if_exists='replace', index=False)
        
        # Now perform a bulk insert with joins
        # We handle name normalization here too
        insert_query = text(f"""
            INSERT INTO latlon_suitability (
                soil_sample_id, stage, state_name, district_name, village_name,
                lat, lon, nitrogen, phosphorus, potassium, moisture, ph,
                organic_carbon, temperature, shs_score, shs_category, created_at, geom
            )
            SELECT 
                t."Pixel_ID", 
                :stage,
                t."State",
                t."District",
                'Unknown', -- Village name not in this specific CSV, can be updated later if needed
                ST_Y(s.geom),
                ST_X(s.geom),
                t."N", t."P", t."K", t."Moisture", t."pH", t."OC", t."Temp",
                t."SHS", t."category", NOW(), s.geom
            FROM temp_import t
            JOIN soil_sample s ON t."Pixel_ID" = s.soil_sample_id
        """)
        
        res = conn.execute(insert_query, {"stage": stage_name})
        print(f"Successfully cached {res.rowcount} records into latlon_suitability.")

        # 3. Also update soil_health_score for subdistrict mapping
        print(f"Updating soil_health_score for {stage_name}...")
        shs_query = text(f"""
            INSERT INTO soil_health_score (soil_sample_id, score_value, score_category, created_at)
            SELECT "Pixel_ID", "SHS", :stage, NOW() FROM temp_import
        """)
        res = conn.execute(shs_query, {"stage": stage_name})
        print(f"Successfully updated {res.rowcount} records in soil_health_score.")

        conn.execute(text("DROP TABLE IF EXISTS temp_import"))
        conn.commit()

if __name__ == "__main__":
    print("Starting Optimized Import Process from CSVs...")
    
    import_stage_data(GERMINATION_CSV, "Germination")
    import_stage_data(BOOTING_CSV, "Booting")
    import_stage_data(RIPENING_CSV, "Ripening")
    
    print("\nAll imports completed. Your map is now ready!")
