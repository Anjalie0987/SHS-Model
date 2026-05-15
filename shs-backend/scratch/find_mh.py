import os
import sys
sys.path.append(os.getcwd())

from app.database import engine
from sqlalchemy import text

def find_maharashtra_tables():
    with engine.connect() as conn:
        tables = conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public'")).fetchall()
        print("--- MAHARASHTRA DATA SCAN ---")
        for (table_name,) in tables:
            try:
                # Check if table has a 'state' or 'state_name' column
                from sqlalchemy import inspect
                inspector = inspect(engine)
                cols = [c['name'].lower() for c in inspector.get_columns(table_name)]
                
                state_col = None
                for c in cols:
                    if 'state' in c:
                        state_col = c
                        break
                
                if state_col:
                    count_mh = conn.execute(text(f"SELECT COUNT(*) FROM \"{table_name}\" WHERE UPPER(\"{state_col}\") LIKE '%MAHARASHTRA%'")).scalar()
                    count_total = conn.execute(text(f"SELECT COUNT(*) FROM \"{table_name}\"")).scalar()
                    if count_mh > 0:
                        print(f"Table '{table_name}': {count_mh} Maharashtra rows (out of {count_total})")
                else:
                    # Try joining with old_state/old_district if possible, or just check for common subdistricts
                    pass
            except:
                pass

if __name__ == "__main__":
    find_maharashtra_tables()
