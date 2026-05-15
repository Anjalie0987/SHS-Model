from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from app.database import SessionLocal
from app.schemas.farm_analysis import FarmDataResponse, LocationHierarchy
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
    Fetch unique States and Districts for dropdowns.
    """
    try:
        # Fetch states and districts from the Hierarchy tables (Chain of Responsibility)
        query = """
            SELECT DISTINCT s.name as state_name, d.name as district_name 
            FROM state s
            JOIN districts d ON s.state_code = d.state_code
            WHERE s.name ILIKE '%MAHARASHTRA%'
        """
        results = db.execute(text(query)).fetchall()
        
        states_set = set()
        districts_map = {}
        
        for row in results:
            s_name = row[0] or "MAHARASHTRA"
            d_name = row[1] or "Unknown"
            
            states_set.add(s_name)
            if s_name not in districts_map:
                districts_map[s_name] = []
            if d_name not in districts_map[s_name]:
                districts_map[s_name].append(d_name)
        
        # If DB is empty or no Maharashtra data found, fall back to shapefile names
        if not states_set:
            states = ["MAHARASHTRA"]
            districts = {"MAHARASHTRA": []}
            if ALL_DISTRICTS_GDF is not None:
                # Filter shapefile for Maharashtra districts specifically
                districts["MAHARASHTRA"] = sorted(ALL_DISTRICTS_GDF['District'].unique().tolist())
            return {
                "states": states,
                "districts": districts,
                "subdistricts": {}
            }
            
        return {
            "states": sorted(list(states_set)),
            "districts": {s: sorted(d) for s, d in districts_map.items()},
            "subdistricts": {}
        }
    except Exception as e:
        print(f"Error fetching locations: {e}")
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
