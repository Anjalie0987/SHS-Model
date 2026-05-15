from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url).execution_options(isolation_level="AUTOCOMMIT")

with engine.connect() as conn:
    tables_to_drop = [
        'soil_score_component',
        'soil_parameter_value',
        'latlon_suitability',
        'weather_data',
        'soil_sample',
        'soil_health_score',
        'farm_crop',
        'crop_recommendation',
        'farm',
        'village',
        'district_soil_summary',
        'district',
        'state',
        'soil_parameter_master',
        'score_model',
        'farmer',
        'crop_master'
    ]
    
    for t in tables_to_drop:
        try:
            conn.execute(text(f"DROP TABLE IF EXISTS {t} CASCADE;"))
            print(f"Dropped {t}")
        except Exception as e:
            print(f"Failed to drop {t}: {e}")
