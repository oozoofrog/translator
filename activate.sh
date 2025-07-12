#!/bin/bash

# EPUB 추출기 - 가상환경 활성화 스크립트

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📚 EPUB 추출기 - Python 가상환경 설정"
echo "=========================================="

# 가상환경 존재 확인
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "❌ 가상환경을 찾을 수 없습니다."
    echo "다음 명령어로 가상환경을 생성하세요:"
    echo "  python3 -m venv venv"
    exit 1
fi

echo "🐍 Python 가상환경을 활성화합니다..."
source "$SCRIPT_DIR/venv/bin/activate"

# 활성화 확인
if [ "$VIRTUAL_ENV" != "" ]; then
    echo "✅ 가상환경이 활성화되었습니다: $(basename $VIRTUAL_ENV)"
    
    # Python 버전 확인
    echo "🔍 Python 버전: $(python --version)"
    
    # requirements.txt 확인
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo "📋 의존성 파일 확인됨: requirements.txt"
        echo "   (이 프로젝트는 표준 라이브러리만 사용합니다)"
    fi
    
    echo ""
    echo "사용 가능한 명령어:"
    echo "  ./extract.sh \"파일명.epub\"  - EPUB 파일 추출"
    echo "  deactivate                 - 가상환경 비활성화"
    echo ""
else
    echo "❌ 가상환경 활성화에 실패했습니다."
    exit 1
fi