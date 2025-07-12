#!/bin/bash

# EPUB 파일 추출 스크립트
# 사용법: ./extract.sh "파일명.epub"

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 인수 확인
if [ $# -eq 0 ]; then
    echo "❌ 사용법: $0 \"파일명.epub\""
    echo "예시: $0 \"example.epub\""
    exit 1
fi

EPUB_FILE="$1"

# 파일 존재 확인
if [ ! -f "$EPUB_FILE" ]; then
    echo "❌ 파일을 찾을 수 없습니다: $EPUB_FILE"
    exit 1
fi

# EPUB 파일 확장자 확인
if [[ ! "$EPUB_FILE" =~ \.epub$ ]]; then
    echo "❌ EPUB 파일이 아닙니다: $EPUB_FILE"
    exit 1
fi

echo "📚 EPUB 파일 추출 시작: $EPUB_FILE"
echo "================================================"

# 가상환경 활성화
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "🐍 가상환경 활성화 중..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "⚠️  가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다."
fi

# Python 스크립트 실행
python3 "$SCRIPT_DIR/epub_extractor.py" "$EPUB_FILE"

# 결과 확인
if [ $? -eq 0 ]; then
    echo "================================================"
    echo "✅ 추출 완료!"
    
    # 생성된 디렉토리 표시
    OUTPUT_DIR=$(basename "$EPUB_FILE" .epub)
    if [ -d "$OUTPUT_DIR" ]; then
        echo "📁 생성된 파일들:"
        ls -la "$OUTPUT_DIR"/*.txt 2>/dev/null | wc -l | xargs echo "   총 파일 수:"
        echo "   위치: $OUTPUT_DIR/"
    fi
else
    echo "❌ 추출 중 오류가 발생했습니다."
    exit 1
fi