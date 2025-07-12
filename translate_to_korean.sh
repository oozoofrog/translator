#!/bin/bash

# 영문 EPUB을 한글 EPUB으로 번역하는 통합 스크립트
# 사용법: ./translate_to_korean.sh "영문소설.epub" [옵션]

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 도움말 표시 함수
show_help() {
    echo "📚 영문 EPUB → 한글 EPUB 번역기"
    echo "========================================"
    echo "기본 사용법:"
    echo "  $0 \"영문소설.epub\""
    echo ""
    echo "고급 옵션:"
    echo "  $0 \"novel.epub\" --model llama3.1:8b"
    echo "  $0 \"novel.epub\" --genre sci-fi"
    echo "  $0 \"novel.epub\" --max-chunk-size 2000"
    echo "  $0 \"novel.epub\" --output \"번역본.epub\""
    echo ""
    echo "옵션 설명:"
    echo "  --model MODEL         사용할 Ollama 모델 (기본값: llama3.1:8b)"
    echo "  --genre GENRE         소설 장르 (fantasy/sci-fi/romance/mystery/general, 기본값: fantasy)"
    echo "  --max-chunk-size N    최대 청크 크기 (기본값: 3000)"
    echo "  --min-chunk-size N    최소 청크 크기 (기본값: 1000)"
    echo "  --temperature N       번역 온도 0.0-2.0 (기본값: 0.1)"
    echo "  --output FILE         출력 EPUB 파일명 (기본값: 원본파일명-ko.epub)"
    echo "  --keep-temp           임시 파일들 보존 (디버깅용)"
    echo "  --resume              중단된 번역 이어서 진행"
    echo "  --verbose, -v         상세한 출력 표시"
    echo "  --help, -h            이 도움말 표시"
    echo ""
    echo "전체 과정:"
    echo "  1. EPUB 파일 추출 및 청크 분할"
    echo "  2. Ollama를 사용한 영어→한국어 번역"
    echo "  3. 번역된 텍스트로 한글 EPUB 파일 생성"
    echo ""
    echo "요구사항:"
    echo "  - Ollama가 실행 중이어야 함"
    echo "  - 지정된 모델이 설치되어 있어야 함"
    echo "  - 충분한 디스크 공간 (원본 크기의 3-5배)"
}

# 기본값 설정
MODEL="llama3.1:8b"
GENRE="fantasy"
MAX_CHUNK_SIZE=3000
MIN_CHUNK_SIZE=1000
TEMPERATURE=0.1
KEEP_TEMP=false
RESUME=false
VERBOSE=false
OUTPUT_FILE=""

# 인수 확인
if [ $# -lt 1 ]; then
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

# 나머지 옵션 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --genre)
            GENRE="$2"
            shift 2
            ;;
        --max-chunk-size)
            MAX_CHUNK_SIZE="$2"
            shift 2
            ;;
        --min-chunk-size)
            MIN_CHUNK_SIZE="$2"
            shift 2
            ;;
        --temperature)
            TEMPERATURE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --keep-temp)
            KEEP_TEMP=true
            shift
            ;;
        --resume)
            RESUME=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        *)
            echo "❌ 알 수 없는 옵션: $1"
            echo "도움말: $0 --help"
            exit 1
            ;;
    esac
done

# 파일 존재 확인
if [ ! -f "$EPUB_FILE" ]; then
    echo "❌ EPUB 파일을 찾을 수 없습니다: $EPUB_FILE"
    exit 1
fi

# EPUB 확장자 확인
if [[ ! "$EPUB_FILE" =~ \.epub$ ]]; then
    echo "❌ EPUB 파일이 아닙니다: $EPUB_FILE"
    exit 1
fi

# 출력 파일명 자동 생성
if [ -z "$OUTPUT_FILE" ]; then
    BASE_NAME=$(basename "$EPUB_FILE" .epub)
    OUTPUT_FILE="${BASE_NAME}-ko.epub"
fi

# 작업 디렉토리 설정
BASE_NAME=$(basename "$EPUB_FILE" .epub)
WORK_DIR="${BASE_NAME}_translation_work"
EXTRACTED_DIR="$WORK_DIR/extracted"
TRANSLATED_DIR="$WORK_DIR/translated"

echo "📚 영문 EPUB → 한글 EPUB 번역기"
echo "========================================"
echo "📖 입력: $EPUB_FILE"
echo "📄 출력: $OUTPUT_FILE"
echo "🤖 모델: $MODEL"
echo "🎭 장르: $GENRE"
echo "📐 청크: $MIN_CHUNK_SIZE-$MAX_CHUNK_SIZE 문자"
echo "🌡️ 온도: $TEMPERATURE"
if [ "$RESUME" = true ]; then
    echo "🔄 모드: 이어서 진행"
fi
echo ""

