from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url)

with engine.connect() as conn:
    tables_to_rename = {
        'latlon_suitability': 'old_latlon_suitability',
        'farmers': 'old_farmers',
        'soil_samples': 'old_soil_samples',
        'state': 'old_state',
        'district': 'old_district',
        'village': 'old_village',
        'farmer': 'old_farmer_new', # renaming the one created by create_all
        'farm': 'old_farm',
        'crop_master': 'old_crop_master',
        'farm_crop': 'old_farm_crop',
        'soil_sample': 'old_soil_sample_new',
        'soil_parameter_master': 'old_soil_parameter_master',
        'soil_parameter_value': 'old_soil_parameter_value',
        'score_model': 'old_score_model',
        'soil_health_score': 'old_soil_health_score',
        'soil_score_component': 'old_soil_score_component',
        'weather_data': 'old_weather_data',
        'crop_recommendation': 'old_crop_recommendation',
        'district_soil_summary': 'old_district_soil_summary'
    }
    
    for old, new in tables_to_rename.items():
        try:
            conn.execute(text(f"ALTER TABLE {old} RENAME TO {new}"))
            print(f"Renamed {old} to {new}")
        except Exception as e:
            print(f"Failed to rename {old}: {e}")
    conn.commit()
