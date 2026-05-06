cd# Step-by-step execution commands (run yourself)

**Assumptions:**
* Workspace root: `C:\Users\sujan\Desktop\CROP2`
* Ports:
    * Main backend: `8000`
    * SHS backend: `8001`
    * Frontend: `3000`
* CSVs are placed in: `shs-backend\app\Data\`

---

### 0) Start Postgres (manual)
Make sure PostgreSQL is running and your DB exists:
* DB: `bhoomisanket_db`
* PostGIS enabled (as in `BhoomiSanket\DATABASE_SETUP.md`)
* `.env` files have correct `DATABASE_URL`:
    * `BhoomiSanket\backend\.env`
    * `shs-backend\.env`

---

### 1) Start MAIN backend (8000)
```powershell
cd C:\Users\sujan\Desktop\CROP2\BhoomiSanket\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
**Verify:**
```powershell
irm http://localhost:8000/ | ConvertTo-Json -Depth 3
irm http://localhost:8000/map/state | Select-Object -First 1 | Out-Null; "map/state OK"
```

---

### 2) Start SHS backend (8001)
Open a new terminal:
```powershell
cd C:\Users\sujan\Desktop\CROP2\shs-backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```
**Verify:**
```powershell
irm http://localhost:8001/ | ConvertTo-Json -Depth 3
```

---

### 3) (Simple pipeline) Process CSVs from shs-backend\app\Data\ (no UI upload)

**3A) Germination (district CSV)**
```powershell
irm "http://localhost:8001/api/process-csv-from-data?filename=Maharashtra_Germination_8000_NoSpatial.csv&stage=germination" -Method Post | ConvertTo-Json -Depth 5
```

**3B) Booting (district CSV)**
```powershell
irm "http://localhost:8001/api/process-csv-from-data?filename=Maharashtra_Booting_8000_NoSpatial.csv&stage=booting" -Method Post | ConvertTo-Json -Depth 5
```

**3C) Ripening (district CSV)** - *NEW STAGE*
```powershell
irm "http://localhost:8001/api/process-csv-from-data?filename=Maharashtra_Ripening_8000_NoSpatial.csv&stage=ripening" -Method Post | ConvertTo-Json -Depth 5
```

**Verify aggregates:**
```powershell
irm http://localhost:8001/api/districts | ConvertTo-Json -Depth 5
irm http://localhost:8001/api/districts/booting | ConvertTo-Json -Depth 5
irm http://localhost:8001/api/districts/ripening | ConvertTo-Json -Depth 5
```

**Verify output CSVs exist:**
```powershell
ls C:\Users\sujan\Desktop\CROP2\shs-backend\app\outputs
```

---

### 4) (Lat/Lon pipeline) Process the lat/lon CSV from app\Data\
```powershell
irm "http://localhost:8001/api/process-latlon-local?filename=synthetic_soil_data.csv" -Method Post | ConvertTo-Json -Depth 5
```

**Verify the main backend can fetch the stored points:**
```powershell
irm "http://localhost:8000/map/suitability/points?limit=5" | ConvertTo-Json -Depth 10
```

**Verify lat/lon output CSV exists:**
```powershell
ls C:\Users\sujan\Desktop\CROP2\shs-backend\app\outputs
```
You should see:
* `latlon_output_with_shs_avg_category.csv`

---

### 5) Start Frontend (3000)
Open a new terminal:
```powershell
cd C:\Users\sujan\Desktop\CROP2\BhoomiSanket\frontend
npm install
npm start
```

**Open in browser:**
* `http://localhost:3000/germination-suitability`

**What to toggle in UI:**
* **District SHS Choropleths**
  * Germination SHS Choropleth
  * Booting SHS Choropleth
  * Ripening SHS Choropleth
* **Lat/Lon Suitability**
  * Germination Points / Booting Points / Ripening Points
  * Germination Heatmap / Booting Heatmap / Ripening Heatmap
