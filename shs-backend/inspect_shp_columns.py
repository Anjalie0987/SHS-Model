import geopandas as gpd
import os

BASE_DIR = r"d:\CROP2\CROP2\BhoomiSanket\backend"
SHAPEFILE_DIR = os.path.join(BASE_DIR, "data", "shapefiles")

STATE_SHP = os.path.join(SHAPEFILE_DIR, "state", "STATE_BOUNDARY_wgs84.shp")
DISTRICT_SHP = os.path.join(SHAPEFILE_DIR, "district", "DISTRICT_BOUNDARY_WGS84.shp")

print("--- STATE SHAPEFILE ---")
if os.path.exists(STATE_SHP):
    gdf_state = gpd.read_file(STATE_SHP)
    print("Columns:", gdf_state.columns.tolist())
    print("First row:", gdf_state.iloc[0].to_dict())
else:
    print("State SHP not found")

print("\n--- DISTRICT SHAPEFILE ---")
if os.path.exists(DISTRICT_SHP):
    gdf_dist = gpd.read_file(DISTRICT_SHP)
    print("Columns:", gdf_dist.columns.tolist())
    print("First row properties (excluding geometry):", {k:v for k,v in gdf_dist.iloc[0].to_dict().items() if k != 'geometry'})
else:
    print("District SHP not found")
