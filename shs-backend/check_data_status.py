from app.database import SessionLocal
from app.models import WheatGerminationSHS, WheatBootingSHS, WheatRipeningSHS
from sqlalchemy import func

def check_tables():
    session = SessionLocal()
    print("=== Soil Health Data Status ===")
    
    tables = [
        ("Germination", WheatGerminationSHS),
        ("Booting", WheatBootingSHS),
        ("Ripening", WheatRipeningSHS)
    ]
    
    try:
        for name, Model in tables:
            count = session.query(Model).count()
            print(f"\n[{name} Stage]")
            print(f"Total Records: {count}")
            
            if count > 0:
                # Get the most recent record date
                latest = session.query(func.max(Model.created_at)).scalar()
                # Get district breakdown (sample)
                districts = session.query(Model.district, func.count(Model.id)).group_by(Model.district).limit(5).all()
                
                print(f"Latest Upload: {latest}")
                print(f"Districts Sample: {districts}")
            else:
                print("No data found in this table.")
                
    except Exception as e:
        print(f"Error checking database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_tables()
