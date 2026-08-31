@echo off
echo ========================================
echo  Installing Bank Statement Converter
echo ========================================

echo.
echo [1/3] Installing Python dependencies...
pip install flask==3.0.0 flask-cors==4.0.0 werkzeug==3.0.1
pip install pandas==2.1.4 openpyxl==3.1.2 pdfplumber==0.10.3 python-dateutil==2.8.2

echo.
echo [2/3] Checking Node.js installation...
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from: https://nodejs.org/
    pause
    exit /b 1
)

echo.
echo [3/3] Installing Node.js dependencies...
cd frontend
call npm install

cd ..
echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo To run the application:
echo 1. Run start_backend.bat (in one terminal)
echo 2. Run start_frontend.bat (in another terminal)
echo.
pause
