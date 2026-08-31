@echo off
echo ========================================
echo  Clearing React Development Cache
echo ========================================

echo.
echo [1/3] Stopping dev server if running...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Clearing webpack cache...
if exist node_modules\.cache (
    rmdir /s /q node_modules\.cache
    echo Cache cleared successfully!
) else (
    echo No cache found (already clean)
)

echo [3/3] Ready to restart...
echo.
echo Now run: npm start
echo.
pause
