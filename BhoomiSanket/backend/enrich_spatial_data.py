import geopandas as gpd
from sqlalchemy import create_engine, text
import pandas as pd
import os

# DB Config
DB_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DB_URL)

SHP_PATH = r"d:\CROP2\CROP2\BhoomiSanket\backend\data\shapefiles\subdistrict\SUBDISTRICT_BOUNDARY_WGS84.shp"

def main():
    print("--- 1. Loading Shapefile ---")
    if not os.path.exists(SHP_PATH):
        print(f"Error: Shapefile not found at {SHP_PATH}")
        return
    
    gdf = gpd.read_file(SHP_PATH)
    # Ensure standard column names for the join
    # Check for 'SUBDISTRIC' or 'SDNAME' or 'NAME'
    print(f"Columns in SHP: {gdf.columns.tolist()}")
    
    # Identify the name column (Standard LGD or common names)
    name_col = None
    for c in ['SUBDISTRIC', 'SDNAME', 'NAME', 'name', 'sd_name', 'TEHSIL']:
        if c in gdf.columns:
            name_col = c
            break
    
    if not name_col:
        print("Error: Could not identify Subdistrict Name column in Shapefile")
        return

    print(f"Using '{name_col}' as the Subdistrict Name column.")

    print("--- 2. Uploading Boundaries to DB (village_boundary) ---")
    # We only need the geometry and the name for the enrichment
    gdf_to_db = gdf[[name_col, 'geometry']].copy()
    gdf_to_db.columns = ['name', 'geometry']
    
    # Save to SQL using GeoPandas to_postgis
    gdf_to_db.to_postgis("village_boundary", engine, if_exists="replace", index=False)
    print("Upload complete!")

    print("--- 3. Running Spatial Join to Enrich Soil Data ---")
    with engine.connect() as conn:
        # Update latlon_suitability where village_name is NULL
        # We match points to polygons
        query = text("""
            UPDATE latlon_suitability l
            SET village_name = vb.name
            FROM village_boundary vb
            WHERE ST_Within(ST_SetSRID(ST_Point(l.lon, l.lat), 4326), vb.geometry)
            AND l.village_name IS NULL;
        """)
        result = conn.execute(query)
        conn.commit()
        print(f"Enriched {result.rowcount} soil points with subdistrict names!")

    print("--- 4. Verification ---")
    with engine.connect() as conn:
        count = conn.execute(text("SELECT count(*) FROM latlon_suitability WHERE village_name IS NOT NULL")).scalar()
        print(f"Total points now linked to subdistricts: {count}")

if __name__ == "__main__":
    main()
