import psycopg2
conn=psycopg2.connect('postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db')
cur=conn.cursor()

redundant_tables = [
    'old_farmers', 'old_farmer_new', 'old_crop_master', 'old_farm_crop',
    'old_latlon_suitability', 'old_score_model', 'old_soil_health_score',
    'old_soil_score_component', 'old_soil_parameter_value', 'old_weather_data',
    'old_crop_recommendation', 'old_district_soil_summary', 'wheat_shs',
    'wheat_shs_germination', 'wheat_shs_booting', 'wheat_shs_ripening',
    'temp_soil_data', 'temp_shs_data', 'temp_tehsil_boundary',
    'soil_germination_data', 'soil_crop_data', 'latlon_suitability_legacy'
]

print(f"Starting wipe of {len(redundant_tables)} redundant tables...")

for table in redundant_tables:
    try:
        cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        print(f"  Dropped: {table}")
    except Exception as e:
        print(f"  Error dropping {table}: {e}")
        conn.rollback()

conn.commit()
print("\nFinal Cleanup Complete! Your database is now 100% clean.")
conn.close()
