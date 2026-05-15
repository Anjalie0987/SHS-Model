import requests
import time

URL = "http://localhost:8000/api/analyze-soil"
PAYLOAD = {
    "farmer_name": "Test Farmer",
    "mobile": "1234567890",
    "field_id": "F1",
    "state": "Punjab",
    "district": "Amritsar",
    "village": "Test Village",
    "crop_type": "Wheat",
    "season": "Rabi",
    "field_area": 5.0,
    "nitrogen": 160.0,
    "phosphorus": 15.0,
    "potassium": 120.0,
    "ph": 6.5,
    "moisture": 22.0,
    "organic_carbon": 0.6,
    "temperature": 24.0,
    "ndvi": 0.8,
    "coordinates": [31.634, 74.872] # [lat, lon]
}

def verify():
    print("Submitting soil analysis request...")
    try:
        response = requests.post(URL, json=PAYLOAD)
        print(f"Response: {response.status_code} - {response.json()}")
        
        if response.status_code == 200:
            print("Waiting for background task to complete...")
            time.sleep(5) # Wait 5 seconds for background task
            
            # Check database for cache entries
            from sqlalchemy import create_engine, text
            engine = create_engine("postgresql://postgres:post123@127.0.0.1:5433/bhoomisanket_db")
            with engine.connect() as conn:
                res = conn.execute(text("SELECT stage, shs_score, shs_category FROM latlon_suitability WHERE district_name = 'AMRITSAR'"))
                rows = res.fetchall()
                print(f"Found {len(rows)} cache entries in latlon_suitability:")
                for r in rows:
                    print(f" - Stage: {r[0]}, Score: {r[1]}, Category: {r[2]}")
                    
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify()
