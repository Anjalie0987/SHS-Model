import os
import sys
import pandas as pd
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import Village, SoilSample, SoilHealthScore

def import_csv_to_db():
    csv_path = "app/outputs/germination_output_with_shs_avg_category.csv"
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        return

    print(f"Reading {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Found {len(df)} records.")

    db = SessionLocal()
    try:
        # Create a cache of villages for fast lookup
        villages = {v.name.strip().upper(): v.village_id for v in db.query(Village).all()}
        
        scores_to_add = []
        for index, row in df.iterrows():
            dist_name = str(row['District']).strip().upper()
            
            # Since we don't have subdistrict in CSV, we map to the first village in that district for demo
            # OR better: find if 'District' itself exists in Village table
            v_id = villages.get(dist_name)
            
            if v_id:
                # Create a sample and score record
                # (Normally we'd check if it exists, but here we just want to show data)
                score = SoilHealthScore(
                    score_value=float(row['SHS']),
                    score_category=row['category'],
                    # We'll link to a dummy sample ID or create one
                )
                # For the map to work with my strict join, I need Village -> Sample -> Score
                sample = SoilSample(
                    village_id=v_id,
                    stage="germination"
                )
                db.add(sample)
                db.flush() # Get sample_id
                
                score.soil_sample_id = sample.soil_sample_id
                db.add(score)
                
            if index % 500 == 0:
                print(f"Processed {index} records...")
                db.commit()

        db.commit()
        print("IMPORT SUCCESSFUL!")
    except Exception as e:
        print(f"IMPORT FAILED: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_to_db()
