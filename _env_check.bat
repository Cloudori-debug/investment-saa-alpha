@echo off
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [오류] Python을 찾을 수 없습니다.
    echo  Python 3.11 이상을 설치하고 "PATH에 추가"를 체크한 뒤 다시 실행하세요.
    echo  https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
exit /b 0
