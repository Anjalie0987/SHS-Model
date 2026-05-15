from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import sys
import os

# Manually add path to app
sys.path.append('d:/CROP2/CROP2/shs-backend')

from app.models import Village, SoilSample, SoilHealthScore
from app.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print(f"Testing SQLAlchemy with URL: {DATABASE_URL}")
    
    # 1. Check counts of each table
    print(f"  Villages in DB: {db.query(Village).count()}")
    print(f"  Samples in DB: {db.query(SoilSample).count()}")
    print(f"  Scores in DB: {db.query(SoilHealthScore).count()}")
    
    # 2. Test the specific join
    stage = 'Germination'
    results = db.query(
        Village.name.label("village_name"),
        func.avg(SoilHealthScore.score_value).label("avg_shs")
    ).join(
        SoilSample, Village.village_id == SoilSample.village_id
    ).join(
        SoilHealthScore, SoilSample.soil_sample_id == SoilHealthScore.soil_sample_id
    ).filter(
        SoilSample.stage.ilike(stage)
    ).group_by(
        Village.name
    ).all()
    
    print(f"  Join Results found: {len(results)}")
    if results:
        print(f"  Sample Result: {results[0]}")

except Exception as e:
    print(f"  ERROR: {e}")
finally:
    db.close()
