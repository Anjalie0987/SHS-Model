import os
import sys
sys.path.append(os.getcwd())

from app.database import engine
from sqlalchemy import text

def find_data():
    with engine.connect() as conn:
        tables = conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public'")).fetchall()
        print("--- TABLE ROW COUNTS ---")
        for (table_name,) in tables:
            try:
                count = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar()
                if count > 0:
                    print(f"{table_name}: {count} rows")
                    
                    # If it has around 8000 rows, show columns
                    if 7000 < count < 9000:
                        from sqlalchemy import inspect
                        inspector = inspect(engine)
                        cols = [c['name'] for c in inspector.get_columns(table_name)]
                        print(f"  -> COLUMNS: {cols}")
            except:
                pass

if __name__ == "__main__":
    find_data()
