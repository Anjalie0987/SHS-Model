from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import SessionLocal
from app import models
from pydantic import BaseModel

router = APIRouter(
    prefix="/germination",
    tags=["germination"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def normalize_db_name(name):
    """
    Normalizes corrupted database names (e.g. BIL>SPUR -> BILASPUR)
    to match cleaned shapefile names.
    """
    if not name:
        return "UNKNOWN"
    name = name.upper()
    name = name.replace('>', 'A').replace('<', 'A')
    name = name.replace('|', 'I').replace('\\', 'I')
    name = name.replace('@', 'U').replace('#', 'U')
    return name.strip()

class GerminationDataResponse(BaseModel):
    pixel_id: int
    state: Optional[str]
    nitrogen: Optional[float]
    phosphorus: Optional[float]
    potassium: Optional[float]
    moisture: Optional[float]
    ph: Optional[float]
    organic_carbon: Optional[float]
    temperature: Optional[float]
    shs_germination: Optional[float]
    category_germination: Optional[str]

    class Config:
        from_attributes = True

@router.get("/", response_model=List[GerminationDataResponse])
def get_all_germination_data(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Fetch all germination data from the GIS cache with pagination.
    """
    results = db.query(models.LatLonSuitability).filter(models.LatLonSuitability.stage == "Germination").offset(skip).limit(limit).all()
    
    # Map to schema
    return [
        GerminationDataResponse(
            pixel_id=r.id,
            state=r.state_name,
            nitrogen=r.nitrogen,
            phosphorus=r.phosphorus,
            potassium=r.potassium,
            moisture=r.moisture,
            ph=r.ph,
            organic_carbon=r.organic_carbon,
            temperature=r.temperature,
            shs_germination=r.shs_score,
            category_germination=r.shs_category
        ) for r in results
    ]

@router.get("/stats/categories")
def get_germination_category_stats(db: Session = Depends(get_db)):
    """
    Get summary statistics of germination categories.
    """
    from sqlalchemy import func
    stats = db.query(
        models.LatLonSuitability.shs_category,
        func.count(models.LatLonSuitability.id)
    ).filter(models.LatLonSuitability.stage == "Germination").group_by(models.LatLonSuitability.shs_category).all()
    
    return {category: count for category, count in stats}

@router.get("/state-stats")
def get_germination_state_stats(db: Session = Depends(get_db)):
    """
    Get averaged soil and germination data per state.
    """
    from sqlalchemy import func
    stats = db.query(
        models.LatLonSuitability.state_name,
        func.avg(models.LatLonSuitability.shs_score).label("shs_germination"),
        func.avg(models.LatLonSuitability.nitrogen).label("nitrogen"),
        func.avg(models.LatLonSuitability.phosphorus).label("phosphorus"),
        func.avg(models.LatLonSuitability.potassium).label("potassium"),
        func.avg(models.LatLonSuitability.ph).label("ph"),
        func.avg(models.LatLonSuitability.moisture).label("moisture"),
        func.avg(models.LatLonSuitability.organic_carbon).label("organic_carbon"),
        func.avg(models.LatLonSuitability.temperature).label("temperature")
    ).filter(models.LatLonSuitability.stage == "Germination").group_by(models.LatLonSuitability.state_name).all()
    
    return {
        normalize_db_name(row.state_name): {
            "shs_germination": row.shs_germination,
            "nitrogen": row.nitrogen,
            "phosphorus": row.phosphorus,
            "potassium": row.potassium,
            "ph": row.ph,
            "moisture": row.moisture,
            "organic_carbon": row.organic_carbon,
            "temperature": row.temperature
        } for row in stats
    }

@router.get("/district-stats")
def get_germination_district_stats(db: Session = Depends(get_db)):
    """
    Get averaged soil data per district using the cached GIS table.
    """
    results = db.query(models.LatLonSuitability).filter(models.LatLonSuitability.stage == "Germination").all()
    
    district_data = {}
    
    for r in results:
        d_name = normalize_db_name(r.district_name)
        
        if d_name not in district_data:
            district_data[d_name] = {
                "shs_germination": [], "nitrogen": [], "phosphorus": [], 
                "potassium": [], "ph": [], "moisture": [], 
                "organic_carbon": [], "temperature": [],
                "categories": []
            }
        
        d = district_data[d_name]
        if r.shs_score is not None: d["shs_germination"].append(r.shs_score)
        if r.nitrogen is not None: d["nitrogen"].append(r.nitrogen)
        if r.phosphorus is not None: d["phosphorus"].append(r.phosphorus)
        if r.potassium is not None: d["potassium"].append(r.potassium)
        if r.ph is not None: d["ph"].append(r.ph)
        if r.moisture is not None: d["moisture"].append(r.moisture)
        if r.organic_carbon is not None: d["organic_carbon"].append(r.organic_carbon)
        if r.temperature is not None: d["temperature"].append(r.temperature)
        if r.shs_category: d["categories"].append(r.shs_category)

    final_stats = {}
    import numpy as np
    from collections import Counter
    
    for name, vals in district_data.items():
        majority_cat = "Good"
        if vals["categories"]:
            majority_cat = Counter(vals["categories"]).most_common(1)[0][0]

        final_stats[name] = {
            k: float(np.mean(v)) if v else 0.0 for k, v in vals.items() if k != "categories"
        }
        final_stats[name]["category_germination"] = majority_cat
    
    return final_stats

@router.get("/village-stats")
def get_germination_village_stats(db: Session = Depends(get_db)):
    """
    Get averaged soil data per village/subdistrict.
    """
    results = db.query(models.LatLonSuitability).filter(models.LatLonSuitability.stage == "Germination").all()
    
    village_data = {}
    for r in results:
        v_name = normalize_db_name(r.village_name)
        
        if v_name not in village_data:
            village_data[v_name] = {
                "shs_germination": [], "nitrogen": [], "phosphorus": [], 
                "potassium": [], "ph": [], "moisture": [], 
                "organic_carbon": [], "temperature": [],
                "categories": []
            }
        
        v = village_data[v_name]
        if r.shs_score is not None: v["shs_germination"].append(r.shs_score)
        if r.nitrogen is not None: v["nitrogen"].append(r.nitrogen)
        if r.phosphorus is not None: v["phosphorus"].append(r.phosphorus)
        if r.potassium is not None: v["potassium"].append(r.potassium)
        if r.ph is not None: v["ph"].append(r.ph)
        if r.moisture is not None: v["moisture"].append(r.moisture)
        if r.organic_carbon is not None: v["organic_carbon"].append(r.organic_carbon)
        if r.temperature is not None: v["temperature"].append(r.temperature)
        if r.shs_category: v["categories"].append(r.shs_category)

    final_stats = {}
    import numpy as np
    from collections import Counter
    
    for name, vals in village_data.items():
        majority_cat = "Good"
        if vals["categories"]:
            majority_cat = Counter(vals["categories"]).most_common(1)[0][0]

        final_stats[name] = {
            k: float(np.mean(v)) if v else 0.0 for k, v in vals.items() if k != "categories"
        }
        final_stats[name]["category_germination"] = majority_cat
    
    return final_stats
