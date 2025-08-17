#!/bin/bash

echo "🚀 TeamUp 프로젝트 설치를 시작합니다..."

# Python 버전 확인
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3이 설치되지 않았습니다."
    echo "📥 Python 3.12.6을 설치하세요."
    exit 1
fi

# Python 버전 체크 (3.9 이상, 3.13 미만)
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "현재 Python 버전: $PYTHON_VERSION"

if [ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -ge 9 ] && [ "$MINOR_VERSION" -lt 13 ]; then
    echo "✅ Python 버전이 호환됩니다."
else
    echo "⚠️  Python 3.9 ~ 3.12 버전을 권장합니다."
    echo "📥 Python 3.12.6을 설치하세요."
fi

# 가상환경 생성
echo "📦 가상환경을 생성합니다..."
python3 -m venv venv

# 가상환경 활성화
echo "🔄 가상환경을 활성화합니다..."
source venv/bin/activate

# 의존성 설치
echo "📥 필요한 패키지들을 설치합니다..."
pip install -r requirements.txt

echo "✅ 설치가 완료되었습니다!"
echo "🚀 서버를 시작하려면: uvicorn main:app --reload"
