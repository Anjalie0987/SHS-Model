from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    res = conn.execute(text("SELECT indexname FROM pg_indexes WHERE indexname LIKE 'idx_%' OR indexname LIKE 'ix_%';"))
    for row in res:
        print(row[0])
