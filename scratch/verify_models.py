import sys
import os

# Add project root and backend to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_path = os.path.join(project_root, 'BhoomiSanket', 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from app.database import SessionLocal
    from app import models
except ImportError as e:
    print(f"Import Error: {e}")
    print(f"Current sys.path: {sys.path}")
    sys.exit(1)

db = None
try:
    db = SessionLocal()
    print("Testing State Model...")
    state = db.query(models.State).first()
    if state:
        print(f"  Found State: {state.name} (Code: {state.state_code})")
        
        print("Testing District Model via Relationship...")
        if state.districts:
            dist = state.districts[0]
            print(f"  Found District: {dist.name} (Code: {dist.district_code})")
            
            print("Testing Village Model via Relationship...")
            if dist.villages:
                vill = dist.villages[0]
                print(f"  Found Village: {vill.name} (ID: {vill.village_id})")
                
                print("Testing District back-relationship from Village...")
                if vill.district:
                    print(f"  Village parent district: {vill.district.name}")
                else:
                    print("  Village has no parent district relationship.")
            else:
                print("  No villages found for this district.")
        else:
            print("  No districts found for this state.")
    else:
        print("  No states found in DB.")

except Exception as e:
    print(f"Runtime Error: {e}")
finally:
    if db:
        db.close()
