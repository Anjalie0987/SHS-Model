from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from app.database import SessionLocal
from app.schemas.farm_analysis import FarmDataResponse, LocationHierarchy, SubdistrictInfo
import hashlib

import geopandas as gpd
from shapely.geometry import Point
import numpy as np
import os

# Cache for all districts geometry
ALL_DISTRICTS_GDF = None

def load_all_districts():
    global ALL_DISTRICTS_GDF
    if ALL_DISTRICTS_GDF is not None:
        return
    
    try:
        shp_path = r'D:\CROP2\CROP2\BhoomiSanket\backend\data\shapefiles\district\DISTRICT_BOUNDARY_WGS84.shp'
        gdf = gpd.read_file(shp_path)
        # Load all districts
        ALL_DISTRICTS_GDF = gdf.copy()
        print(f"Loaded {len(ALL_DISTRICTS_GDF)} districts.")
    except Exception as e:
        print(f"Error loading district shapefile: {e}")
        ALL_DISTRICTS_GDF = None

# Initialize on module load
load_all_districts()

router = APIRouter(
    prefix="/farm-analysis",
    tags=["farm-analysis"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_district_from_coords(lat, lon):
    if ALL_DISTRICTS_GDF is None:
        return "UNKNOWN"
    
    p = Point(lon, lat)
    # Check which district contains this point
    for _, row in ALL_DISTRICTS_GDF.iterrows():
        if row.geometry.contains(p):
            return str(row['District']).upper()
    return "UNKNOWN"

@router.get("/locations", response_model=LocationHierarchy)
def get_locations(db: Session = Depends(get_db)):
    """
    Fetch unique States and Districts for dropdowns with codes.
    """
    try:
        # Fetch states from state table
        states_query = "SELECT name, state_code FROM state ORDER BY name"
        states_res = db.execute(text(states_query)).fetchall()
        states_list = [{"name": row[0], "code": row[1]} for row in states_res]
        
        # Fetch districts from districts table
        districts_query = "SELECT name, district_code, state_code FROM districts ORDER BY name"
        districts_res = db.execute(text(districts_query)).fetchall()
        
        districts_map = {}
        for row in districts_res:
            s_code = row[2]
            if s_code not in districts_map:
                districts_map[s_code] = []
            districts_map[s_code].append({"name": row[0], "code": row[1], "state_code": s_code})
            
        # Fetch villages from village table
        villages_query = "SELECT name, district_id FROM village ORDER BY name"
        villages_res = db.execute(text(villages_query)).fetchall()
        
        villages_map = {}
        for row in villages_res:
            v_name = row[0]
            d_id = row[1]
            if d_id not in villages_map:
                villages_map[d_id] = []
            villages_map[d_id].append({"name": v_name})

        return {
            "states": states_list,
            "districts": districts_map,
            "subdistricts": villages_map
        }
    except Exception as e:
        print(f"Error fetching locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subdistricts", response_model=List[SubdistrictInfo])
def get_subdistricts(
    state_code: int,
    district_code: int,
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Fetch subdistricts (villages) for a given state and district with optional search.
    """
    try:
        # We join village with districts by name (since district_id in village table is inconsistent)
        # and then filter by state_code and district_code
        query = """
            SELECT MIN(v.village_id), MAX(UPPER(v.name)) as subdistrict_name
            FROM village v
            JOIN districts d ON LOWER(v.district_name) = LOWER(d.name)
            WHERE d.state_code = :state_code AND d.district_code = :district_code
        """
        params = {"state_code": state_code, "district_code": district_code}
        
        if q:
            query += " AND v.name ILIKE :q"
            params["q"] = f"%{q}%"
            
        query += " GROUP BY LOWER(v.name) ORDER BY subdistrict_name LIMIT 20"
        
        results = db.execute(text(query), params).fetchall()
        return [{"id": row[0], "name": row[1]} for row in results]
    except Exception as e:
        print(f"Error fetching subdistricts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data", response_model=List[FarmDataResponse])
def get_farm_data(
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Fetch all farm data and link to districts via optimized spatial join.
    """
    try:
        query_str = "SELECT * FROM latlon_suitability"
        result = db.execute(text(query_str)).fetchall()
        
        if not result:
            return []

        # Convert to DataFrame for fast join
        import pandas as pd
        df = pd.DataFrame([dict(row._mapping) for row in result])
        
        # Create GeoDataFrame from points
        points_gdf = gpd.GeoDataFrame(
            df, 
            geometry=gpd.points_from_xy(df.lon, df.lat),
            crs="EPSG:4326"
        )
        
        # Spatial Join with Districts
        if ALL_DISTRICTS_GDF is not None:
            # Ensure CRS matches
            dist_gdf = ALL_DISTRICTS_GDF.to_crs("EPSG:4326")
            joined = gpd.sjoin(points_gdf, dist_gdf, how='left', predicate='within')
            # Extract District name (case insensitive match for 'District' column)
            dist_col = 'District' if 'District' in joined.columns else 'DISTRICT'
            joined['detected_district'] = joined[dist_col].fillna("UNKNOWN").str.upper()
        else:
            joined = points_gdf
            joined['detected_district'] = "UNKNOWN"

        farm_data = []
        for _, row in joined.iterrows():
            # Filtering by state if requested
            if state and state.upper() != "MAHARASHTRA" and row['detected_district'] == "MAHARASHTRA":
                continue

            farm_data.append({
                "farmer_id": f"LATLON_{row['id']}",
                "state": row['state_name'] or "MAHARASHTRA",
                "district": row['detected_district'],
                "subdistrict": "N/A",
                "latitude": row['lat'],
                "longitude": row['lon'],
                "lat": row['lat'],
                "lon": row['lon'],
                "nitrogen": row['nitrogen'],
                "phosphorus": row['phosphorus'],
                "potassium": row['potassium'],
                "ph": row['ph'],
                "organic_carbon": row['organic_carbon'],
                "moisture": row['moisture'],
                "temperature": row['temperature'],
                "shs_germination": row['shs_score'],
                "category_germination": row['shs_category'],
                "soil_type": "N/A",
                "crop_type": "Wheat",
                "recommended_fertilizer": "N/A"
            })
            
        return farm_data
        
    except Exception as e:
        print(f"Error fetching farm data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
