@echo off
chcp 65001 >nul
title 투자 나침반 - 운용 승인 검증
cd /d "%~dp0"

call "%~dp0_env_check.bat"
if errorlevel 1 exit /b 1

echo.
echo  운용 승인 기준(AC) 검증 중...
echo.

python -m src.validation.acceptance_main
set CODE=%ERRORLEVEL%

echo.
if %CODE% EQU 0 (
    echo  결과: outputs\acceptance_report.json
) else (
    echo  [주의] RED 또는 오류 — acceptance_report.json 확인
)
echo.
pause
exit /b %CODE%
