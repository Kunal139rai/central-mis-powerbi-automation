@echo off
title Central MIS - Director Control Room
echo ===================================================
echo  Starting Director Central MIS Web App...
echo ===================================================
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on your PATH.
    echo Install Python from https://www.python.org/downloads/ and make sure
    echo "Add python.exe to PATH" is checked during setup, then try again.
    pause
    exit /b 1
)

python -c "import streamlit" >nul 2>nul
if errorlevel 1 (
    echo Required packages are not installed yet. Installing now from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Package installation failed. See the messages above.
        pause
        exit /b 1
    )
)

echo Launching app at http://localhost:8501 ...
python -m streamlit run app.py --server.port 8501 --server.headless false
pause
