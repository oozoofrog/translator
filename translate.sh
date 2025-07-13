#!/bin/bash

# Ollama 번역 스크립트
# 사용법: ./translate.sh "추출된_디렉토리" "번역_출력_디렉토리" [옵션]

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 도움말 표시 함수
show_help() {
    echo "🌏 Ollama 번역기 - 사용법"
    echo "======================================"
    echo "기본 사용법:"
    echo "  $0 \"추출된_디렉토리\" \"번역_출력_디렉토리\""
    echo ""
    echo "고급 옵션:"
    echo "  $0 \"novel/\" \"translated/\" --model llama3.1:8b"
    echo "  $0 \"novel/\" \"translated/\" --temperature 0.1"
    echo "  $0 \"novel/\" \"translated/\" --resume"
    echo ""
    echo "옵션 설명:"
    echo "  --model MODEL         사용할 Ollama 모델 (기본값: llama3.1:8b)"
    echo "  --temperature N       번역 온도 0.0-2.0 (기본값: 0.1)"
    echo "  --max-retries N       재시도 횟수 (기본값: 3)"
    echo "  --genre GENRE         소설 장르 (fantasy/sci-fi/romance/mystery/general, 기본값: fantasy)"
    echo "  --max-workers N       병렬 처리 워커 수 (기본값: 4)"
    echo "  --batch-size N        배치 처리 크기 (기본값: 5)"
    echo "  --no-parallel         병렬 처리 비활성화"
    echo "  --no-cache            번역 캐싱 비활성화"
    echo "  --num-gpu-layers N    GPU에 로드할 레이어 수"
    echo "  --resume              이전 번역 작업 이어서 진행"
    echo "  --verbose, -v         상세한 출력 표시"
    echo "  --help, -h            이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 \"dragonlance-legends-01/\" \"translated/\"     # 기본 설정으로 번역"
    echo "  $0 \"novel/\" \"ko_novel/\" --model llama3:8b        # 다른 모델 사용"
    echo "  $0 \"novel/\" \"ko_novel/\" --resume                # 중단된 번역 이어서 진행"
    echo ""
    echo "요구사항:"
    echo "  - Ollama가 실행 중이어야 함"
    echo "  - 지정된 모델이 설치되어 있어야 함"
    echo "  - 입력 디렉토리에 chunks/ 폴더가 있어야 함"
}

# 인수 확인
if [ $# -lt 2 ]; then
    echo "❌ 입력 디렉토리와 출력 디렉토리를 지정해주세요."
    echo ""
    show_help
    exit 1
fi

# 도움말 확인
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"
shift 2  # 첫 두 개 인수 제거

# 입력 디렉토리 존재 확인
if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ 입력 디렉토리를 찾을 수 없습니다: $INPUT_DIR"
    exit 1
fi

# 청크 디렉토리 확인
if [ ! -d "$INPUT_DIR/chunks" ]; then
    echo "❌ 청크 디렉토리를 찾을 수 없습니다: $INPUT_DIR/chunks"
    echo "먼저 EPUB 파일을 추출해주세요."
    exit 1
fi

# 청크 인덱스 파일 확인
if [ ! -f "$INPUT_DIR/chunks/chunk_index.json" ]; then
    echo "❌ 청크 인덱스 파일을 찾을 수 없습니다: $INPUT_DIR/chunks/chunk_index.json"
    exit 1
fi

echo "🌏 Ollama 번역기"
echo "입력: $INPUT_DIR"
echo "출력: $OUTPUT_DIR"
echo "======================================"

# 가상환경 활성화
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "🐍 가상환경 활성화 중..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "⚠️  가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다."
fi

echo ""

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

# Python 번역 스크립트 실행 (추가 인수들 전달)
cd "$SCRIPT_DIR" && python3 -m epub_extractor.cli translate "$INPUT_DIR" "$OUTPUT_DIR" "$@"

# 결과 확인
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ 번역 완료!"
    
    if [ -d "$OUTPUT_DIR" ]; then
        echo ""
        echo "📁 생성된 구조:"
        echo "   $OUTPUT_DIR/"
        
        # 번역된 청크 파일 수 세기
        if [ -d "$OUTPUT_DIR/translated_chunks" ]; then
            echo "   ├── translated_chunks/     (번역된 청크들)"
            translated_count=$(find "$OUTPUT_DIR/translated_chunks" -name "ko_*.txt" 2>/dev/null | wc -l)
            echo "   │   └── $translated_count 개 번역 파일"
        fi
        
        # 번역 인덱스 확인
        if [ -f "$OUTPUT_DIR/translation_index.json" ]; then
            echo "   ├── translation_index.json (번역 정보)"
        fi
        
        # 진행 상황 파일 확인
        if [ -f "$OUTPUT_DIR/translation_progress.json" ]; then
            echo "   └── translation_progress.json (진행 상황)"
        fi
        
        echo ""
        echo "💡 다음 단계:"
        echo "   - translation_index.json에서 번역 통계 확인"
        echo "   - translated_chunks/ 폴더에서 번역 결과 확인"
        echo "   - 필요시 번역 파일들을 하나로 병합"
    fi
else
    echo "❌ 번역 중 오류가 발생했습니다."
    echo ""
    echo "💡 문제 해결 방법:"
    echo "   1. Ollama 서버가 실행 중인지 확인: ollama list"
    echo "   2. 모델이 설치되어 있는지 확인: ollama list"
    echo "   3. 네트워크 연결 상태 확인"
    echo "   4. --verbose 옵션으로 상세 정보 확인"
    exit 1
fi