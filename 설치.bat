@echo off
chcp 65001 >nul
title 투자 나침반 - 설치
cd /d "%~dp0"

call "%~dp0_env_check.bat"
if errorlevel 1 exit /b 1

echo.
echo  ================================================
echo   투자 나침반 - 패키지 설치 / 업데이트
echo  ================================================
echo.
echo  Python 패키지 설치 중... (최초 1~3분 소요)
echo.

python -m pip install --upgrade pip
python -m pip install -e ".[dev,ui,data]"
set CODE=%ERRORLEVEL%

echo.
if %CODE% EQU 0 (
    echo  [완료] 설치되었습니다.
    echo  다음: "투자나침반.bat" → [1] UI 실행
) else (
    echo  [실패] 설치 중 오류가 발생했습니다. 인터넷 연결을 확인하세요.
)
echo.
pause
exit /b %CODE%
