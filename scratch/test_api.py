import requests

BASE_URL = "http://127.0.0.1:8000/farm-analysis" # Assuming standard port

def test_api():
    try:
        # 1. Test /locations
        print("Testing /locations...")
        res = requests.get(f"{BASE_URL}/locations")
        if res.status_code == 200:
            data = res.json()
            print(f"Fetched {len(data['states'])} states.")
            if data['states']:
                s = data['states'][0]
                print(f"Sample State: {s['name']} (Code: {s['code']})")
                districts = data['districts'].get(str(s['code']), [])
                print(f"Districts in {s['name']}: {len(districts)}")
                
                # 2. Test /subdistricts for Sabar Kantha
                print("\nTesting /subdistricts for Sabar Kantha (24, 458) with q=talod...")
                res_sub = requests.get(f"{BASE_URL}/subdistricts?state_code=24&district_code=458&q=talod")
                if res_sub.status_code == 200:
                    subs = res_sub.json()
                    print(f"Fetched {len(subs)} subdistricts.")
                    for s in subs:
                        print(f" - {s['name']} (ID: {s['id']})")
                else:
                    print(f"Subdistricts failed: {res_sub.status_code}")
                    print(res_sub.text)
        else:
            print(f"Locations failed: {res.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
