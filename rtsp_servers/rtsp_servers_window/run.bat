@echo off
echo ========== RTSP Server System ==========

:: Move to the project directory
cd rtsp_servers

:: Activate the virtual environment
if exist venv (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run install.bat first.
    pause
    exit
)

:: Force-kill any existing Python and Node processes (optional, uncomment if needed)
:: taskkill /F /IM python.exe /T > nul 2>&1
:: taskkill /F /IM node.exe /T > nul 2>&1

:: Start backend server in the background
echo Starting backend server on port 8000...
start /b cmd /c "cd %cd% && call venv\Scripts\activate.bat && python backend.py > backend_log.txt 2>&1"

:: Wait for backend to initialize
echo Waiting for backend to initialize...
timeout /t 3 /nobreak > nul

:: Start frontend application in the background
echo Starting frontend application on port 3000...
start /b cmd /c "cd %cd%\rtsp-manager && npm run dev > frontend_log.txt 2>&1"

:: Wait for frontend to initialize
echo Waiting for frontend to initialize...
timeout /t 10 /nobreak > nul

:: Check if servers are running
echo Checking if servers are running properly...

:: Check backend (port 8000)
curl -s http://localhost:8000 > nul
if %errorlevel% neq 0 (
    echo WARNING: Backend might not be running correctly on port 8000.
    echo Check backend_log.txt for errors.
) else (
    echo Backend is running on port 8000.
)

:: Check frontend (port 3000)
curl -s http://localhost:3000 > nul
if %errorlevel% neq 0 (
    echo WARNING: Frontend might not be running correctly on port 3000.
    echo Check frontend_log.txt for errors.
) else (
    echo Frontend is running on port 3000.
)

:: Open the browser
echo Opening browser to http://localhost:3000
start http://localhost:3000

:: Deactivate virtual environment from main script (backend still runs in activated env)
call venv\Scripts\deactivate.bat

cd ..

echo.
echo The system is now running in the background.
echo All output is being logged to backend_log.txt and frontend_log.txt
echo.
echo To stop all servers, run these commands:
echo taskkill /F /IM node.exe /T
echo taskkill /F /IM python.exe /T
echo.
echo Press any key to exit this window (servers will continue running)...
pause > nul 