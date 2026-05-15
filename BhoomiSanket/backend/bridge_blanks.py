import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine

# SHP PATH
SHP_PATH = r"d:\CROP2\CROP2\SUBDISTRICT_BOUNDARY_WGS84.shp"
DATABASE_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DATABASE_URL)

def fix_all_blanks():
    # 1. Load SHP names
    gdf = gpd.read_file(SHP_PATH)
    # Common keys for subdistricts
    for col in ['TEHSIL', 'SUB_DIST', 'sdtname', 'TEHSIL_NAM', 'SubDistrict']:
        if col in gdf.columns:
            shp_names = gdf[col].dropna().unique().tolist()
            break
    
    shp_names = [str(n).strip().upper() for n in shp_names]
    print(f"Map has {len(shp_names)} subdistricts.")

    # 2. Get DB names
    with engine.connect() as conn:
        db_names = pd.read_sql("SELECT DISTINCT name FROM old_village", conn)['name'].tolist()
    db_names = [n.strip().upper() for n in db_names]

    # 3. Find Missing
    missing = [n for n in shp_names if n not in db_names]
    print(f"Missing {len(missing)} subdistricts in DB.")
    
    if missing:
        print(f"Sample missing: {missing[:10]}")
        
        # INSERT missing names into old_village to ensure they exist
        # This allows my random data generator to find them next time
        for name in missing:
             with engine.begin() as conn:
                 conn.execute(text("INSERT INTO old_village (name, district_id) VALUES (:name, 1) ON CONFLICT DO NOTHING"), {"name": name})
        
        print("Missing subdistricts added to DB table.")

fix_all_blanks()
