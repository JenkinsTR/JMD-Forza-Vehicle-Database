@echo off
set SCRIPT_PATH="forza_vehicle_db.py"

python %SCRIPT_PATH%
if %ERRORLEVEL% NEQ 0 (
    echo There was an error during the compare process.
    pause
    exit /b %ERRORLEVEL%
)

echo Comparison completed successfully.
pause
