@echo off

chcp 65001 >nul

title 투자 나침반

cd /d "%~dp0"



call "%~dp0_env_check.bat"

if errorlevel 1 exit /b 1



:MENU

cls

echo.

echo  ================================================

echo        투자 나침반 - 운용 콘솔

echo  ================================================

echo.

echo   모든 운용(설정·데이터·분석·승인)은 브라우저 UI에서 합니다.

echo.

python -c "from pathlib import Path; from src.settings.user_secrets import credential_status; s=credential_status(Path('data')); print('  API  DART:', 'OK' if s['dart'] else '미설정', ' | KRX:', 'OK' if s['krx'] else '미설정', '  (UI [설정] 탭에서 저장)')" 2>nul

echo.

echo   [1] UI 실행          (브라우저 — 권장, 매일 사용)

echo   [2] 설치 / 업데이트  (최초 1회 또는 패키지 갱신)

echo   [0] 종료

echo.

choice /C 120 /M "선택 (1=UI, 2=설치, 0=종료): "

if errorlevel 4 (

    echo.

    echo  [오류] 메뉴 입력에 실패했습니다. 아무 키나 누르면 다시 시도합니다.

    pause >nul

    goto MENU

)

set CHOICE=%ERRORLEVEL%



if %CHOICE%==1 goto RUN_UI

if %CHOICE%==2 goto RUN_INSTALL

if %CHOICE%==3 goto EXIT

echo.

echo  [안내] 1, 2 또는 0을 선택하세요.

pause >nul

goto MENU



:RUN_UI

call "%~dp0UI실행.bat"

goto MENU



:RUN_INSTALL

call "%~dp0설치.bat"

goto MENU



:EXIT

exit /b 0

