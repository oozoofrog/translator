#!/bin/bash

# 번역된 텍스트로 한글 EPUB 생성 스크립트
# 사용법: ./build.sh "원본.epub" "번역디렉토리" [출력파일]

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 도움말 표시 함수
show_help() {
    echo "📚 한글 EPUB 빌더 - 사용법"
    echo "======================================"
    echo "기본 사용법:"
    echo "  $0 \"원본.epub\" \"번역디렉토리\""
    echo "  $0 \"원본.epub\" \"번역디렉토리\" \"출력파일.epub\""
    echo ""
    echo "예시:"
    echo "  $0 \"novel.epub\" \"translated/\"                    # novel-ko.epub 생성"
    echo "  $0 \"novel.epub\" \"translated/\" \"korean.epub\"      # korean.epub 생성"
    echo ""
    echo "옵션:"
    echo "  --verbose, -v         상세한 출력 표시"
    echo "  --help, -h            이 도움말 표시"
    echo ""
    echo "요구사항:"
    echo "  - 원본 EPUB 파일이 존재해야 함"
    echo "  - 번역 디렉토리에 translated_chunks/ 폴더가 있어야 함"
    echo "  - translation_index.json 파일이 있어야 함"
}

# 기본값 설정
VERBOSE=false

# 인수 확인
if [ $# -lt 2 ]; then
    echo "❌ 원본 EPUB 파일과 번역 디렉토리를 지정해주세요."
    echo ""
    show_help
    exit 1
fi

# 도움말 확인
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

ORIGINAL_EPUB="$1"
TRANSLATED_DIR="$2"
OUTPUT_FILE="$3"

# 추가 옵션 파싱
shift 3
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "❌ 알 수 없는 옵션: $1"
            echo "도움말: $0 --help"
            exit 1
            ;;
    esac
done

# 파일/디렉토리 존재 확인
if [ ! -f "$ORIGINAL_EPUB" ]; then
    echo "❌ 원본 EPUB 파일을 찾을 수 없습니다: $ORIGINAL_EPUB"
    exit 1
fi

if [ ! -d "$TRANSLATED_DIR" ]; then
    echo "❌ 번역 디렉토리를 찾을 수 없습니다: $TRANSLATED_DIR"
    exit 1
fi

# EPUB 확장자 확인
if [[ ! "$ORIGINAL_EPUB" =~ \\.epub$ ]]; then
    echo "❌ 원본 파일이 EPUB 파일이 아닙니다: $ORIGINAL_EPUB"
    exit 1
fi

# 출력 파일명 자동 생성
if [ -z "$OUTPUT_FILE" ]; then
    BASE_NAME=$(basename "$ORIGINAL_EPUB" .epub)
    OUTPUT_FILE="${BASE_NAME}-ko.epub"
fi

echo "📚 한글 EPUB 빌더"
echo "원본: $ORIGINAL_EPUB"
echo "번역: $TRANSLATED_DIR"
echo "출력: $OUTPUT_FILE"
echo "========================================"

# 가상환경 활성화
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "🐍 가상환경 활성화 중..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "⚠️  가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다."
fi

echo ""

# 필수 파일들 확인
echo "🔍 번역 파일 확인 중..."

TRANSLATED_CHUNKS_DIR="$TRANSLATED_DIR/translated_chunks"
if [ ! -d "$TRANSLATED_CHUNKS_DIR" ]; then
    echo "❌ 번역된 청크 디렉토리를 찾을 수 없습니다: $TRANSLATED_CHUNKS_DIR"
    echo "먼저 번역을 수행해주세요."
    exit 1
fi

TRANSLATION_INDEX="$TRANSLATED_DIR/translation_index.json"
if [ ! -f "$TRANSLATION_INDEX" ]; then
    echo "❌ 번역 인덱스 파일을 찾을 수 없습니다: $TRANSLATION_INDEX"
    echo "먼저 번역을 수행해주세요."
    exit 1
fi

# 번역된 파일 수 확인
TRANSLATED_COUNT=$(find "$TRANSLATED_CHUNKS_DIR" -name "ko_*.txt" 2>/dev/null | wc -l)
echo "✅ 번역된 청크: $TRANSLATED_COUNT 개"

echo ""

# Python 빌드 스크립트 실행
BUILD_ARGS=(
    "build"
    "$ORIGINAL_EPUB"
    "$TRANSLATED_DIR"
    "--output" "$OUTPUT_FILE"
)

if [ "$VERBOSE" = true ]; then
    BUILD_ARGS+=("--verbose")
fi

cd "$SCRIPT_DIR" && python3 -m epub_extractor.cli "${BUILD_ARGS[@]}"

# 결과 확인
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✅ 한글 EPUB 생성 완료!"
    
    if [ -f "$OUTPUT_FILE" ]; then
        echo ""
        echo "📁 생성된 파일:"
        echo "   파일: $OUTPUT_FILE"
        
        # 파일 크기 표시
        FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
        echo "   크기: $FILE_SIZE"
        
        # 번역 통계 표시 (translation_index.json에서)
        if [ -f "$TRANSLATION_INDEX" ]; then
            echo ""
            echo "📊 번역 통계:"
            python3 -c "
import json
try:
    with open('$TRANSLATION_INDEX', 'r', encoding='utf-8') as f:
        data = json.load(f)
    info = data['translation_info']
    print(f\"   총 청크: {info['total_chunks']}개\")
    print(f\"   완료: {info['completed_chunks']}개\")
    print(f\"   실패: {info['failed_chunks']}개\")
    print(f\"   모델: {info['model']}\")
except Exception as e:
    print(f\"   통계 로드 실패: {e}\")
"
        fi
        
        echo ""
        echo "💡 다음 단계:"
        echo "   - e-reader나 EPUB 뷰어에서 파일 확인"
        echo "   - 번역 품질 검토"
        echo "   - 필요시 번역 설정 조정 후 재번역"
    fi
else
    echo "❌ EPUB 생성 중 오류가 발생했습니다."
    echo ""
    echo "💡 문제 해결 방법:"
    echo "   1. 번역 디렉토리 구조 확인"
    echo "   2. 원본 EPUB 파일 무결성 확인"
    echo "   3. --verbose 옵션으로 상세 정보 확인"
    exit 1
fi