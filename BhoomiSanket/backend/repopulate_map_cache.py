import sys
import os

# Add paths to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from app.database import SessionLocal
from app import models
from app.services.shs_service import SHSService
from sqlalchemy import text

def repopulate_cache():
    db = SessionLocal()
    try:
        # 1. Clear existing cache (optional but recommended for a clean start)
        print("Clearing existing map cache...")
        db.execute(text("TRUNCATE TABLE latlon_suitability"))
        db.commit()

        # 2. Fetch all soil samples that have scores
        print("Fetching soil samples with scores...")
        samples = db.query(models.SoilSample.soil_sample_id).all()
        
        total = len(samples)
        print(f"Found {total} samples to process.")

        # 3. Process each sample
        # Note: This might take a few minutes if there are 30k samples
        # For a demo, we can process a subset or just run it all
        count = 0
        for s in samples:
            SHSService.process_soil_sample(s.soil_sample_id)
            count += 1
            if count % 100 == 0:
                print(f"Processed {count}/{total} samples...")
        
        print(f"Successfully repopulated cache with {count} samples.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    repopulate_cache()