# 가상환경 활성화
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "🐍 가상환경 활성화 중..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "⚠️  가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다."
fi

# Ollama 설치 확인
echo "🔍 Ollama 설치 상태 확인 중..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama를 찾을 수 없습니다."
    echo ""
    echo "💡 Ollama 설치 방법:"
    echo "   1. 자동 설치: ./activate.sh 실행"
    echo "   2. 수동 설치: https://ollama.com"
    echo ""
    exit 1
fi

echo "✅ Ollama 설치 확인 완료"
echo ""

# 작업 디렉토리 생성
mkdir -p "$WORK_DIR"

# 1단계: EPUB 추출
echo "🔄 1단계: EPUB 파일 추출 및 청크 분할"
echo "========================================"

if [ "$RESUME" = true ] && [ -d "$EXTRACTED_DIR" ]; then
    echo "✅ 추출 결과 발견, 건너뛰기: $EXTRACTED_DIR"
else
    EXTRACT_ARGS=(
        "extract"
        "$EPUB_FILE"
        "--output-dir" "$EXTRACTED_DIR"
        "--max-chunk-size" "$MAX_CHUNK_SIZE"
        "--min-chunk-size" "$MIN_CHUNK_SIZE"
    )
    
    if [ "$VERBOSE" = true ]; then
        EXTRACT_ARGS+=("--verbose")
    fi
    
    cd "$SCRIPT_DIR" && python3 -m epub_extractor.cli "${EXTRACT_ARGS[@]}"
    
    if [ $? -ne 0 ]; then
        echo "❌ EPUB 추출 실패"
        exit 1
    fi
    
    echo "✅ EPUB 추출 완료"
fi

echo ""

# 2단계: 번역
echo "🌏 2단계: 영어 → 한국어 번역"
echo "========================================"

TRANSLATE_ARGS=(
    "translate"
    "$EXTRACTED_DIR"
    "$TRANSLATED_DIR"
    "--model" "$MODEL"
    "--genre" "$GENRE"
    "--temperature" "$TEMPERATURE"
)

if [ "$RESUME" = true ]; then
    TRANSLATE_ARGS+=("--resume")
fi

if [ "$VERBOSE" = true ]; then
    TRANSLATE_ARGS+=("--verbose")
fi

cd "$SCRIPT_DIR" && python3 -m epub_extractor.cli "${TRANSLATE_ARGS[@]}"

if [ $? -ne 0 ]; then
    echo "❌ 번역 실패"
    exit 1
fi

echo "✅ 번역 완료"
echo ""

# 3단계: 한글 EPUB 생성
echo "📚 3단계: 한글 EPUB 파일 생성"
echo "========================================"

BUILD_ARGS=(
    "build"
    "$EPUB_FILE"
    "$TRANSLATED_DIR"
    "--output" "$OUTPUT_FILE"
)

if [ "$VERBOSE" = true ]; then
    BUILD_ARGS+=("--verbose")
fi

cd "$SCRIPT_DIR" && python3 -m epub_extractor.cli "${BUILD_ARGS[@]}"

if [ $? -ne 0 ]; then
    echo "❌ EPUB 생성 실패"
    exit 1
fi

echo "✅ 한글 EPUB 생성 완료"
echo ""

# 결과 요약
echo "🎉 번역 완료!"
echo "========================================"
echo "📖 원본: $EPUB_FILE"
echo "📄 한글: $OUTPUT_FILE"

if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "📏 크기: $FILE_SIZE"
fi

# 번역 통계 표시
if [ -f "$TRANSLATED_DIR/translation_index.json" ]; then
    echo ""
    echo "📊 번역 통계:"
    python3 -c "
import json
try:
    with open('$TRANSLATED_DIR/translation_index.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    info = data['translation_info']
    print(f\"   총 청크: {info['total_chunks']}개\")
    print(f\"   완료: {info['completed_chunks']}개\")
    print(f\"   실패: {info['failed_chunks']}개\")
    print(f\"   소요 시간: {info['duration_minutes']}분\")
    print(f\"   모델: {info['model']}\")
except:
    pass
"
fi

# 임시 파일 정리
if [ "$KEEP_TEMP" = false ]; then
    echo ""
    echo "🧹 임시 파일 정리 중..."
    rm -rf "$WORK_DIR"
    echo "✅ 정리 완료"
else
    echo ""
    echo "📁 작업 파일들이 보존되었습니다: $WORK_DIR"
    echo "   - $EXTRACTED_DIR (추출 결과)"
    echo "   - $TRANSLATED_DIR (번역 결과)"
fi

echo ""
echo "💡 다음 단계:"
echo "   - $OUTPUT_FILE 파일을 e-reader에서 확인"
echo "   - 번역 품질 검토 및 필요시 재번역"
echo "   - 다른 장르나 모델로 번역 실험"