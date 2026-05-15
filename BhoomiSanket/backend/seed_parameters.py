from app.database import SessionLocal
from app.models import SoilParameterMaster

def seed_parameters():
    db = SessionLocal()
    parameters = [
        {"name": "N", "unit": "mg/kg", "ideal_min": 150.0, "ideal_max": 280.0, "weight": 0.25},
        {"name": "P", "unit": "mg/kg", "ideal_min": 10.0, "ideal_max": 25.0, "weight": 0.20},
        {"name": "K", "unit": "mg/kg", "ideal_min": 110.0, "ideal_max": 200.0, "weight": 0.15},
        {"name": "Moisture", "unit": "%", "ideal_min": 15.0, "ideal_max": 25.0, "weight": 0.10},
        {"name": "pH", "unit": "pH", "ideal_min": 6.0, "ideal_max": 7.5, "weight": 0.10},
        {"name": "OC", "unit": "%", "ideal_min": 0.5, "ideal_max": 1.0, "weight": 0.10},
        {"name": "Temp", "unit": "C", "ideal_min": 15.0, "ideal_max": 25.0, "weight": 0.05},
        {"name": "NDVI", "unit": "index", "ideal_min": 0.6, "ideal_max": 0.9, "weight": 0.05},
    ]
    
    for param_data in parameters:
        existing = db.query(SoilParameterMaster).filter(SoilParameterMaster.name == param_data["name"]).first()
        if not existing:
            param = SoilParameterMaster(**param_data)
            db.add(param)
            print(f"Added parameter: {param_data['name']}")
        else:
            print(f"Parameter already exists: {param_data['name']}")
    
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_parameters()
