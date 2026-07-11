@echo off
chcp 65001 >nul
title 투자 나침반 - PyKRX 수집
cd /d "%~dp0"

call "%~dp0_env_check.bat"
if errorlevel 1 exit /b 1

echo.
echo  PyKRX KOSPI 일괄 수집 (KRX ID/PW 필요 — UI 설정 탭)
echo.

python -m src.data_refresh.pykrx_collect_main --scope liquid %*
set CODE=%ERRORLEVEL%

echo.
if %CODE% EQU 0 (echo  [완료]) else (echo  [실패] 설정 탭에서 KRX ID/PW 확인)
echo.
pause
exit /b %CODE%
