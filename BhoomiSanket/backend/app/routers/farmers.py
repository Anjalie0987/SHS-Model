from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.models import FarmerResultGerm, FarmerResultBoot, FarmerResultRip
from app.schemas.farmers import FarmerCreate, FarmerResponse, FarmerLogin
from passlib.context import CryptContext
import csv
import io

# Password hashing context - Switching to pbkdf2_sha256 for stability on Python 3.14
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

router = APIRouter(
    prefix="/farmers",
    tags=["farmers"]
)

# Helpers
def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=FarmerResponse, status_code=status.HTTP_201_CREATED)
def register_farmer(farmer: FarmerCreate, db: Session = Depends(get_db)):
    # Check if mobile number already exists
    db_farmer = db.query(models.Farmer).filter(models.Farmer.mobile == farmer.mobile_number).first()
    if db_farmer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number already registered"
        )
    
    try:
        hashed_password = get_password_hash(farmer.password)
    except Exception as e:
        print(f"Hashing error: {e}") 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing password"
        )
    
    # Lookup or create state
    state_obj = None
    if farmer.state:
        from sqlalchemy import func
        state_obj = db.query(models.State).filter(func.lower(models.State.name) == func.lower(farmer.state)).first()
        if not state_obj:
            # Get max state_code
            max_code = db.query(func.max(models.State.state_code)).scalar() or 0
            state_obj = models.State(name=farmer.state, state_code=max_code + 1)
            db.add(state_obj)
            db.commit()
            db.refresh(state_obj)

    # Lookup or create district
    district_obj = None
    if farmer.district and state_obj:
        district_obj = db.query(models.District).filter(
            func.lower(models.District.name) == func.lower(farmer.district), 
            models.District.state_code == state_obj.state_code
        ).first()
        if not district_obj:
            max_dcode = db.query(func.max(models.District.district_code)).scalar() or 0
            district_obj = models.District(name=farmer.district, state_code=state_obj.state_code, district_code=max_dcode + 1)
            db.add(district_obj)
            db.commit()
            db.refresh(district_obj)

    # Lookup or create village
    village_obj = None
    if farmer.village and district_obj:
        village_obj = db.query(models.Village).filter(
            func.lower(models.Village.name) == func.lower(farmer.village), 
            models.Village.district_id == district_obj.district_code
        ).first()
        if not village_obj:
            max_vcode = db.query(func.max(models.Village.village_id)).scalar() or 0
            village_obj = models.Village(name=farmer.village, district_id=district_obj.district_code, village_id=max_vcode + 1)
            db.add(village_obj)
            db.commit()
            db.refresh(village_obj)
    
    new_farmer = models.Farmer(
        name=farmer.full_name,
        mobile=farmer.mobile_number,
        password=hashed_password,
        gender=farmer.gender if farmer.gender else None,
        dob=farmer.dob if farmer.dob else None,
        aadhaar_encrypted=farmer.aadhaar if farmer.aadhaar else None
    )
    
    db.add(new_farmer)
    db.commit()
    db.refresh(new_farmer)
    
    # Create farm linking to the village and farmer
    if village_obj:
        new_farm = models.Farm(
            farmer_id=new_farmer.farmer_id,
            village_id=village_obj.village_id,
            farm_name=farmer.plot_number or f"{farmer.full_name}'s Farm",
            plot_number=farmer.plot_number if farmer.plot_number else None,
            area_ha=farmer.area_ha if farmer.area_ha not in ["", None] else None
        )
        db.add(new_farm)
        db.commit()
        db.refresh(new_farm)
    
    # Create a response object matching the expected FarmerResponse structure
    class DummyResponse:
        id = new_farmer.farmer_id
        full_name = new_farmer.name
        mobile_number = new_farmer.mobile
        gender = farmer.gender
        dob = farmer.dob
        state = farmer.state
        district = farmer.district
        village = farmer.village
        plot_number = farmer.plot_number
        created_at = None
    
    return DummyResponse()

@router.post("/login")
def login_farmer(credentials: FarmerLogin, db: Session = Depends(get_db)):
    db_farmer = db.query(models.Farmer).filter(models.Farmer.mobile == credentials.mobile_number).first()
    
    if not db_farmer or not verify_password(credentials.password, db_farmer.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mobile number or password"
        )
    
    farmer_dict = {
        "id": db_farmer.farmer_id,
        "full_name": db_farmer.name,
        "mobile_number": db_farmer.mobile,
        "state": None,
        "district": None,
        "village": None,
    }
    
    if db_farmer.farms and len(db_farmer.farms) > 0:
        farm = db_farmer.farms[0]
        if farm.village:
            farmer_dict["village"] = farm.village.name
            if farm.village.district:
                farmer_dict["district"] = farm.village.district.name
                if farm.village.district.state:
                    farmer_dict["state"] = farm.village.district.state.name

    return {
        "message": "Login successful",
        "farmer": farmer_dict
    }

@router.get("/{farmer_id}/results/download")
def download_farmer_results(
    farmer_id: int,
    stage: str = Query(default="germination", description="Stage: germination, booting, or ripening"),
    db: Session = Depends(get_db)
):
    """Download farmer soil analysis results for a specific stage as CSV."""
    stage = stage.lower().strip()

    # Pick the correct table model and SHS score column
    stage_config = {
        "germination": (FarmerResultGerm, "germ_shs", "Germination SHS (%)"),
        "booting":     (FarmerResultBoot, "boot_shs", "Booting SHS (%)"),
        "ripening":    (FarmerResultRip,  "rip_shs",  "Ripening SHS (%)"),
    }
    if stage not in stage_config:
        raise HTTPException(status_code=400, detail=f"Invalid stage '{stage}'. Choose: germination, booting, ripening.")

    ModelClass, shs_attr, shs_label = stage_config[stage]

    results = db.query(ModelClass).filter(
        ModelClass.farmer_id == farmer_id
    ).order_by(ModelClass.created_at.desc()).all()

    if not results:
        raise HTTPException(status_code=404, detail=f"No {stage} results found for this farmer.")

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row — only the relevant SHS column
    writer.writerow([
        "ID", "Latitude", "Longitude",
        "Nitrogen (N)", "Phosphorus (P)", "Potassium (K)",
        "pH", "Moisture (%)", "Organic Carbon (%)", "Temperature (°C)",
        shs_label,
        "Analyzed At"
    ])

    # Data rows
    for r in results:
        writer.writerow([
            r.id, r.lat, r.lon,
            r.nitrogen, r.phosphorus, r.potassium,
            r.ph, r.moisture, r.organic_carbon, r.temperature,
            getattr(r, shs_attr),
            r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
        ])

    output.seek(0)
    filename = f"farmer_{farmer_id}_{stage}_results.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
