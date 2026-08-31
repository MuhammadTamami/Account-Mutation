@echo off
echo ========================================
echo  Starting Frontend Server...
echo ========================================
echo.
echo Checking dependencies...

cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo.
    echo Installing dependencies first...
    echo This may take 2-3 minutes...
    echo.
    call npm install
    echo.
    echo Dependencies installed!
    echo.
)

echo.
echo Starting React dev server...
echo.
echo Browser will open automatically at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

npm start

pause
