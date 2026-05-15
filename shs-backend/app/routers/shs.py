from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np
import logging
import os
import uuid
import io
import re
from datetime import datetime, timedelta
from app.database import get_db
from app.models import (
    WheatGerminationSHS, WheatBootingSHS, WheatRipeningSHS, 
    LatLonSuitability, UploadBatch, UploadedCSVData
)
from fastapi.responses import StreamingResponse
from app.model.wheat_shs_engine import WheatSHSEngine

router = APIRouter()

# ==========================================================
# LOGGING CONFIGURATION
# ==========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WheatSHSEngine")

# NEW: lat-long germination pipeline defaults (only used by the new local-file processor)
DEFAULT_BOOTING_NDVI = 0.7
DEFAULT_RIPENING_NDVI = 0.6

# NEW: file-based processing folders (no UI upload needed)
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(APP_DIR, "Data")
OUTPUTS_DIR = os.path.join(APP_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)


def _safe_join_csv(base_dir: str, filename: str) -> str:
    """
    NEW: Restrict reads to CSV files inside a known base directory.
    """
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="filename must end with .csv")

    full = os.path.abspath(os.path.join(base_dir, filename))
    base = os.path.abspath(base_dir)
    if not full.startswith(base + os.sep):
        raise HTTPException(status_code=400, detail="Invalid filename/path")
    return full


def _write_standard_output_csv(processed_df: pd.DataFrame, original_columns: list, stage: str, output_path: str):
    """
    NEW: Shared output CSV writer (same rules as existing upload pipeline).
    Keeps input columns + SHS + avg_shs + category.
    """
    if "SHS" in processed_df.columns:
        processed_df["avg_shs"] = processed_df["SHS"]
    else:
        processed_df["avg_shs"] = None

    processed_df["category"] = processed_df.get("Category")

    final_columns = list(original_columns)
    if "SHS" in processed_df.columns and "SHS" not in final_columns:
        final_columns.append("SHS")
    for extra_col in ["avg_shs", "category"]:
        if extra_col not in final_columns:
            final_columns.append(extra_col)

    processed_df.to_csv(output_path, index=False, columns=final_columns)
    logger.info(f"Written SHS output CSV for stage '{stage}' to {output_path}")

# ==========================================================
# AHP MATRICES
# ==========================================================

GERMINATION_MATRIX = np.array([
[1,1/3,3,1/3,3,3,5],
[3,1,5,1,5,5,7],
[1/3,1/5,1,1/5,3,3,5],
[3,1,5,1,5,5,7],
[1/3,1/5,1/3,1/5,1,3,3],
[1/3,1/5,1/3,1/5,1/3,1,1],
[1/5,1/7,1/5,1/7,1/3,1,1]
])

BOOTING_MATRIX = np.array([
[1,3,3,1,5,5,5,1],
[1/3,1,1,1/3,3,3,3,1/3],
[1/3,1,1,1/3,3,3,3,1/3],
[1,3,3,1,5,5,5,1],
[1/5,1/3,1/3,1/5,1,3,3,1/5],
[1/5,1/3,1/3,1/5,1/3,1,1,1/5],
[1/5,1/3,1/3,1/5,1/3,1,1,1/5],
[1,3,3,1,5,5,5,1]
])

# ==========================================================
# MEMBERSHIP FUNCTIONS
# ==========================================================

def nitrogen_membership(n):
    if n < 150: return 0
    elif n < 280: return (n-150)/130
    return 1

def phosphorus_membership(p):
    if p < 10: return 0
    elif p < 20: return (p-10)/10
    return 1

def potassium_membership(k):
    if k < 110: return 0
    elif k < 150: return (k-110)/40
    return 1

def moisture_membership(m):
    if m < 10: return 0
    elif m < 20: return (m-10)/10
    return 1

def ph_membership(ph):
    if ph < 5.5: return 0
    elif ph < 6.0: return (ph-5.5)/0.5
    elif ph <= 7.5: return 1
    elif ph <= 8.0: return (8-ph)/0.5
    return 0

