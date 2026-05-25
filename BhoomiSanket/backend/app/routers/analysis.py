from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import LatLonSuitability, FarmerResultGerm, FarmerResultBoot, FarmerResultRip
from app.utils.wheat_engine import WheatSHSEngine

router = APIRouter(
    prefix="/analyze",
    tags=["analysis"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AnalysisRequest(BaseModel):
    farmer_name: str
    field_id: str
    state: str
    district: str
    sub_district: str
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    moisture: float
    organic_carbon: float
    temperature: float
    selected_stage: Optional[str] = "germination"
    ndvi: Optional[float] = 0.7  # Default NDVI for booting/ripening if not provided
    coordinates: Optional[List[float]] = None
    farmer_id: Optional[int] = None  # Actual farmer PK from farmer table

class AnalysisResponse(BaseModel):
    analysis_id: str
    message: str
    germ_shs: float
    boot_shs: float
    rip_shs: float
    sub_district: str

@router.post("/", response_model=AnalysisResponse)
async def analyze_soil(request: AnalysisRequest, db: Session = Depends(get_db)):
    try:
        # 1. Prepare data for the engine
        sample = {
            "N": request.nitrogen,
            "P": request.phosphorus,
            "K": request.potassium,
            "pH": request.ph,
            "Moisture": request.moisture,
            "OC": request.organic_carbon,
            "Temp": request.temperature,
            "NDVI": request.ndvi
        }

        # 2. Run Engine for all stages
        germ_engine = WheatSHSEngine("germination")
        boot_engine = WheatSHSEngine("booting")
        rip_engine = WheatSHSEngine("ripening")

        res_g = germ_engine.predict(sample)
        res_b = boot_engine.predict(sample)
        res_r = rip_engine.predict(sample)

        analysis_id = str(uuid.uuid4())
        lat, lon = (request.coordinates[0], request.coordinates[1]) if request.coordinates else (0.0, 0.0)
        
        # Insert into the correct stage-specific table
        stage = (request.selected_stage or "germination").lower().strip()
        base_fields = dict(
            farmer_id=request.farmer_id,
            lat=lat,
            lon=lon,
            nitrogen=request.nitrogen,
            phosphorus=request.phosphorus,
            potassium=request.potassium,
            ph=request.ph,
            moisture=request.moisture,
            organic_carbon=request.organic_carbon,
            temperature=request.temperature,
        )
        if stage == "booting":
            farmer_result = FarmerResultBoot(**base_fields, boot_shs=res_b["SHS"])
        elif stage == "ripening":
            farmer_result = FarmerResultRip(**base_fields, rip_shs=res_r["SHS"])
        else:  # germination (default)
            farmer_result = FarmerResultGerm(**base_fields, germ_shs=res_g["SHS"])

        db.add(farmer_result)
        db.commit()
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            message="Analysis completed and saved successfully",
            germ_shs=res_g["SHS"],
            boot_shs=res_b["SHS"],
            rip_shs=res_r["SHS"],
            sub_district=request.sub_district
        )
    except Exception as e:
        db.rollback()
        print(f"Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
