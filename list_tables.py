from sqlalchemy import create_engine, inspect

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)
inspector = inspect(engine)
print("Tables in db:")
for table_name in inspector.get_table_names():
    print(table_name)
