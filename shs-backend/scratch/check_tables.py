import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd()))

from app.database import engine
from sqlalchemy import inspect

def check_all_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Total tables found: {len(tables)}")
    
    for table in tables:
        # Check row count for each table
        with engine.connect() as conn:
            from sqlalchemy import text
            res = conn.execute(text(f"SELECT COUNT(*) FROM \"{table}\""))
            count = res.scalar()
            if count > 0:
                print(f"Table '{table}': {count} rows")
                
                # If table has shs in name, show columns
                if 'shs' in table.lower() or 'suitability' in table.lower() or 'sample' in table.lower() or 'score' in table.lower():
                    columns = [c['name'] for c in inspector.get_columns(table)]
                    print(f"  Columns: {columns}")

if __name__ == "__main__":
    check_all_tables()
