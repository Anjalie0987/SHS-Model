from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.database import engine, Base
from app import models
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Create tables
Base.metadata.create_all(bind=engine)

# Lightweight DB migration for additive columns (Postgres).
# `create_all` won't add columns to existing tables, so we add new ripening columns safely.
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE IF EXISTS latlon_suitability ADD COLUMN IF NOT EXISTS rip_shs DOUBLE PRECISION"))
        conn.execute(text("ALTER TABLE IF EXISTS latlon_suitability ADD COLUMN IF NOT EXISTS rip_category VARCHAR"))
except Exception as e:
    # Don't hard-fail API startup if the DB is not reachable during dev.
    print(f"Warning: DB migration step failed: {e}")

app = FastAPI(title="Wheat SHS Backend", version="0.1.0")

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"  # Allow all for now, restrict in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.routers import shs
app.include_router(shs.router, prefix="/api", tags=["SHS"])

@app.get("/")
def read_root():
    return {"message": "Wheat SHS Backend API"}