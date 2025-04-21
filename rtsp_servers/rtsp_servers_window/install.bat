@echo off
echo ========== RTSP Server Installation Script ==========
echo Installing necessary components for the project. Please wait...

:: Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo After installing Python, run this script again.
    pause
    exit
) else (
    echo Python is already installed.
)

:: Check if Node.js is installed
node --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js is not installed. Please install Node.js from https://nodejs.org/
    echo After installing Node.js, run this script again.
    pause
    exit
) else (
    echo Node.js is already installed.
)

:: Install virtualenv if not already installed
pip show virtualenv > nul 2>&1
if %errorlevel% neq 0 (
    echo Installing virtualenv...
    pip install virtualenv
) else (
    echo virtualenv is already installed.
)

:: Create and activate virtual environment
cd rtsp_servers
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Fix Pillow version in requirements.txt
echo Fixing dependency versions in requirements.txt...
powershell -Command "(Get-Content requirements.txt) -replace 'pillow==11.2.0', 'pillow==11.2.1' | Set-Content requirements.txt"

:: Install Python packages
echo Installing Python packages...
python -m pip install --upgrade pip

:: Try to install requirements, if it fails try with more flexible versioning
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Some packages couldn't be installed with exact versions.
    echo Installing with more flexible versioning...
    powershell -Command "(Get-Content requirements.txt) -replace '==', '>=' | Set-Content requirements_flexible.txt"
    python -m pip install -r requirements_flexible.txt
)

:: Store venv path for later use
echo @echo off > venv_path.bat
echo set VENV_PATH=%cd%\venv >> venv_path.bat

:: Install Node.js packages
echo Installing Node.js packages...
cd rtsp-manager
call npm install
cd ..

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat
cd ..

echo ========== Installation Complete ==========
echo You can now run the project using run.bat
echo.
pause 