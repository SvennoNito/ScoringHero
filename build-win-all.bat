@echo off
echo === Building scoringhero_windows.exe (py13) ===
call build-win-py13.bat
if errorlevel 1 (
    echo Build failed: build-win-py13.bat
    exit /b 1
)

echo === Building auto-scoringhero_windows.exe (gssc) ===
call build-win-gssc.bat
if errorlevel 1 (
    echo Build failed: build-win-gssc.bat
    exit /b 1
)

echo === All builds completed successfully ===
