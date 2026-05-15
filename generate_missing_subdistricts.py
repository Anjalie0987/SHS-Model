import random
from sqlalchemy import create_engine, text

# Update this path if your database credentials are different
DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

def get_category(score):
    if score > 78:
        return "Excellent"
    elif score >= 77:
        return "Very Good"
    elif score >= 76:
        return "Good"
    elif score >= 75:
        return "Moderate"
    elif score >= 74:
        return "Poor"
    else:
        return "Very Poor"

def generate_missing_data():
    print("Connecting to database...")
    with engine.connect() as conn:
        # Get all village IDs
        print("Fetching all villages...")
        all_villages = conn.execute(text("SELECT village_id, district_id FROM old_village")).fetchall()
        
        # Get villages that already have samples
        print("Fetching existing samples...")
        existing_villages = conn.execute(text("SELECT DISTINCT village_id FROM soil_sample WHERE village_id IS NOT NULL")).fetchall()
        existing_set = set([v[0] for v in existing_villages])
        
        # Determine which villages need data
        missing_villages = [v for v in all_villages if v[0] not in existing_set]
        print(f"Found {len(missing_villages)} villages that need data generated.")
        
        if not missing_villages:
            print("All villages already have data!")
            return

        print("Generating data... This might take a minute.")
        
        try:
            samples_to_insert = []
            scores_to_insert = []
            
            # To avoid conflict with existing IDs, let the database auto-increment soil_sample_id
            # However, we need the inserted IDs to link the scores.
            # Using RETURNING is efficient, but doing it in a batch is tricky.
            # We will use raw SQL and let the sequence handle the ID, using currval or just fetching the new IDs.
            # Even better: Get the max ID and assign manually.
            max_sample_id = conn.execute(text("SELECT COALESCE(MAX(soil_sample_id), 0) FROM soil_sample")).scalar()
            current_id = max_sample_id + 1
            
            stages = ["Germination", "Booting", "Ripening"]
            
            count = 0
            for village in missing_villages:
                v_id = village[0]
                
                for stage in stages:
                    # Generate random score between 65 and 85 to match typical range
                    # We skew it slightly towards 74-78 so we get a good mix of colors
                    base_score = random.gauss(76, 2.5) 
                    base_score = max(60, min(95, base_score)) # Clamp between 60 and 95
                    
                    score_value = round(base_score, 2)
                    category = get_category(score_value)
                    
                    samples_to_insert.append({
                        "id": current_id,
                        "v_id": v_id,
                        "stage": stage
                    })
                    
                    scores_to_insert.append({
                        "sample_id": current_id,
                        "score": score_value,
                        "cat": category
                    })
                    
                    current_id += 1
                
                count += 1
                if count % 1000 == 0:
                    print(f"Prepared data for {count} villages...")

            print("Inserting soil samples...")
            conn.execute(
                text("INSERT INTO soil_sample (soil_sample_id, village_id, stage) VALUES (:id, :v_id, :stage)"),
                samples_to_insert
            )
            
            print("Inserting soil health scores...")
            conn.execute(
                text("INSERT INTO soil_health_score (soil_sample_id, score_value, score_category) VALUES (:sample_id, :score, :cat)"),
                scores_to_insert
            )
            
            # Update sequence just in case
            conn.execute(text("SELECT setval(pg_get_serial_sequence('soil_sample', 'soil_sample_id'), (SELECT MAX(soil_sample_id) FROM soil_sample))"))
            
            conn.commit()
            print(f"Successfully generated and inserted data for {len(missing_villages)} subdistricts!")
            
        except Exception as e:
            conn.rollback()
            print("An error occurred. Transaction rolled back.")
            print(e)

if __name__ == "__main__":
    generate_missing_data()
