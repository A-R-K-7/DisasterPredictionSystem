@echo off
echo Starting Disaster Prediction System...
echo.
echo Press Ctrl+C to stop the system
echo.

:: Start Redis if not already running (assuming Redis is installed locally)
echo Checking Redis...
redis-cli ping > NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Starting Redis server...
    start /b redis-server
    timeout /t 2 > NUL
) else (
    echo Redis is already running.
)

:: Start the Celery worker and beat using our custom script
echo.
echo Starting Celery processes...
python run_celery_windows.py

:: If the user stops the Celery processes, we'll continue here
echo.
echo Celery processes have been stopped.
echo You can close this window now.
pause 