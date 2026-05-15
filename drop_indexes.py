from sqlalchemy import create_engine, text

db_url = "postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db"
engine = create_engine(db_url).execution_options(isolation_level="AUTOCOMMIT")

with engine.connect() as conn:
    indexes_to_drop = [
        'idx_district_soil_summary_geom',
        'idx_farm_geom',
        'idx_soil_sample_geom',
        'idx_latlon_suitability_geom',
        'ix_country_country_id',
        'ix_state_state_id',
        'ix_district_district_id',
        'ix_village_village_id',
        'ix_farmer_farmer_id',
        'ix_farmer_mobile',
        'ix_crop_master_crop_id',
        'ix_farm_farm_id',
        'ix_soil_sample_soil_sample_id',
        'ix_soil_parameter_master_parameter_id',
        'ix_soil_parameter_value_param_value_id',
        'ix_score_model_score_model_id',
        'ix_soil_health_score_soil_health_score_id',
        'ix_soil_score_component_soil_score_component_id',
        'ix_weather_data_weather_id',
        'ix_crop_recommendation_recommendation_id',
        'ix_latlon_suitability_id',
        'ix_farm_crop_farm_crop_id'
    ]
    
    for idx in indexes_to_drop:
        try:
            conn.execute(text(f"DROP INDEX IF EXISTS {idx}"))
            print(f"Dropped {idx}")
        except Exception as e:
            print(f"Failed to drop {idx}: {e}")
