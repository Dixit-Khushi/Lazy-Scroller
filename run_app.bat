@echo off
echo ==========================================
echo      🖐️ Lazy Scroller - Auto Launcher
echo ==========================================

echo [1/3] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    pause
    exit /b
)

echo.
echo [2/3] Verifying Requirements...
python test_setup.py
if %errorlevel% neq 0 (
    echo ⚠️  Dependencies missing. Installing now...
    pip install -r requirements.txt
)

echo.
echo [3/3] Starting Lazy Scroller...
echo Press 'q' in the window to quit.
echo.
python Scrollerr.py

pause
