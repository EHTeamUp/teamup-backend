@echo off
echo 🚀 TeamUp 프로젝트 설치를 시작합니다...

REM Python 버전 확인 (여러 명령어 시도)
python --version 2>nul
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :python_found
)

py --version 2>nul
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto :python_found
)

python3 --version 2>nul
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto :python_found
)

echo ❌ Python이 설치되지 않았습니다.
echo 📥 https://www.python.org/downloads/ 에서 Python 3.12.6을 다운로드하세요.
pause
exit /b 1

:python_found
echo ✅ Python을 찾았습니다: %PYTHON_CMD%

REM Python 버전 체크 (3.9 이상, 3.13 미만)
for /f "tokens=2" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.version_info[0:2])"') do (
    set PYTHON_VERSION=%%i
)

echo 현재 Python 버전: %PYTHON_VERSION%

REM 가상환경 생성
echo 📦 가상환경을 생성합니다...
%PYTHON_CMD% -m venv venv

REM 가상환경 활성화
echo 🔄 가상환경을 활성화합니다...
call venv\Scripts\activate.bat

REM 의존성 설치
echo 📥 필요한 패키지들을 설치합니다...
pip install -r requirements.txt

echo ✅ 설치가 완료되었습니다!
echo 🚀 서버를 시작하려면: uvicorn main:app --reload
pause
