from sqlalchemy import create_engine, func, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys

# DATABASE CONFIG
DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
Base = declarative_base()

# REDEFINE MODELS IN SCRIPT TO BE 100% SURE
class Village(Base):
    __tablename__ = 'old_village'
    village_id = Column(Integer, primary_key=True)
    name = Column(String)

class SoilSample(Base):
    __tablename__ = 'soil_sample'
    soil_sample_id = Column(Integer, primary_key=True)
    village_id = Column(Integer, ForeignKey('old_village.village_id'))
    stage = Column(String)

class SoilHealthScore(Base):
    __tablename__ = 'soil_health_score'
    soil_health_score_id = Column(Integer, primary_key=True)
    soil_sample_id = Column(Integer, ForeignKey('soil_sample.soil_sample_id'))
    score_value = Column(Float)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    print(f"Testing direct SQLAlchemy models...")
    v_count = db.query(Village).count()
    print(f"  Villages: {v_count}")
    s_count = db.query(SoilSample).count()
    print(f"  Samples: {s_count}")
    
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
    
    print(f"  SUCCESS! Aggregation found {len(results)} rows.")
    if results:
        print(f"  First result: {results[0]}")

except Exception as e:
    print(f"  ERROR: {e}")
finally:
    db.close()
