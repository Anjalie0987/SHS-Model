from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    indexes_to_rename = {
        'idx_district_soil_summary_geom': 'old_idx_district_soil_summary_geom',
        'idx_farm_geom': 'old_idx_farm_geom',
        'idx_soil_sample_geom': 'old_idx_soil_sample_geom',
        'idx_latlon_suitability_geom': 'old_idx_latlon_suitability_geom'
    }
    
    for old, new in indexes_to_rename.items():
        try:
            conn.execute(text(f"ALTER INDEX {old} RENAME TO {new}"))
            print(f"Renamed {old} to {new}")
        except Exception as e:
            print(f"Failed to rename {old}: {e}")
    conn.commit()
