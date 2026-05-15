import os
import sys
import pandas as pd
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import Village, SoilSample, SoilHealthScore, District
from sqlalchemy import text

def import_hierarchy():
    csv_path = "app/outputs/germination_output_with_shs_avg_category.csv"
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        return

    db = SessionLocal()
    try:
        # 1. Clear existing data in shs/sample tables to avoid duplicates
        print("Clearing old records...")
        db.execute(text("TRUNCATE soil_health_score RESTART IDENTITY CASCADE"))
        db.execute(text("TRUNCATE soil_sample RESTART IDENTITY CASCADE"))
        db.commit()

        print(f"Reading {csv_path}...")
        df = pd.read_csv(csv_path)
        
        # Get unique district scores
        district_scores = df.groupby('District').agg({
            'SHS': 'mean',
            'category': lambda x: x.mode()[0] if not x.mode().empty else 'Fair'
        }).to_dict('index')

        print(f"Found scores for {len(district_scores)} districts.")

        # Get all Maharashtra villages
        all_villages = db.query(Village.village_id, District.name.label("dist_name")).join(
            District, Village.district_id == District.district_id
        ).all()
        
        print(f"Mapping to {len(all_villages)} potential subdistricts...")

        count = 0
        for v_id, dist_name in all_villages:
            if not dist_name: continue
            clean_dist = dist_name.strip().upper()
            
            score_data = None
            for d_key in district_scores:
                if str(d_key).strip().upper() == clean_dist:
                    score_data = district_scores[d_key]
                    break
            
            if score_data:
                sample = SoilSample(
                    village_id=v_id,
                    stage="germination"
                )
                db.add(sample)
                db.flush() 
                
                score = SoilHealthScore(
                    soil_sample_id=sample.soil_sample_id,
                    score_value=float(score_data['SHS']),
                    score_category=score_data['category']
                )
                db.add(score)
                count += 1
                
            if count % 1000 == 0 and count > 0:
                print(f"Imported {count} records...")
                db.commit()

        db.commit()
        print(f"SUCCESS: Imported {count} records into the Hierarchy!")
    except Exception as e:
        print(f"IMPORT FAILED: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_hierarchy()
