@echo off
chcp 65001 >nul
title 투자 나침반 - 전체 분석
cd /d "%~dp0"

call "%~dp0_env_check.bat"
if errorlevel 1 exit /b 1

echo.
echo  ================================================
echo   투자 나침반 - 전체 분석 (나침반+Alpha+실행)
echo  ================================================
echo.

python -m src.main
set CODE=%ERRORLEVEL%

echo.
if %CODE% EQU 0 (
    echo  [완료] outputs\ 폴더를 확인하세요.
    echo  - acceptance_report.json  운용 승인
    echo  - trade_actions.csv       실행 권고
) else (
    echo  [주의] Data Gate RED 또는 오류 — outputs\ 확인
)
echo.
pause
exit /b %CODE%
