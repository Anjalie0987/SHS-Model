from sqlalchemy import create_engine, text
from geoalchemy2.elements import WKTElement

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    # Migrate farmers
    res = conn.execute(text("SELECT id, full_name, mobile_number, password, state, district, village, plot_number FROM old_farmers"))
    for row in res:
        farmer_id, full_name, mobile, password, state, district, village, plot_number = row
        
        # Insert into farmer
        try:
            conn.execute(text("INSERT INTO farmer (name, mobile, password) VALUES (:name, :mobile, :password) ON CONFLICT (mobile) DO NOTHING"), 
                         {"name": full_name, "mobile": mobile, "password": password})
            print(f"Migrated farmer {full_name}")
            
            # Since the old schema didn't link farm geometry correctly, we'll just insert a dummy farm for them later if needed.
        except Exception as e:
            print(f"Failed to migrate farmer {full_name}: {e}")
            
    conn.commit()
    print("Migration complete.")
