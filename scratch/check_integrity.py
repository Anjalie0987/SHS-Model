from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- Sample vs Farm Check ---")
    res = conn.execute(text("SELECT count(*) FROM soil_sample WHERE farm_id IS NOT NULL")).scalar()
    print(f"Soil Samples with farm_id: {res}")
    
    res = conn.execute(text("SELECT count(*) FROM soil_sample s LEFT JOIN farm f ON s.farm_id = f.farm_id WHERE f.farm_id IS NULL AND s.farm_id IS NOT NULL")).scalar()
    print(f"Soil Samples with NON-EXISTENT farm_id: {res}")
    
    res = conn.execute(text("SELECT count(*) FROM farm")).scalar()
    print(f"Total Farms: {res}")
    
    print("\n--- Sample vs Village Check ---")
    res = conn.execute(text("SELECT count(*) FROM soil_sample WHERE village_id IS NOT NULL")).scalar()
    print(f"Soil Samples with village_id: {res}")
    
    res = conn.execute(text("SELECT count(*) FROM soil_sample s JOIN village v ON s.village_id = v.village_id")).scalar()
    print(f"Soil Samples with VALID village_id: {res}")
