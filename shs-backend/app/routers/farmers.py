from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from app.database import get_db
from app.models import Farmer, Farm, Village, District, State

router = APIRouter()

# --- Schemas ---

class FarmerRegistrationRequest(BaseModel):
    full_name: str
    mobile_number: str
    password: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    state: str
    district: str
    village: Optional[str] = None
    plot_number: Optional[str] = None
    aadhaar: Optional[str] = None
    area_ha: Optional[float] = None

class FarmerLoginRequest(BaseModel):
    mobile_number: str
    password: str

# --- Endpoints ---

@router.post("/register")
def register_farmer(payload: FarmerRegistrationRequest, db: Session = Depends(get_db)):
    # 1. Check if mobile already exists
    existing_farmer = db.query(Farmer).filter(Farmer.mobile == payload.mobile_number).first()
    if existing_farmer:
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    # 2. Resolve location to get village_id
    # To do this safely, we lookup the village. If it doesn't exist, we might need to create it 
    # or just use a fallback. Since this is a demo, we will try to find a matching village,
    # or create a dummy village record if it does not exist.
    
    state_rec = db.query(State).filter(func.lower(State.name) == func.lower(payload.state)).first()
    if not state_rec:
        raise HTTPException(status_code=400, detail=f"State '{payload.state}' not found in database")
        
    district_rec = db.query(District).filter(
        District.state_code == state_rec.state_code,
        func.lower(District.name) == func.lower(payload.district)
    ).first()
    
    if not district_rec:
        raise HTTPException(status_code=400, detail=f"District '{payload.district}' not found in state '{payload.state}'")

    village_id = None
    if payload.village:
        village_rec = db.query(Village).filter(
            Village.district_id == district_rec.district_code,
            func.lower(Village.name) == func.lower(payload.village)
        ).first()
        
        if village_rec:
            village_id = village_rec.village_id
        else:
            # Create a new village dynamically for the demo
            # Get max village_id to create a new one safely
            max_vid = db.query(func.max(Village.village_id)).scalar() or 0
            new_village = Village(
                village_id=max_vid + 1,
                district_id=district_rec.district_code,
                name=payload.village,
                state_name=state_rec.name,
                district_name=district_rec.name
            )
            db.add(new_village)
            db.commit()
            db.refresh(new_village)
            village_id = new_village.village_id

    # 3. Create Farmer
    new_farmer = Farmer(
        name=payload.full_name,
        mobile=payload.mobile_number,
        password=payload.password, # In production, hash this!
        gender=payload.gender,
        dob=payload.dob,
        aadhaar_encrypted=payload.aadhaar # Storing raw for demo purposes
    )
    db.add(new_farmer)
    db.commit()
    db.refresh(new_farmer)

    # 4. Create Farm
    new_farm = Farm(
        farmer_id=new_farmer.farmer_id,
        village_id=village_id,
        farm_name=f"{payload.full_name}'s Farm",
        plot_number=payload.plot_number,
        area_ha=payload.area_ha
    )
    db.add(new_farm)
    db.commit()

    return {"message": "Farmer registered successfully", "farmer_id": new_farmer.farmer_id}


@router.post("/login")
def login_farmer(payload: FarmerLoginRequest, db: Session = Depends(get_db)):
    farmer = db.query(Farmer).filter(
        Farmer.mobile == payload.mobile_number,
        Farmer.password == payload.password
    ).first()

    if not farmer:
        raise HTTPException(status_code=401, detail="Invalid mobile number or password")

    return {
        "message": "Login successful",
        "farmer": {
            "id": farmer.farmer_id,
            "full_name": farmer.name,
            "mobile_number": farmer.mobile,
            "gender": farmer.gender
        }
    }
