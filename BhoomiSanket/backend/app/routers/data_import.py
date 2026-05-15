from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal, engine
from app import models
from app.services.shs_service import SHSService
import pandas as pd
import io

router = APIRouter(
    prefix="/import",
    tags=["import"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/soil-data")
async def import_soil_data(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import CSV Data into Normalized Database.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    try:
        content = await file.read()
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # Normalize headers
        df.columns = [c.strip().lower() for c in df.columns]
        
        rename_map = {
            'n': 'n', 'p': 'p', 'k': 'k',
            'ph': 'ph', 'oc': 'oc', 'nitrogen': 'n', 'phosphorus': 'p', 'potassium': 'k',
            'soil_ph': 'ph', 'soc': 'oc', 'soil_moisture': 'moisture', 'moisture': 'moisture',
            'temperature': 'temp', 'temp': 'temp', 'ndvi': 'ndvi'
        }
        df.rename(columns=rename_map, inplace=True)

        # Helper to safely parse float
        def safe_float(val, default=0.0):
            try:
                if pd.isna(val) or val is None: return default
                return float(val)
            except:
                return default

        imported_count = 0
        for index, row in df.iterrows():
            # 1. Location Hierarchy (Using defaults if missing)
            state_name = str(row.get('state', 'Punjab')).strip().title()
            district_name = str(row.get('district', 'Amritsar')).strip().upper()
            village_name = str(row.get('village', 'Default Village')).strip().title()

            state = db.query(models.State).filter(models.State.name == state_name).first()
            if not state:
                state = models.State(name=state_name)
                db.add(state)
                db.commit(); db.refresh(state)

            district = db.query(models.District).filter(models.District.name == district_name, models.District.state_id == state.state_id).first()
            if not district:
                district = models.District(name=district_name, state_id=state.state_id)
                db.add(district); db.commit(); db.refresh(district)

            village = db.query(models.Village).filter(models.Village.name == village_name, models.Village.district_id == district.district_id).first()
            if not village:
                village = models.Village(name=village_name, district_id=district.district_id)
                db.add(village); db.commit(); db.refresh(village)

            # 2. Farmer & Farm
            farmer_name = str(row.get('farmer', 'CSV Farmer')).strip()
            mobile = str(row.get('mobile', f"99{index:08d}"))
            
            farmer = db.query(models.Farmer).filter(models.Farmer.mobile == mobile).first()
            if not farmer:
                farmer = models.Farmer(name=farmer_name, mobile=mobile)
                db.add(farmer); db.commit(); db.refresh(farmer)

            farm = models.Farm(
                farmer_id=farmer.farmer_id,
                village_id=village.village_id,
                farm_name=f"Farm_{index}",
                area_ha=safe_float(row.get('area', 1.0))
            )
            db.add(farm); db.commit(); db.refresh(farm)

            # 3. Soil Sample
            sample = models.SoilSample(
                farm_id=farm.farm_id,
                stage="CSV Import"
            )
            db.add(sample); db.commit(); db.refresh(sample)

            # 4. Parameters
            param_map = {
                "N": safe_float(row.get('n')),
                "P": safe_float(row.get('p')),
                "K": safe_float(row.get('k')),
                "pH": safe_float(row.get('ph')),
                "Moisture": safe_float(row.get('moisture')),
                "OC": safe_float(row.get('oc')),
                "Temp": safe_float(row.get('temp')),
                "NDVI": safe_float(row.get('ndvi'))
            }

            for p_name, p_val in param_map.items():
                master_param = db.query(models.SoilParameterMaster).filter(models.SoilParameterMaster.name == p_name).first()
                if master_param:
                    db.add(models.SoilParameterValue(
                        soil_sample_id=sample.soil_sample_id,
                        parameter_id=master_param.parameter_id,
                        value=p_val
                    ))
            
            db.commit()

            # 5. Trigger Background Task
            background_tasks.add_task(SHSService.process_soil_sample, sample.soil_sample_id)
            imported_count += 1

        return {"message": f"Successfully imported {imported_count} records. Background processing started."}

    except Exception as e:
        db.rollback()
        print(f"Import Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
