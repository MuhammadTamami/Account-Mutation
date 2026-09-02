@echo off
echo ========================================
echo Installing OCR Dependencies for Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] Installing Python packages...
echo.
cd backend
pip install pytesseract PyMuPDF Pillow
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python packages
    pause
    exit /b 1
)
cd ..

echo.
echo [2/3] Checking Tesseract OCR...
echo.

REM Check if Tesseract is already installed
tesseract --version >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Tesseract OCR is already installed
    tesseract --version
    goto verify
)

echo Tesseract OCR is not installed.
echo.
echo Please install Tesseract OCR manually:
echo 1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
echo 2. Or direct link: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe
echo 3. Run the installer
echo 4. Make sure to check "Add to PATH" during installation
echo 5. Restart this script after installation
echo.
echo Opening download page in browser...
start https://github.com/UB-Mannheim/tesseract/wiki
echo.
pause
exit /b 1

:verify
echo.
echo [3/3] Verifying installation...
echo.

cd backend
python test_rk_ocr.py
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Some tests failed
    echo Please check the error messages above
) else (
    echo.
    echo ========================================
    echo SUCCESS: All dependencies installed!
    echo ========================================
    echo.
    echo You can now process scanned PDF files with OCR
)
cd ..

echo.
pause
