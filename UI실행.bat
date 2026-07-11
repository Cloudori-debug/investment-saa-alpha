@echo off
chcp 65001 >nul
title 투자 나침반 - UI
cd /d "%~dp0"

call "%~dp0_env_check.bat"
if errorlevel 1 exit /b 1

python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [안내] Streamlit이 설치되지 않았습니다.
    echo  "설치.bat"을 먼저 실행하거나 "투자나침반.bat" 메뉴 [3]을 선택하세요.
    echo.
    pause
    exit /b 1
)

python -c "from pathlib import Path; from src.settings.user_secrets import credential_status; s=credential_status(Path('data')); print('  API  DART:', 'OK' if s['dart'] else '미설정', ' | KRX:', 'OK' if s['krx'] else '미설정')" 2>nul
echo.
echo  브라우저 운용 화면을 엽니다.
echo  - 설정·PyKRX·DART·전체 분석·운용승인: 모두 UI에서 실행
echo  - 종료: 이 창에서 Ctrl+C
echo.

streamlit run app.py
pause