def oc_membership(oc):
    if oc < 0.3: return 0
    elif oc < 0.6: return (oc-0.3)/0.3
    return 1

def temp_membership(t):
    if t < 10: return 0
    elif t < 18: return (t-10)/8
    elif t <= 25: return 1
    return 0.5

def ndvi_membership(ndvi):
    if ndvi < 0.5: return 0
    elif ndvi < 0.7: return (ndvi-0.5)/0.2
    elif ndvi <= 0.9: return 1
    return 0.5

# ==========================================================
# CLASSIFICATION
# ==========================================================

def classify_score(score):
    if score >= 78: return "Excellent"
    elif score >= 77: return "Very Good"
    elif score >= 76: return "Good"
    elif score >= 75: return "Moderate"
    elif score >= 74: return "Poor"
    return "Very Poor"

def clean_location_name(name: str) -> str:
    if not name: return ""
    # Exact same logic as map.py for 100% matching
    s = name.strip().upper()
    s = s.replace('>', 'A').replace('<', 'A')
    s = s.replace('|', 'I').replace('\\', 'I')
    s = s.replace('@', 'U').replace('#', 'U')
    s = s.replace('&', 'AND')
    # Remove all non-alphanumeric for final matching key
    import re
    return re.sub(r'[^A-Z0-9]', '', s)

def _run_stage_engine(df: pd.DataFrame, stage: str) -> pd.DataFrame:
    """
    Runs Adarsh's engine for the given stage and returns a dataframe with:
    - SHS (numeric)
    - Category (derived locally for DB/backward compatibility; frontend can ignore)
    - Error_<stage> passthrough (if engine provided it)
    """
    engine = WheatSHSEngine(stage)
    out = engine.run_dataset(df)

    shs_col = f"SHS_{stage}"
    if shs_col not in out.columns:
        raise ValueError(f"Expected column '{shs_col}' from engine output")

    out["SHS"] = out[shs_col]
    out["Category"] = out["SHS"].apply(lambda x: classify_score(x) if pd.notna(x) else None)
    return out

