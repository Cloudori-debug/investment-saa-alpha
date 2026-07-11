@echo off
chcp 65001 >nul
title 투자 나침반 - DART 보강
cd /d "%~dp0"

call "%~dp0_env_check.bat"
if errorlevel 1 exit /b 1

echo.
echo  Open DART 재무 보강 (DART API Key 필요 — UI 설정 탭)
echo.

python -m src.data_refresh.dart_collect_main --scope prices %*
set CODE=%ERRORLEVEL%

echo.
if %CODE% EQU 0 (echo  [완료]) else (echo  [실패] 설정 탭에서 DART API Key 확인)
echo.
pause
exit /b %CODE%
