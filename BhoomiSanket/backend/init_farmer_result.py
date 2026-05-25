from app.database import engine
from app.models import Base

# This will create any tables defined in app.models that don't already exist
print("Creating new database tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
