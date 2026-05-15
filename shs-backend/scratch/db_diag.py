import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd()))

from app.database import SessionLocal
from app.models import Village, SoilSample, SoilHealthScore, LatLonSuitability
from sqlalchemy import func

def diag():
    db = SessionLocal()
    try:
        print("--- DATABASE DIAGNOSTIC ---")
        
        v_count = db.query(func.count(Village.village_id)).scalar()
        print(f"Total Villages/Subdistricts in database: {v_count}")
        
        sample_count = db.query(func.count(SoilSample.soil_sample_id)).scalar()
        print(f"Total Soil Samples: {sample_count}")
        
        shs_count = db.query(func.count(SoilHealthScore.soil_health_score_id)).scalar()
        print(f"Total Soil Health Scores: {shs_count}")
        
        # Check specific join
        print("\n--- JOIN TEST (Subdistrict Aggregation) ---")
        query = db.query(
            Village.name,
            func.count(SoilHealthScore.soil_health_score_id)
        ).join(
            SoilSample, Village.village_id == SoilSample.village_id
        ).join(
            SoilHealthScore, SoilSample.soil_sample_id == SoilHealthScore.soil_sample_id
        ).group_by(Village.name)
        
        results = query.all()
        if not results:
            print("WARNING: No data found using the Village -> SoilSample -> SoilHealthScore join!")
            
            # Check individual tables for content
            print("\nFirst 5 villages:")
            for v in db.query(Village).limit(5).all():
                print(f"- {v.name}")
        else:
            print(f"Found {len(results)} active subdistricts with data:")
            for r in results:
                print(f"- {r[0]}: {r[1]} scores")

    finally:
        db.close()

if __name__ == "__main__":
    diag()
