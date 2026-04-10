@echo off
echo ===================================================
echo Starting BhoomiSanket Main Backend on Port 8000
echo ===================================================
start "Main Backend" cmd /k "cd /d D:\CROP2\CROP2\BhoomiSanket\backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

echo ===================================================
echo Starting BhoomiSanket SHS Backend on Port 8001
echo ===================================================
start "SHS Backend" cmd /k "cd /d D:\CROP2\CROP2\shs-backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8001"

echo ===================================================
echo Starting React Frontend
echo ===================================================
start "Frontend" cmd /k "cd /d D:\CROP2\CROP2\BhoomiSanket\frontend && (if not exist node_modules echo Installing dependencies... ^& call npm install) & npm start"

echo.
echo All services have been launched in separate terminal windows.
echo Let the processes a moment to fully initialize.
echo.
pause
