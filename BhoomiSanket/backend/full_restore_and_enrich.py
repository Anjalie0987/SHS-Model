import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd
import geopandas as gpd

# DB Config
DB_URL = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(DB_URL)

SHP_PATH = r"d:\CROP2\CROP2\BhoomiSanket\backend\data\shapefiles\subdistrict\SUBDISTRICT_BOUNDARY_WGS84.shp"

def migrate_and_enrich():
    # 1. Fetch old data
    print("--- 1. Fetching Old Data ---")
    df_old = pd.read_sql("SELECT * FROM old_latlon_suitability", engine)
    print(f"Found {len(df_old)} records in old table.")

    # 2. Prepare stage-specific suitability rows
    print("--- 2. Preparing Suitability Data ---")
    stages = [
        ('Germination', 'germ_shs', 'germ_category'),
        ('Booting', 'boot_shs', 'boot_category'),
        ('Ripening', 'rip_shs', 'rip_category')
    ]

    all_new_rows = []
    
    for stage_name, shs_col, cat_col in stages:
        stage_df = df_old.copy()
        stage_df['stage'] = stage_name
        stage_df['shs_score'] = stage_df[shs_col]
        stage_df['shs_category'] = stage_df[cat_col]
        stage_df['state_name'] = 'Maharashtra'
        stage_df['district_name'] = 'UNKNOWN'
        stage_df['village_name'] = None
        
        # Select required columns for latlon_suitability
        cols = {
            'lat': 'lat',
            'lon': 'lon',
            'n': 'nitrogen',
            'p': 'phosphorus',
            'k': 'potassium',
            'moisture': 'moisture',
            'ph': 'ph',
            'oc': 'organic_carbon',
            'temp': 'temperature',
            'shs_score': 'shs_score',
            'shs_category': 'shs_category',
            'stage': 'stage',
            'state_name': 'state_name',
            'district_name': 'district_name',
            'village_name': 'village_name'
        }
        stage_df_final = stage_df.rename(columns=cols)[list(cols.values())]
        all_new_rows.append(stage_df_final)

    full_suitability_df = pd.concat(all_new_rows)
    
    print("--- 3. Uploading to latlon_suitability ---")
    # Clear existing data to avoid duplicates if re-running
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE latlon_suitability CASCADE"))
        conn.commit()

    full_suitability_df.to_sql("latlon_suitability", engine, if_exists="append", index=False)
    print(f"Successfully migrated {len(full_suitability_df)} rows.")

    # 4. Spatial Enrichment
    print("--- 4. Running Spatial Enrichment (Tehsils) ---")
    gdf_tehsil = gpd.read_file(SHP_PATH)
    gdf_tehsil = gdf_tehsil[['District', 'TEHSIL', 'geometry']]
    gdf_tehsil.columns = ['district_name', 'village_name', 'geometry']
    
    # Upload boundaries to temp table
    gdf_tehsil.to_postgis("temp_tehsil_boundary", engine, if_exists="replace", index=False)

    with engine.connect() as conn:
        # Update District and Village names from the shapefile
        # Also update the 'geom' column in latlon_suitability
        print("Updating database names and geometries...")
        conn.execute(text("""
            UPDATE latlon_suitability
            SET geom = ST_SetSRID(ST_Point(lon, lat), 4326);
            
            UPDATE latlon_suitability l
            SET district_name = UPPER(t.district_name),
                village_name = UPPER(t.village_name)
            FROM temp_tehsil_boundary t
            WHERE ST_Within(l.geom, t.geometry);
        """))
        conn.commit()
    print("Enrichment complete!")

if __name__ == "__main__":
    migrate_and_enrich()
