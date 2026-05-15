import json
import pandas as pd
from sqlalchemy import create_engine, text

# DB Connection
DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

def scan_coverage():
    # 1. Get all names from DB
    with engine.connect() as conn:
        db_names = pd.read_sql("SELECT DISTINCT name FROM old_village", conn)['name'].tolist()
    
    db_clean = {n.strip().upper().replace('[^A-Z0-9]', ''): n for n in db_names}
    
    # 2. Get all names from GeoJSON (Subdistricts)
    # I'll simulate a fetch from the backend since I can't read the .shp directly here easily
    # But I can check the shs.py aggregation results
    
    print(f"DB has {len(db_names)} unique village names.")
    
    # Check the actual aggregation results for Germination
    query = """
    SELECT v.name, count(*) 
    FROM old_village v
    JOIN soil_sample s ON v.village_id = s.village_id
    WHERE s.stage ILIKE 'Germination'
    GROUP BY v.name
    """
    with engine.connect() as conn:
        agg_results = pd.read_sql(query, conn)
    
    print(f"Aggregation found {len(agg_results)} matching villages with Germination data.")
    
    # List some names to see if they look okay
    print("Sample Names from Aggregation:")
    print(agg_results['name'].head(20).tolist())

scan_coverage()
