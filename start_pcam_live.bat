@echo off
title NEOMA P-CAM Integrated Launcher
cd /d "C:\Users\shs15\pcam-live"

echo ==============================================================================
echo  NEOMA P-CAM & Physical AI Neoma Cluster Launcher
echo  Directory: C:\Users\shs15\pcam-live
echo ==============================================================================

echo [1/3] Starting 24h Main Server Gateway (COM3, Port 8000)...
start "P-CAM Gateway (COM3)" python pcam_rapidapi_gateway.py

timeout /t 2 /nobreak > nul

echo [2/3] Starting Neoma Hardware Bridge (COM6, Port 8002)...
start "P-CAM Accelerator Bridge (COM6)" python pcam_bridge.py

timeout /t 2 /nobreak > nul

echo [3/3] Starting Neoma Control Dashboard (Port 8501)...
start "Neoma Web Dashboard" python -m streamlit run neoma_web_app.py --server.headless false

echo ==============================================================================
echo  All systems launched successfully inside pcam-live enclave.
echo ==============================================================================