def cleanup_old_records(db: Session, days: int = 7):
    """
    Deletes SHS records and their batches older than the specified number of days.
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    logger.info(f"Running database cleanup. Removing records older than {cutoff_date}")
    
    try:
        # Cleanup the Batch table (Cascade delete should handle SHS records)
        deleted_batches = db.query(UploadBatch).filter(UploadBatch.created_at < cutoff_date).delete()
        if deleted_batches > 0:
            logger.info(f"Cleaned up {deleted_batches} old upload batches (and their records)")
        
        # Cleanup unified table (redundant if cascade works, but safe to keep)
        deleted_unified = db.query(UploadedCSVData).filter(UploadedCSVData.created_at < cutoff_date).delete()
        if deleted_unified > 0:
            logger.info(f"Cleaned up {deleted_unified} old records from uploaded_csv_data")

        # Cleanup latlon_suitability (separate table)
        deleted_ll = db.query(LatLonSuitability).filter(LatLonSuitability.created_at < cutoff_date).delete()
        if deleted_ll > 0:
            logger.info(f"Cleaned up {deleted_ll} old records from latlon_suitability")
            
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Cleanup failed: {e}")

def _save_analysis_to_db(db: Session, processed_df: pd.DataFrame, stage: str, filename: str, default_state: str = None):
    """
    Helper to create a batch and save SHS records to the unified table.
    """
    # 1. Create the Batch (Folder)
    batch = UploadBatch(
        filename=filename,
        stage=stage.capitalize()
    )
    db.add(batch)
    db.flush() # Get the batch ID

    # 2. Save individual records to the UNIFIED table
    stored_count = 0
    for _, row in processed_df.iterrows():
        if pd.notna(row['SHS']):
            # Extract state/district from row with multiple candidate keys
            state_val = str(row.get('State', row.get('state', row.get('STATE_NAME', row.get('ST_NM', 'Unknown')))))
            if state_val == "Unknown" and default_state:
                state_val = default_state
                
            district_val = str(row.get('District', row.get('district', row.get('subdistrict', row.get('TEHSIL', 'Unknown')))))
            
            shs_record = UploadedCSVData(
                batch_id=batch.id,
                stage=stage.lower(),
                state=state_val,
                district=district_val,
                # Soil Parameters (Map standard keys from engine or CSV)
                nitrogen=float(row.get('N', 0)),
                phosphorus=float(row.get('P', 0)),
                potassium=float(row.get('K', 0)),
                moisture=float(row.get('Moisture', 0)),
                ph=float(row.get('pH', 0)),
                organic_carbon=float(row.get('OC', 0)),
                temperature=float(row.get('Temp', 0)),
                ndvi=float(row.get('NDVI', 0)),
                # Results
                shs_score=row['SHS'],
                shs_category=row.get('Category', classify_score(row['SHS'])),
            )
            db.add(shs_record)
            
            # --- ALSO Save to legacy tables for backward compatibility (Optional) ---
            if stage == "germination":
                Model = WheatGerminationSHS
            elif stage == "booting":
                Model = WheatBootingSHS
            else:
                Model = WheatRipeningSHS
                
            legacy_rec = Model(
                batch_id=batch.id,
                pixel_id=str(row.get('Pixel_ID', '')),
                district=district_val,
                state=state_val,
                shs=row['SHS'],
                category=row.get('Category', classify_score(row['SHS'])),
            )
            db.add(legacy_rec)
            # -------------------------------------------------------------------------
            
            stored_count += 1
    
    db.commit()
    logger.info(f"Saved {stored_count} records for batch: {filename} into unified table")
    return stored_count

# ==========================================================
# API ENDPOINTS
# ==========================================================

@router.post("/process-csv")
async def process_csv(
    file: UploadFile = File(...), 
    stage: str = Form("germination"), 
    state: str = Form(None),
    db: Session = Depends(get_db)
):
    # Automatically clean up records older than 7 days
    cleanup_old_records(db, days=7)
    
    if stage not in ["germination", "booting", "ripening"]:
        raise HTTPException(status_code=400, detail="Stage must be 'germination', 'booting', or 'ripening'")
    
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
    
    # Preserve original column order for CSV output
    original_columns = list(df.columns)

    # Filter for specific state if column exists (optional, keeping as a comment or removing)
    # if 'State' in df.columns:
    #     df = df[df['State'].str.lower() == 'maharashtra']
    
    if df.empty:
        raise HTTPException(status_code=400, detail="No data found in CSV")

    # Ripening and booting require NDVI (engine will validate)
    processed_df = _run_stage_engine(df, stage)
    
    # Generate Unique Filename with Timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_name = getattr(file, "filename", "uploaded_file.csv")
    name_parts = os.path.splitext(original_name)
    unique_filename = f"{name_parts[0]}_{timestamp}{name_parts[1]}"

    # ------------------------------------------------------------------
    # CSV OUTPUT
    # ------------------------------------------------------------------
    try:
        output_path = os.path.join(OUTPUTS_DIR, unique_filename)
        _write_standard_output_csv(processed_df, original_columns, stage, output_path)
    except Exception as e:
        logger.warning(f"Failed to write SHS output CSV: {e}")

    # ------------------------------------------------------------------
    # DB STORAGE (Batch System)
    # ------------------------------------------------------------------
    stored_count = _save_analysis_to_db(db, processed_df, stage, unique_filename, default_state=state)
    
    return {
        "message": f"Processed {len(processed_df)} rows, stored {stored_count} results",
        "batch_file": unique_filename
    }


@router.post("/process-csv-from-data")
def process_csv_from_data(
    filename: str,
    stage: str = "germination",
    db: Session = Depends(get_db),
):
    # Automatically clean up records older than 7 days
    cleanup_old_records(db, days=7)
    """
    NEW: Simple, no-UI pipeline.
    Reads a CSV from `shs-backend/app/Data/`, runs the requested stage model,
    writes to the same stage DB table, and generates the same output CSV in `app/outputs/`.

    This does NOT modify existing upload behavior.
    """
    if stage not in ["germination", "booting"]:
        if stage != "ripening":
            raise HTTPException(status_code=400, detail="stage must be 'germination', 'booting', or 'ripening'")

    csv_path = _safe_join_csv(DATA_DIR, filename)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")

    original_columns = list(df.columns)

    # Keep existing upload behavior: filter state if it exists (optional)
    # if "State" in df.columns:
    #     df = df[df["State"].astype(str).str.lower() == "maharashtra"]
    if df.empty:
        raise HTTPException(status_code=400, detail="No data found in CSV")

    processed_df = _run_stage_engine(df, stage)

    # Output CSV (same naming pattern as existing pipeline)
    try:
        if stage == "germination":
            output_filename = "germination_output_with_shs_avg_category.csv"
        elif stage == "booting":
            output_filename = "booting_output_with_shs_avg_category.csv"
        else:
            output_filename = "ripening_output_with_shs_avg_category.csv"
        output_path = os.path.join(OUTPUTS_DIR, output_filename)
        _write_standard_output_csv(processed_df, original_columns, stage, output_path)
    except Exception as e:
        logger.warning(f"Failed to write SHS output CSV for stage '{stage}': {e}")

    # DB insert (same as existing upload pipeline)
    if stage == "germination":
        Model = WheatGerminationSHS
    elif stage == "booting":
        Model = WheatBootingSHS
    else:
        Model = WheatRipeningSHS
    stored_count = 0
    for _, row in processed_df.iterrows():
        if pd.notna(row["SHS"]):
            rec = Model(
                pixel_id=str(row.get("Pixel_ID", "")),
                district=str(row.get("District", "")),
                state=str(row.get("State", "Unknown")),
                shs=row["SHS"],
                category=row["Category"],
            )
            db.add(rec)
            stored_count += 1
    db.commit()

    return {
        "message": "Processed CSV from app/Data and stored results",
        "filename": filename,
        "stage": stage,
        "rows": int(len(processed_df)),
        "stored": stored_count,
        "output_csv": os.path.join("app", "outputs", output_filename),
    }


# ==========================================================
# NEW: LAT/LON LOCAL-FILE PIPELINE (does not affect existing APIs)
# ==========================================================

@router.post("/process-latlon-local")
def process_latlon_local(
    filename: str = "synthetic_soil_data.csv",
    db: Session = Depends(get_db)
):
    # Automatically clean up records older than 7 days
    cleanup_old_records(db, days=7)
    """
    NEW: Reads a CSV from the shs-backend project root (local folder),
    runs BOTH germination and booting models, and stores per-point results
    into a separate table `latlon_suitability`.

    This endpoint does NOT modify or depend on the existing district-based tables.
    """
    # NEW: read from app/Data by default (simple upload-by-copy workflow)
    csv_path = _safe_join_csv(DATA_DIR, filename)

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail=f"CSV not found: {csv_path}")

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")

    original_columns = list(df.columns)

    required_cols = {"lat", "lon", "N", "P", "K", "Moisture", "pH", "OC", "Temp"}
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}. Found: {list(df.columns)}")

    # Booting/Ripening require NDVI. If absent, inject a demo default (only for this new pipeline).
    if "NDVI" not in df.columns:
        df["NDVI"] = DEFAULT_BOOTING_NDVI

    batch_id = str(uuid.uuid4())

    # Run germination
    germ_df = _run_stage_engine(df.copy(), "germination")

    # Run booting
    boot_df = _run_stage_engine(df.copy(), "booting")

    # Run ripening
    rip_df = _run_stage_engine(df.copy(), "ripening")

    stored = 0
    for idx in range(len(df)):
        row_in = df.iloc[idx]
        row_g = germ_df.iloc[idx]
        row_b = boot_df.iloc[idx]
        row_r = rip_df.iloc[idx]

        rec = LatLonSuitability(
            batch_id=batch_id,
            source_file=filename,
            lat=float(row_in["lat"]),
            lon=float(row_in["lon"]),
            n=float(row_in["N"]) if pd.notna(row_in["N"]) else None,
            p=float(row_in["P"]) if pd.notna(row_in["P"]) else None,
            k=float(row_in["K"]) if pd.notna(row_in["K"]) else None,
            moisture=float(row_in["Moisture"]) if pd.notna(row_in["Moisture"]) else None,
            ph=float(row_in["pH"]) if pd.notna(row_in["pH"]) else None,
            oc=float(row_in["OC"]) if pd.notna(row_in["OC"]) else None,
            temp=float(row_in["Temp"]) if pd.notna(row_in["Temp"]) else None,
            ndvi=float(row_in["NDVI"]) if pd.notna(row_in["NDVI"]) else None,
            germ_shs=float(row_g["SHS"]) if pd.notna(row_g.get("SHS")) else None,
            germ_category=str(row_g["Category"]) if pd.notna(row_g.get("Category")) else None,
            boot_shs=float(row_b["SHS"]) if pd.notna(row_b.get("SHS")) else None,
            boot_category=str(row_b["Category"]) if pd.notna(row_b.get("Category")) else None,
            rip_shs=float(row_r["SHS"]) if pd.notna(row_r.get("SHS")) else None,
            rip_category=str(row_r["Category"]) if pd.notna(row_r.get("Category")) else None,
        )
        db.add(rec)
        stored += 1

    db.commit()

    # NEW: output CSV for lat/lon pipeline (saved under app/outputs/)
    try:
        out_df = df.copy()
        out_df["germ_shs"] = germ_df["SHS"]
        out_df["germ_category"] = germ_df["Category"]
        out_df["boot_shs"] = boot_df["SHS"]
        out_df["boot_category"] = boot_df["Category"]
        out_df["rip_shs"] = rip_df["SHS"]
        out_df["rip_category"] = rip_df["Category"]

        out_path = os.path.join(OUTPUTS_DIR, "latlon_output_with_shs_avg_category.csv")
        # Keep input columns, plus new output columns
        final_cols = list(original_columns)
        for col in ["germ_shs", "germ_category", "boot_shs", "boot_category", "rip_shs", "rip_category"]:
            if col not in final_cols:
                final_cols.append(col)
        out_df.to_csv(out_path, index=False, columns=final_cols)
        logger.info(f"Written lat/lon output CSV to {out_path}")
    except Exception as e:
        logger.warning(f"Failed to write lat/lon output CSV: {e}")

    return {
        "message": "Lat/Lon suitability processed and stored",
        "filename": filename,
        "batch_id": batch_id,
        "rows": int(len(df)),
        "stored": stored,
        "ndvi_default_used": DEFAULT_BOOTING_NDVI if "NDVI" not in original_columns else None,
        "output_csv": os.path.join("app", "outputs", "latlon_output_with_shs_avg_category.csv"),
    }

def _aggregate_districts(Model, db: Session):
    # Attempt to pull from legacy tables first (backward compatibility)
    results = db.query(
        Model.district,
        func.avg(Model.shs).label('avg_shs')
    ).group_by(Model.district).all()

    districts = {}
    for row in results:
        if not row.district: continue
        categories = db.query(Model.category).filter(Model.district == row.district).all()
        category_counts = {}
        for cat in categories:
            category_counts[cat[0]] = category_counts.get(cat[0], 0) + 1
        most_common = max(category_counts, key=category_counts.get) if category_counts else "Fair"
        districts[row.district.upper()] = {"avg_shs": round(row.avg_shs, 2), "category": most_common}
    
    # Enrich with NEW LatLonSuitability data if available
    # We map 'germination' -> stage='Germination', etc.
    stage_map = {
        'WheatGerminationSHS': 'Germination',
        'WheatBootingSHS': 'Booting',
        'WheatRipeningSHS': 'Ripening'
    }
    stage = stage_map.get(Model.__name__, 'Germination')
    
    extra_results = db.query(
        LatLonSuitability.district_name,
        func.avg(LatLonSuitability.shs_score).label('avg_shs')
    ).filter(LatLonSuitability.stage == stage).group_by(LatLonSuitability.district_name).all()
    
    for row in extra_results:
        if not row.district_name: continue
        d_name = row.district_name.upper()
        # Only add if not already in legacy or if legacy was empty
        if d_name not in districts:
            # Get most common category for this district/stage
            cat_res = db.query(LatLonSuitability.shs_category).filter(
                LatLonSuitability.district_name == row.district_name,
                LatLonSuitability.stage == stage
            ).all()
            cats = [c[0] for c in cat_res if c[0]]
            most_common = max(set(cats), key=cats.count) if cats else "Fair"
            districts[d_name] = {"avg_shs": round(row.avg_shs, 2), "category": most_common}

    return districts

def _aggregate_subdistricts(stage: str, db: Session):
    try:
        from app.models import Village, SoilSample, SoilHealthScore, District
        
        # USE ONLY STANDARD TABLES (District-Level Spread for Full Coverage)
        # We join Village -> SoilSample directly since village_id is populated
        query = db.query(
            Village.name.label("location_name"),
            func.avg(SoilHealthScore.score_value).label("avg_shs"),
            func.count(SoilHealthScore.soil_health_score_id).label("count")
        ).join(
            SoilSample, Village.village_id == SoilSample.village_id
        ).join(
            SoilHealthScore, SoilSample.soil_sample_id == SoilHealthScore.soil_sample_id
        ).filter(
            SoilSample.stage.ilike(stage)
        ).group_by(Village.name).all()
        
        # FALLBACK: If the direct join is too strict, use a more inclusive query
        if not query:
            # Get district averages first
            district_avgs = db.query(
                District.district_id,
                func.avg(SoilHealthScore.score_value).label("avg_shs")
            ).join(
                Village, District.district_id == Village.district_id
            ).join(
                SoilSample, Village.village_id == SoilSample.village_id
            ).join(
                SoilHealthScore, SoilSample.soil_sample_id == SoilHealthScore.soil_sample_id
            ).filter(
                SoilSample.stage.ilike(stage)
            ).group_by(District.district_id).subquery()

            # Map them back to all villages in those districts
            query = db.query(
                Village.name.label("location_name"),
                district_avgs.c.avg_shs.label("avg_shs"),
                func.count(Village.village_id).label("count")
            ).join(
                District, Village.district_id == District.district_id
            ).join(
                district_avgs, District.district_id == district_avgs.c.district_id
            ).group_by(Village.name, district_avgs.c.avg_shs).all()

        subdistricts = {}
        for r in query:
            clean_name = clean_location_name(r.location_name)
            subdistricts[clean_name] = {
                "avg_shs": round(r.avg_shs, 2),
                "category": classify_score(r.avg_shs),
                "data_points": r.count
            }
                
        return subdistricts
    except Exception as e:
        print(f"CRITICAL ERROR in subdistrict aggregation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/districts")
def get_germination_districts(db: Session = Depends(get_db)):
    return _aggregate_districts(WheatGerminationSHS, db)


@router.get("/districts/booting")
def get_booting_districts(db: Session = Depends(get_db)):
    return _aggregate_districts(WheatBootingSHS, db)


@router.get("/districts/ripening")
def get_ripening_districts(db: Session = Depends(get_db)):
    return _aggregate_districts(WheatRipeningSHS, db)

@router.get("/subdistricts")
def get_germination_subdistricts(db: Session = Depends(get_db)):
    return _aggregate_subdistricts("Germination", db)


@router.get("/shs-map-data")
def get_shs_map_data(stage: str, state: str = None, db: Session = Depends(get_db)):
    """
    Returns aggregated district-level SHS data filtered by stage and state.
    """
    query = db.query(
        UploadedCSVData.district,
        func.avg(UploadedCSVData.shs_score).label('avg_shs'),
        func.count(UploadedCSVData.id).label('data_points')
    ).filter(UploadedCSVData.stage == stage.lower())
    
    if state:
        query = query.filter(UploadedCSVData.state.ilike(state))
        
    results = query.group_by(UploadedCSVData.district).all()
    
    districts = {}
    for row in results:
        if not row.district: continue
        # Get most common category for this district/stage
        cat_query = db.query(UploadedCSVData.shs_category).filter(
            UploadedCSVData.district == row.district,
            UploadedCSVData.stage == stage.lower()
        )
        if state:
            cat_query = cat_query.filter(UploadedCSVData.state.ilike(state))
        
        cats = [c[0] for c in cat_query.all() if c[0]]
        most_common = max(set(cats), key=cats.count) if cats else classify_score(row.avg_shs)
        
        districts[row.district.upper()] = {
            "avg_shs": round(row.avg_shs, 2),
            "category": most_common,
            "data_points": row.data_points
        }
    
    return districts

@router.get("/export-shs-csv")
def export_shs_csv(stage: str, state: str = None, db: Session = Depends(get_db)):
    """
    Exports filtered SHS data to a CSV file.
    """
    query = db.query(UploadedCSVData).filter(UploadedCSVData.stage == stage.lower())
    if state:
        query = query.filter(UploadedCSVData.state.ilike(state))
        
    records = query.order_by(UploadedCSVData.created_at.desc()).all()
    if not records:
        raise HTTPException(status_code=404, detail="No data found for the selected filters.")
    
    # Convert to list of dicts for pandas
    data = []
    for r in records:
        data.append({
            "Stage": r.stage,
            "State": r.state,
            "District": r.district,
            "Nitrogen": r.nitrogen,
            "Phosphorus": r.phosphorus,
            "Potassium": r.potassium,
            "Moisture": r.moisture,
            "pH": r.ph,
            "OC": r.organic_carbon,
            "Temperature": r.temperature,
            "NDVI": r.ndvi,
            "SHS_Score": r.shs_score,
            "Category": r.shs_category,
            "Created_At": r.created_at
        })
    
    df = pd.DataFrame(data)
    
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    filename = f"shs_data_{stage}_{state if state else 'all'}_{datetime.now().strftime('%Y%m%d')}.csv"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    
    return response


@router.get("/subdistricts/booting")
def get_booting_subdistricts(db: Session = Depends(get_db)):
    return _aggregate_subdistricts("Booting", db)


@router.get("/subdistricts/ripening")
def get_ripening_subdistricts(db: Session = Depends(get_db)):
    return _aggregate_subdistricts("Ripening", db)


@router.post("/upload-suitability")
async def upload_suitability(
    file: UploadFile = File(...), 
    stage: str = Form("germination"),
    state: str = Form(None)
):
    try:
        # Read file into memory
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        # Standardize column names for the engine
        # Map various spellings to standard keys
        col_map = {
            'N': 'N', 'NITROGEN': 'N', 'n': 'N',
            'P': 'P', 'PHOSPHORUS': 'P', 'p': 'P',
            'K': 'K', 'POTASSIUM': 'K', 'k': 'K',
            'PH': 'pH', 'ph': 'pH', 'Soil pH': 'pH',
            'MOISTURE': 'Moisture', 'moisture': 'Moisture',
            'OC': 'OC', 'ORGANIC CARBON': 'OC', 'oc': 'OC',
            'TEMP': 'Temp', 'TEMPERATURE': 'Temp', 'temp': 'Temp',
            'NDVI': 'NDVI', 'ndvi': 'NDVI',
            'STATE': 'State', 'state': 'State', 'ST_NM': 'State', 'STATE_NAME': 'State',
            'DISTRICT': 'district', 'District': 'district', 'DIST': 'district', 'DTNAME': 'district',
            'SUBDISTRICT': 'subdistrict', 'Subdistrict': 'subdistrict', 'TEHSIL': 'subdistrict', 'village': 'subdistrict'
        }
        
        # Rename columns if found
        new_cols = {}
        original_has_district = False
        for c in df.columns:
            clean_col = c.strip().upper()
            if clean_col in ['DISTRICT', 'DIST', 'DTNAME']:
                original_has_district = True
            
            for k, v in col_map.items():
                if clean_col == k.upper():
                    new_cols[c] = v
        
        df.rename(columns=new_cols, inplace=True)

        # Ensure we have a location column (prioritize subdistrict, then district)
        if 'subdistrict' not in df.columns and 'district' in df.columns:
            df.rename(columns={'district': 'subdistrict'}, inplace=True)
            original_has_district = True
        
        if 'subdistrict' not in df.columns:
             # Final Fallback: look for common location-like column names manually
             location_candidates = ['DISTRICT', 'DIST', 'DTNAME', 'SUBDISTRICT', 'TEHSIL', 'VILLAGE', 'LOCATION']
             found = False
             for c in df.columns:
                 if c.strip().upper() in location_candidates:
                     df.rename(columns={c: 'subdistrict'}, inplace=True)
                     if 'DIST' in c.strip().upper(): original_has_district = True
                     found = True
                     break
             
             if not found:
                 # If still not found, try the first string column that ISN'T 'State' or 'Category'
                 str_cols = [c for c in df.select_dtypes(include=['object']).columns if c.lower() not in ['state', 'category', 'shs_category']]
                 if len(str_cols) > 0:
                     df.rename(columns={str_cols[0]: 'subdistrict'}, inplace=True)
                 else:
                     raise HTTPException(status_code=400, detail="Could not find a location column (District/Subdistrict) in the file.")

        # Run SHS Engine
        engine = WheatSHSEngine(stage)
        required = engine.required_fields()
        
        # Fill missing numeric values with mean
        for col in required:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                df[col] = df[col].fillna(df[col].mean() if not df[col].isna().all() else 0)
            else:
                df[col] = 0

        # Predict SHS
        results = []
        for _, row in df.iterrows():
            try:
                p = engine.predict(row.to_dict())
                results.append(p['SHS'])
            except:
                results.append(None)
        
        df['SHS'] = results
        df['Category'] = df['SHS'].apply(lambda x: classify_score(x) if pd.notna(x) else None)
        df['avg_shs'] = df['SHS']
        
        # ------------------------------------------------------------------
        # NEW: SAVE TO DATABASE (Sync with main pipeline)
        # ------------------------------------------------------------------
        db = next(get_db()) # Manual session for this endpoint
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = getattr(file, "filename", "ui_upload.csv")
        name_parts = os.path.splitext(original_name)
        unique_filename = f"{name_parts[0]}_{timestamp}{name_parts[1]}"
        
        _save_analysis_to_db(db, df, stage, unique_filename, default_state=state)
        # ------------------------------------------------------------------

        # Aggregate by Location for Frontend
        agg = df.groupby('subdistrict')['SHS'].mean().dropna().to_dict()
        
        # Format for frontend
        final_data = {}
        for k, v in agg.items():
            clean_name = re.sub(r'[^A-Z0-9]', '', str(k).strip().upper())
            final_data[clean_name] = {
                "avg_shs": round(float(v), 2),
                "category": "Analyzed",
                "data_points": int(df[df['subdistrict'] == k].shape[0])
            }
            
        return {
            "type": "district_upload" if original_has_district else "subdistrict_upload",
            "data": final_data
        }

    except Exception as e:
        logger.error(f"Upload Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
