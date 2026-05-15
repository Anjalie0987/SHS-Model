import os
import sys
sys.path.append(os.getcwd())

from app.database import engine
from sqlalchemy import text

def find_mh_id():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT state_id, name FROM old_state WHERE name ILIKE '%MAHARASHTRA%'")).fetchone()
        if res:
            mh_id = res[0]
            print(f"Maharashtra ID: {mh_id}")
            
            # Check districts
            d_count = conn.execute(text(f"SELECT COUNT(*) FROM old_district WHERE state_id = {mh_id}")).scalar()
            print(f"Districts in Maharashtra: {d_count}")
            
            # Check villages
            v_count = conn.execute(text(f"SELECT COUNT(*) FROM old_village v JOIN old_district d ON v.district_id = d.district_id WHERE d.state_id = {mh_id}")).scalar()
            print(f"Villages in Maharashtra (via old_village): {v_count}")
            
            # Check village_boundary
            try:
                vb_count = conn.execute(text(f"SELECT COUNT(*) FROM village_boundary WHERE UPPER(state_name) LIKE '%MAHARASHTRA%'")).scalar()
                print(f"Subdistricts in Maharashtra (via village_boundary): {vb_count}")
            except:
                pass
        else:
            print("Maharashtra not found in old_state table.")

if __name__ == "__main__":
    find_mh_id()
