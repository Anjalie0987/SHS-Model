from sqlalchemy import create_engine, inspect

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)
inspector = inspect(engine)

for table in ['state', 'districts', 'village']:
    print(f"\nTable: {table}")
    pk = inspector.get_pk_constraint(table)
    print(f"Primary Key: {pk['constrained_columns']}")
    fks = inspector.get_foreign_keys(table)
    for fk in fks:
        print(f"Foreign Key: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
