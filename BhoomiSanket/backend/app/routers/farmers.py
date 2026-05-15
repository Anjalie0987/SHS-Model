from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.schemas.farmers import FarmerCreate, FarmerResponse, FarmerLogin
from passlib.context import CryptContext

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
        state_obj = db.query(models.State).filter(models.State.name == farmer.state).first()
        if not state_obj:
            state_obj = models.State(name=farmer.state)
            db.add(state_obj)
            db.commit()
            db.refresh(state_obj)

    # Lookup or create district
    district_obj = None
    if farmer.district and state_obj:
        district_obj = db.query(models.District).filter(models.District.name == farmer.district, models.District.state_id == state_obj.state_id).first()
        if not district_obj:
            district_obj = models.District(name=farmer.district, state_id=state_obj.state_id)
            db.add(district_obj)
            db.commit()
            db.refresh(district_obj)

    # Lookup or create village
    village_obj = None
    if farmer.village and district_obj:
        village_obj = db.query(models.Village).filter(models.Village.name == farmer.village, models.Village.district_id == district_obj.district_id).first()
        if not village_obj:
            village_obj = models.Village(name=farmer.village, district_id=district_obj.district_id)
            db.add(village_obj)
            db.commit()
            db.refresh(village_obj)
    
    new_farmer = models.Farmer(
        name=farmer.full_name,
        mobile=farmer.mobile_number,
        password=hashed_password
    )
    
    db.add(new_farmer)
    db.commit()
    db.refresh(new_farmer)
    
    # Create farm linking to the village and farmer
    if village_obj:
        new_farm = models.Farm(
            farmer_id=new_farmer.farmer_id,
            village_id=village_obj.village_id,
            farm_name=farmer.plot_number or f"{farmer.full_name}'s Farm"
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
    
    return {
        "message": "Login successful",
        "farmer": {
            "id": db_farmer.farmer_id,
            "full_name": db_farmer.name,
            "mobile_number": db_farmer.mobile
        }
    }
