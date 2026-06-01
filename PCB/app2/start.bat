@echo off
REM Startup script for the application

set PORT=8080

if not "%1"=="" (
    set PORT=%1
)

echo ========================================
echo Starting Application
echo ========================================
echo Port: %PORT%
echo.

java -jar dist\app.jar %PORT%
