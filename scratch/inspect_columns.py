from sqlalchemy import create_engine, inspect

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)
inspector = inspect(engine)

for table_name in ['state', 'districts', 'village']:
    print(f"\nColumns in {table_name}:")
    for column in inspector.get_columns(table_name):
        print(f" - {column['name']} ({column['type']})")
