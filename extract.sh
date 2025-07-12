#!/bin/bash

# EPUB 파일 추출 스크립트 (개선된 버전)
# 사용법: ./extract.sh "파일명.epub" [옵션]

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 도움말 표시 함수
show_help() {
    echo "📚 EPUB 추출기 - 사용법"
    echo "======================================"
    echo "기본 사용법:"
    echo "  $0 \"파일명.epub\""
    echo ""
    echo "고급 옵션:"
    echo "  $0 \"파일명.epub\" --max-chunk-size 4000"
    echo "  $0 \"파일명.epub\" --min-chunk-size 500"
    echo "  $0 \"파일명.epub\" --no-chunks"
    echo "  $0 \"파일명.epub\" --output-dir \"출력폴더\""
    echo ""
    echo "옵션 설명:"
    echo "  --max-chunk-size N    최대 청크 크기 (문자 수, 기본값: 3000)"
    echo "  --min-chunk-size N    최소 청크 크기 (문자 수, 기본값: 1000)"
    echo "  --no-chunks          청크 파일 생성하지 않음"
    echo "  --output-dir DIR     출력 디렉토리 지정"
    echo "  --help, -h           이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 \"novel.epub\"                           # 기본 설정으로 추출"
    echo "  $0 \"novel.epub\" --max-chunk-size 2000     # 작은 청크로 분할"
    echo "  $0 \"novel.epub\" --no-chunks               # 챕터만 추출"
}

# 인수 확인
if [ $# -eq 0 ]; then
    echo "❌ EPUB 파일을 지정해주세요."
    echo ""
    show_help
    exit 1
fi

# 도움말 확인
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

EPUB_FILE="$1"
shift  # 첫 번째 인수 제거

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

echo "📚 EPUB 추출기 - 개선된 버전"
echo "파일: $EPUB_FILE"
echo "======================================"

# 가상환경 활성화
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "🐍 가상환경 활성화 중..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "⚠️  가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다."
fi

echo ""

# Python 스크립트 실행 (추가 인수들 전달)
cd "$SCRIPT_DIR" && python3 -m epub_extractor.cli extract "$EPUB_FILE" "$@"

# 결과 확인
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ 추출 완료!"
    
    # 생성된 디렉토리 표시
    OUTPUT_DIR=$(basename "$EPUB_FILE" .epub)
    
    # 출력 디렉토리가 다를 수 있으므로 확인
    for arg in "$@"; do
        if [[ "$prev_arg" == "--output-dir" ]] || [[ "$prev_arg" == "-o" ]]; then
            OUTPUT_DIR="$arg"
            break
        fi
        prev_arg="$arg"
    done
    
    if [ -d "$OUTPUT_DIR" ]; then
        echo ""
        echo "📁 생성된 구조:"
        echo "   $OUTPUT_DIR/"
        echo "   ├── info.json          (책 정보)"
        echo "   ├── chapters/          (원본 챕터들)"
        
        # 챕터 파일 수 세기
        chapter_count=$(find "$OUTPUT_DIR/chapters" -name "*.txt" 2>/dev/null | wc -l)
        echo "   │   └── $chapter_count 개 챕터 파일"
        
        # 청크 디렉토리 확인
        if [ -d "$OUTPUT_DIR/chunks" ]; then
            echo "   └── chunks/            (LLM 번역용 청크들)"
            chunk_count=$(find "$OUTPUT_DIR/chunks" -name "*.txt" 2>/dev/null | wc -l)
            echo "       └── $chunk_count 개 청크 파일"
        fi
        
        echo ""
        echo "💡 다음 단계:"
        echo "   - info.json에서 책 정보 확인"
        echo "   - chapters/ 폴더에서 원본 텍스트 확인"
        if [ -d "$OUTPUT_DIR/chunks" ]; then
            echo "   - chunks/ 폴더의 파일들을 LLM으로 번역"
        fi
    fi
else
    echo "❌ 추출 중 오류가 발생했습니다."
    exit 1
fi