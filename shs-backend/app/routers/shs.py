from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import numpy as np
import logging
import os
import uuid
from app.database import get_db
from app.models import WheatGerminationSHS, WheatBootingSHS, WheatRipeningSHS, LatLonSuitability
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
    if score >= 75:
        return "Good"
    elif score >= 50:
        return "Fair"
    return "Poor"

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

# ==========================================================
# API ENDPOINTS
# ==========================================================

@router.post("/process-csv")
async def process_csv(file: UploadFile = File(...), stage: str = "germination", db: Session = Depends(get_db)):
    if stage not in ["germination", "booting", "ripening"]:
        raise HTTPException(status_code=400, detail="Stage must be 'germination', 'booting', or 'ripening'")
    
    try:
        df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
    
    # Preserve original column order for CSV output
    original_columns = list(df.columns)

    # Filter for Maharashtra
    if 'State' in df.columns:
        df = df[df['State'].str.lower() == 'maharashtra']
    
    if df.empty:
        raise HTTPException(status_code=400, detail="No data for Maharashtra found")

    # Ripening and booting require NDVI (engine will validate)
    processed_df = _run_stage_engine(df, stage)
    
    # ------------------------------------------------------------------
    # CSV OUTPUT (non-invasive: DB write logic remains unchanged)
    # ------------------------------------------------------------------
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

    # Store results in DB (separate tables per stage)
    if stage == "germination":
        Model = WheatGerminationSHS
    elif stage == "booting":
        Model = WheatBootingSHS
    else:
        Model = WheatRipeningSHS

    stored_count = 0
    for _, row in processed_df.iterrows():
        if pd.notna(row['SHS']):
            shs_record = Model(
                pixel_id=str(row.get('Pixel_ID', '')),
                district=str(row.get('District', '')),
                state='Maharashtra',
                shs=row['SHS'],
                category=row['Category'],
            )
            db.add(shs_record)
            stored_count += 1
    db.commit()
    
    return {"message": f"Processed {len(processed_df)} rows, stored {stored_count} results"}


@router.post("/process-csv-from-data")
def process_csv_from_data(
    filename: str,
    stage: str = "germination",
    db: Session = Depends(get_db),
):
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

    # Keep existing upload behavior: filter Maharashtra if State exists
    if "State" in df.columns:
        df = df[df["State"].astype(str).str.lower() == "maharashtra"]
    if df.empty:
        raise HTTPException(status_code=400, detail="No data for Maharashtra found")

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
                state="Maharashtra",
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
    results = db.query(
        Model.district,
        func.avg(Model.shs).label('avg_shs')
    ).filter(Model.state == 'Maharashtra').group_by(Model.district).all()

    districts = {}
    for row in results:
        categories = db.query(Model.category).filter(
            Model.district == row.district,
            Model.state == 'Maharashtra'
        ).all()
        category_counts = {}
        for cat in categories:
            category_counts[cat[0]] = category_counts.get(cat[0], 0) + 1
        most_common = max(category_counts, key=category_counts.get) if category_counts else None
        districts[row.district] = {"avg_shs": round(row.avg_shs, 2), "category": most_common}
    return districts


@router.get("/districts")
def get_germination_districts(db: Session = Depends(get_db)):
    """
    Aggregated SHS per district for the germination stage.
    """
    return _aggregate_districts(WheatGerminationSHS, db)


@router.get("/districts/booting")
def get_booting_districts(db: Session = Depends(get_db)):
    """
    Aggregated SHS per district for the booting stage.
    """
    return _aggregate_districts(WheatBootingSHS, db)


@router.get("/districts/ripening")
def get_ripening_districts(db: Session = Depends(get_db)):
    """
    Aggregated SHS per district for the ripening stage.
    """
    return _aggregate_districts(WheatRipeningSHS, db)