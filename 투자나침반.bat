@echo off
chcp 65001 >nul
setlocal
set PYTHONUNBUFFERED=1
title Compass
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

:MENU
cls
echo.
echo ================================================
echo   Compass Launcher
echo ================================================
echo.
python "%~dp0scripts\launcher_cred_status.py" 2>nul
if errorlevel 1 echo   API: unavailable
echo.
echo [1] UI
echo [2] Install
echo [3] Analysis
echo [0] Exit
echo.
choice /C 1230 /N /M "Select: "
if errorlevel 4 goto EXIT
if errorlevel 3 goto RUN_ANALYSIS
if errorlevel 2 goto RUN_INSTALL
if errorlevel 1 goto RUN_UI
goto MENU

:RUN_UI
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Installing...
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev,ui,data]"
    if errorlevel 1 goto FAIL
)
echo.
echo UI starting. Ctrl+C to stop.
echo Phone: http://PC-IP:8501 same Wi-Fi only.
echo.
streamlit run "%~dp0alpha_dashboard.py" --server.address 0.0.0.0
if errorlevel 1 goto FAIL
pause
goto MENU

:RUN_INSTALL
python -m pip install --upgrade pip
python -m pip install -e ".[dev,ui,data]"
if errorlevel 1 goto FAIL
pause
goto MENU

:RUN_ANALYSIS
python -m src.main
if errorlevel 1 goto FAIL
pause
goto MENU

:FAIL
echo.
echo [ERROR] Failed.
pause
goto MENU

:EXIT
endlocal
exit /b 0
