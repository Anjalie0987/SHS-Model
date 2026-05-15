from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.schemas.soil import SoilAnalysisRequest, SoilAnalysisResponse
from app.services.shs_service import SHSService
from geoalchemy2.elements import WKTElement
import random

router = APIRouter(
    prefix="/api",
    tags=["soil"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/analyze-soil", response_model=SoilAnalysisResponse)
async def analyze_soil(request: SoilAnalysisRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Create/Find Location Hierarchy
    state = db.query(models.State).filter(models.State.name == request.state).first()
    if not state:
        state = models.State(name=request.state)
        db.add(state)
        db.commit()
        db.refresh(state)

    district = db.query(models.District).filter(models.District.name == request.district, models.District.state_id == state.state_id).first()
    if not district:
        district = models.District(name=request.district, state_id=state.state_id)
        db.add(district)
        db.commit()
        db.refresh(district)

    village = db.query(models.Village).filter(models.Village.name == request.village, models.Village.district_id == district.district_id).first()
    if not village:
        village = models.Village(name=request.village, district_id=district.district_id)
        db.add(village)
        db.commit()
        db.refresh(village)

    # 2. Create/Find Farmer
    farmer = db.query(models.Farmer).filter(models.Farmer.mobile == request.mobile).first()
    if not farmer:
        farmer = models.Farmer(name=request.farmer_name, mobile=request.mobile)
        db.add(farmer)
        db.commit()
        db.refresh(farmer)

    # 3. Create/Find Farm
    # For now, mapping field_id to farm_name
    farm = db.query(models.Farm).filter(models.Farm.farm_name == request.field_id, models.Farm.farmer_id == farmer.farmer_id).first()
    
    # Handle coordinates (Expect [lat, lon] or similar)
    geom = None
    if request.coordinates and isinstance(request.coordinates, list) and len(request.coordinates) == 2:
        # Assuming [lat, lon] from frontend
        geom = WKTElement(f"POINT({request.coordinates[1]} {request.coordinates[0]})", srid=4326)

    if not farm:
        farm = models.Farm(
            farmer_id=farmer.farmer_id,
            village_id=village.village_id,
            farm_name=request.field_id,
            area_ha=request.field_area,
            geom=geom
        )
        db.add(farm)
        db.commit()
        db.refresh(farm)

    # 4. Create Soil Sample
    sample = models.SoilSample(
        farm_id=farm.farm_id,
        stage="Submission",
        geom=geom
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)

    # 5. Create Soil Parameter Values
    param_map = {
        "N": request.nitrogen,
        "P": request.phosphorus,
        "K": request.potassium,
        "pH": request.ph,
        "Moisture": request.moisture,
        "OC": request.organic_carbon,
        "Temp": request.temperature,
        "NDVI": request.ndvi
    }

    for p_name, p_val in param_map.items():
        master_param = db.query(models.SoilParameterMaster).filter(models.SoilParameterMaster.name == p_name).first()
        if master_param:
            val_entry = models.SoilParameterValue(
                soil_sample_id=sample.soil_sample_id,
                parameter_id=master_param.parameter_id,
                value=p_val
            )
            db.add(val_entry)
    
    db.commit()

    # 6. Trigger Background Processing
    background_tasks.add_task(SHSService.process_soil_sample, sample.soil_sample_id)

    # Maintain backwards compatible response logic (Simulated for UI)
    recommendations = []
    if request.nitrogen < 120: recommendations.append("Apply 50 kg Urea/acre to boost Nitrogen.")
    if request.phosphorus < 15: recommendations.append("Add DAP (Di-ammonium Phosphate) for root growth.")
    if not recommendations: recommendations.append("Soil is in good condition. Follow standard schedule.")

    return SoilAnalysisResponse(
        snsi_score=85.0, # Will be replaced by real score in cache
        soil_status="Excellent",
        nutrient_levels={
            "Nitrogen": f"{request.nitrogen}",
            "Phosphorus": f"{request.phosphorus}",
            "Potassium": f"{request.potassium}",
            "pH": f"{request.ph}"
        },
        recommendations=recommendations,
        map_classification="High",
        health_status="Safe"
    )
