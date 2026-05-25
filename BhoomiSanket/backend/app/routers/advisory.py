from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import FarmerResultGerm, FarmerResultBoot, FarmerResultRip, FarmerAdvisory
from app.utils.advisory_engine import AdvisoryEngine
import json

router = APIRouter(
    prefix="/advisory",
    tags=["advisory"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{farmer_id}")
def get_farmer_advisory(
    farmer_id: int,
    stage: str = Query(default="germination"),
    db: Session = Depends(get_db)
):
    stage = stage.lower().strip()
    
    stage_config = {
        "germination": (FarmerResultGerm, "germ_shs"),
        "booting":     (FarmerResultBoot, "boot_shs"),
        "ripening":    (FarmerResultRip,  "rip_shs"),
    }
    
    if stage not in stage_config:
        raise HTTPException(status_code=400, detail=f"Invalid stage '{stage}'")
        
    ModelClass, shs_attr = stage_config[stage]
    
    # Get all results for this farmer and stage
    results = db.query(ModelClass).filter(
        ModelClass.farmer_id == farmer_id
    ).order_by(ModelClass.created_at.desc()).all()
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No {stage} results found for this farmer.")
        
    engine = AdvisoryEngine(db)
    advisories = []
    
    for r in results:
        # Check if we already generated an advisory for this exact result
        existing = db.query(FarmerAdvisory).filter(
            FarmerAdvisory.result_id == r.id,
            FarmerAdvisory.stage == stage
        ).first()
        
        if existing:
            advisories.append({
                "point_id": r.id,
                "lat": r.lat,
                "lon": r.lon,
                "shs_score": existing.shs_score,
                "shs_category": existing.shs_category,
                "overall_advice": existing.overall_advice,
                "parameters": json.loads(existing.advisory_text)
            })
            continue
            
        # Generate new advisory
        inputs = {
            "nitrogen": r.nitrogen,
            "phosphorus": r.phosphorus,
            "potassium": r.potassium,
            "ph": r.ph,
            "moisture": r.moisture,
            "organic_carbon": r.organic_carbon,
            "temperature": r.temperature
        }
        
        shs_score = getattr(r, shs_attr)
        adv_data = engine.generate(inputs, shs_score)
        
        # Save to DB
        new_adv = FarmerAdvisory(
            farmer_id=farmer_id,
            result_id=r.id,
            stage=stage,
            lat=r.lat,
            lon=r.lon,
            shs_score=shs_score,
            shs_category=adv_data["shs_category"],
            overall_advice=adv_data["overall_advice"],
            advisory_text=json.dumps(adv_data["parameters"])
        )
        db.add(new_adv)
        
        advisories.append({
            "point_id": r.id,
            "lat": r.lat,
            "lon": r.lon,
            "shs_score": shs_score,
            "shs_category": adv_data["shs_category"],
            "overall_advice": adv_data["overall_advice"],
            "parameters": adv_data["parameters"]
        })
        
    db.commit()
    return advisories
