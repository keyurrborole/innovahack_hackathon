@echo off
REM ============================================================
REM  Model X — GNN 3D Pipeline — 1-Click Launch Script
REM  Starts both FastAPI GNN backend and Vite React frontend
REM ============================================================
title Model X - GNN 3D Pipeline Launcher
color 0A

echo.
echo  ================================================================
echo   Model X - GNN-Driven 3D Pipeline — Windows Launcher
echo   Phase M0/M1 MVP
echo  ================================================================
echo.

REM --- Check Python ---
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found.

REM --- Check Node.js ---
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH.
    echo         Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js found.

REM --- Check npm ---
where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] npm is not installed or not in PATH.
    pause
    exit /b 1
)
echo [OK] npm found.

echo.
echo --------------------------------------------------
echo  Step 1: Setting up Python virtual environment...
echo --------------------------------------------------

if not exist "backend_gnn\venv" (
    echo [INFO] Creating virtual environment in backend_gnn\venv...
    python -m venv backend_gnn\venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)

echo.
echo --------------------------------------------------
echo  Step 2: Installing backend dependencies...
echo --------------------------------------------------

call backend_gnn\venv\Scripts\activate.bat
pip install -r backend_gnn\requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Some backend dependencies may have failed to install.
    echo          The server may still work if core packages are present.
)
echo [OK] Backend dependencies installed.
call deactivate

echo.
echo --------------------------------------------------
echo  Step 3: Installing frontend dependencies...
echo --------------------------------------------------

call npm install --silent
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install frontend dependencies.
    pause
    exit /b 1
)
echo [OK] Frontend dependencies installed.

echo.
echo --------------------------------------------------
echo  Step 4: Creating local S3 mock directories...
echo --------------------------------------------------

if not exist "local_s3_mock\raw_assets" mkdir "local_s3_mock\raw_assets"
if not exist "local_s3_mock\processed_assets" mkdir "local_s3_mock\processed_assets"
if not exist "local_s3_mock\graph_datasets" mkdir "local_s3_mock\graph_datasets"
echo [OK] Local S3 mock directories ready.

echo.
echo  ================================================================
echo   Launching servers...
echo  ================================================================
echo.

REM --- Launch FastAPI GNN Backend (port 8001) ---
echo [INFO] Starting FastAPI GNN backend on http://localhost:8001 ...
start "Model X - GNN Backend (port 8001)" cmd /k "cd /d %~dp0 && python -m uvicorn backend_gnn.main:app --reload --host 0.0.0.0 --port 8001"

REM --- Small delay to stagger the starts ---
timeout /t 2 /nobreak >nul

REM --- Launch Vite React Frontend (port 5173) ---
echo [INFO] Starting Vite React frontend on http://localhost:5173 ...
start "Model X - React Frontend (port 5173)" cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo  ================================================================
echo   Both servers are starting in separate windows!
echo.
echo   Frontend:  http://localhost:5173/cryptoflow/gnn-viewer
echo   Backend:   http://localhost:8001/health
echo   API Docs:  http://localhost:8001/docs
echo   (Frontend proxies /gnn-api/* -> backend via Vite)
echo  ================================================================
echo.
echo  Press any key to close this launcher window...
echo  (The server windows will keep running)
pause >nul
