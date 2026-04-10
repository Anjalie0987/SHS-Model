from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import uuid
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import LatLonSuitability
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

        # 3. Save to database
        analysis_id = str(uuid.uuid4())
        lat, lon = (request.coordinates[0], request.coordinates[1]) if request.coordinates else (0.0, 0.0)

        suitability_record = LatLonSuitability(
            batch_id=analysis_id,
            source_file="farmer_form_input",
            lat=lat,
            lon=lon,
            n=request.nitrogen,
            p=request.phosphorus,
            k=request.potassium,
            moisture=request.moisture,
            ph=request.ph,
            oc=request.organic_carbon,
            temp=request.temperature,
            ndvi=request.ndvi,
            germ_shs=res_g["SHS"],
            germ_category=res_g["Category"],
            boot_shs=res_b["SHS"],
            boot_category=res_b["Category"],
            rip_shs=res_r["SHS"],
            rip_category=res_r["Category"]
        )

        db.add(suitability_record)
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
