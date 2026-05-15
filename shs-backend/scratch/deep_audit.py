import os
import sys
import pandas as pd
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import Village, District, SoilSample, SoilHealthScore
from sqlalchemy import text

def deep_audit():
    db = SessionLocal()
    try:
        print("=== DEEP DATA AUDIT ===")
        
        # 1. Check Administrative Foundation
        v_count = db.query(Village).count()
        d_count = db.query(District).count()
        print(f"Total Villages in 'old_village': {v_count}")
        print(f"Total Districts in 'old_district': {d_count}")

        # 2. Check Scientific Core
        sample_count = db.query(SoilSample).count()
        score_count = db.query(SoilHealthScore).count()
        print(f"Total Samples in 'soil_sample': {sample_count}")
        print(f"Total Scores in 'soil_health_score': {score_count}")

        # 3. Check the Join Chain
        print("\n--- LINKAGE CHECK ---")
        
        # Check if Samples are linked to Villages
        samples_with_village = db.query(SoilSample).filter(SoilSample.village_id.isnot(None)).count()
        print(f"Samples with Village ID: {samples_with_village}")

        # Check if Scores are linked to Samples
        scores_with_sample = db.query(SoilHealthScore).filter(SoilHealthScore.soil_sample_id.isnot(None)).count()
        print(f"Scores with Sample ID: {scores_with_sample}")

        # 4. Check the "Full Join" (This is what the map uses)
        full_chain = db.query(
            Village.name, 
            SoilHealthScore.score_value
        ).join(
            SoilSample, Village.village_id == SoilSample.village_id
        ).join(
            SoilHealthScore, SoilSample.soil_sample_id == SoilHealthScore.soil_sample_id
        ).limit(5).all()

        print("\n--- SAMPLE DATA FROM JOIN ---")
        if not full_chain:
            print("FAILURE: The join 'Village -> Sample -> Score' returned ZERO results.")
            
            # Diagnose why
            sample_ids = [s.soil_sample_id for s in db.query(SoilSample).limit(5).all()]
            score_samples = [s.soil_sample_id for s in db.query(SoilHealthScore).limit(5).all()]
            print(f"Sample IDs in 'soil_sample': {sample_ids}")
            print(f"Sample IDs in 'soil_health_score': {score_samples}")
            
            v_ids_in_samples = [s.village_id for s in db.query(SoilSample).limit(5).all()]
            print(f"Village IDs in 'soil_sample': {v_ids_in_samples}")
        else:
            for v_name, score in full_chain:
                print(f"Village '{v_name}' has Score: {score}")

    finally:
        db.close()

if __name__ == "__main__":
    deep_audit()
