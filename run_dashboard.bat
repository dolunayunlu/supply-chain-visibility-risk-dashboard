@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo Supply Chain Visibility and Risk Platform
echo ========================================
echo.

echo Checking Python installation...
where python >nul 2>nul

if errorlevel 1 (
    echo Python is not installed or not added to PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo Python found.
echo.

if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Creating venv...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

echo Activating virtual environment...
call "venv\Scripts\activate.bat"

echo.
echo Installing required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
if not exist "data\processed\orders_clean.csv" (
    echo Processed data files not found.
    echo Running data processing script...
    python process_data.py
    echo Data processing completed.
    echo.
) else (
    echo Processed data files found.
)

echo.
echo Starting Streamlit dashboard...
echo.
python -m streamlit run Overview.py

pause