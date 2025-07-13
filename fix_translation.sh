#!/bin/bash

# 번역 문제 해결 스크립트
# 이미 번역된 파일들에서 문제가 있는 부분을 감지하고 재번역합니다.

set -e

# 스크립트 경로 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 사용법 출력
show_usage() {
    echo "사용법: $0 <번역_디렉토리> [옵션]"
    echo ""
    echo "번역된 파일들에서 문제점을 감지하고 재번역을 수행합니다."
    echo ""
    echo "인수:"
    echo "  번역_디렉토리        번역된 파일들이 있는 디렉토리"
    echo ""
    echo "옵션:"
    echo "  --model MODEL        사용할 Ollama 모델 (기본값: qwen2.5:14b)"
    echo "  --genre GENRE        소설 장르 (fantasy, sci-fi, romance, mystery, horror, general)"
    echo "  --temperature TEMP   번역 온도 (기본값: 0.1)"
    echo "  --max-retries N      최대 재시도 횟수 (기본값: 3)"
    echo "  --verbose, -v        상세한 출력"
    echo "  --help, -h           이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 translated/"
    echo "  $0 translated/ --model llama3.1:8b --verbose"
    echo "  $0 translated/ --genre fantasy --temperature 0.05"
    echo ""
    echo "감지 대상 문제들:"
    echo "  - 중국어/일본어 문자"
    echo "  - HTML 엔티티 (&amp;, &lt; 등)"
    echo "  - 특수 엔티티 (&O;, &C; 등)"
    echo "  - 번역 불완전"
    echo "  - 비정상 문자"
}

# 인수 확인
if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_usage
    exit 0
fi

TRANSLATED_DIR="$1"
shift

# 번역 디렉토리 존재 확인
if [ ! -d "$TRANSLATED_DIR" ]; then
    echo "❌ 번역 디렉토리를 찾을 수 없습니다: $TRANSLATED_DIR"
    exit 1
fi

# 번역된 청크 디렉토리 확인
if [ ! -d "$TRANSLATED_DIR/translated_chunks" ]; then
    echo "❌ 번역된 청크 디렉토리를 찾을 수 없습니다: $TRANSLATED_DIR/translated_chunks"
    echo "올바른 번역 결과 디렉토리인지 확인해주세요."
    exit 1
fi

echo "🔧 번역 문제 해결 시작"
echo "디렉토리: $TRANSLATED_DIR"
echo "================================"

# Python 모듈로 재번역 실행
python3 -m epub_extractor.cli fix "$TRANSLATED_DIR" "$@"

echo ""
echo "🎯 재번역 완료!"
echo ""
echo "다음 단계:"
echo "1. 결과 확인: ls $TRANSLATED_DIR/translated_chunks/"
echo "2. EPUB 생성: ./build.sh <원본.epub> $TRANSLATED_DIR"