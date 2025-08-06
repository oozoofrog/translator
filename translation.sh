#!/bin/bash

# EPUB 번역 통합 스크립트
# 사용법: ./translation.sh <command> [options]
# Commands: extract, translate, combine, full
# Authors: AI Assistant
# Version: 1.0.0

# 스크립트 종료 시 에러 발생하면 중단
set -e

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 색상 코드 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 도움말 표시 함수
show_help() {
    echo "📚 EPUB 번역 통합 스크립트 v1.0.0"
    echo "======================================"
    echo ""
    echo "사용법: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  extract    EPUB을 챕터와 청크로 추출"
    echo "  translate  추출된 청크를 한글로 번역"
    echo "  combine    번역된 청크를 EPUB으로 통합"
    echo "  full       전체 워크플로우 (추출 → 번역 → 통합)"
    echo ""
    echo "Extract 옵션:"
    echo "  -f, --file <file>         EPUB 파일 경로 (필수)"
    echo "  -o, --output-dir <dir>    출력 디렉토리"
    echo "  --max-chunk-size <size>   최대 청크 크기 (기본값: 3000)"
    echo "  --min-chunk-size <size>   최소 청크 크기 (기본값: 1000)"
    echo "  --extract-only            청크 없이 원본 HTML만 추출"
    echo "  --no-chunks               챕터 파일만 생성"
    echo "  -v, --verbose             상세한 출력 표시"
    echo ""
    echo "Translate 옵션:"
    echo "  -i, --input-dir <dir>     입력 디렉토리 (필수)"
    echo "  -o, --output-dir <dir>    출력 디렉토리 (기본값: translated/)"
    echo "  -m, --model <model>       사용할 Ollama 모델 (기본값: gpt-oss:20b)"
    echo "  -g, --genre <genre>       소설 장르 (기본값: fantasy)"
    echo "  --temperature <temp>      번역 온도 (기본값: 0.1)"
    echo "  --max-retries <num>       최대 재시도 횟수 (기본값: 3)"
    echo "  --resume                  이전 번역 작업 이어서 진행"
    echo "  -v, --verbose             상세한 출력 표시"
    echo ""
    echo "Combine 옵션:"
    echo "  -f, --original-file <file>    원본 EPUB 파일 (필수)"
    echo "  -i, --input-dir <dir>         번역 디렉토리 (필수)"
    echo "  -o, --output-file <file>      출력 EPUB 파일 (기본값: 원본-ko.epub)"
    echo "  -v, --verbose                 상세한 출력 표시"
    echo ""
    echo "Full 워크플로우 옵션:"
    echo "  -f, --file <file>             EPUB 파일 경로 (필수)"
    echo "  -w, --work-dir <dir>          작업 디렉토리 (기본값: 파일명)"
    echo "  -m, --model <model>           사용할 Ollama 모델 (기본값: gpt-oss:20b)"
    echo "  -g, --genre <genre>           소설 장르 (기본값: fantasy)"
    echo "  --max-chunk-size <size>       최대 청크 크기 (기본값: 3000)"
    echo "  --temperature <temp>          번역 온도 (기본값: 0.1)"
    echo "  -v, --verbose                 상세한 출력 표시"
    echo ""
    echo "예시:"
    echo "  $0 extract -f novel.epub"
    echo "  $0 translate -i novel/ -m gpt-oss:20b"
    echo "  $0 combine -f novel.epub -i translated/"
    echo "  $0 full -f novel.epub -m gpt-oss:20b"
}

# 가상환경 활성화 함수
activate_venv() {
    if [ -d "$SCRIPT_DIR/venv" ]; then
        log_info "가상환경 활성화 중..."
        source "$SCRIPT_DIR/venv/bin/activate"
        log_success "가상환경 활성화 완료"
    else
        log_warning "가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다."
    fi
}

# EPUB 추출 함수
extract_epub() {
    local epub_file=""
    local output_dir=""
    local max_chunk_size=3000
    local min_chunk_size=1000
    local extract_only=false
    local no_chunks=false
    local verbose=false
    
    # 옵션 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--file)
                epub_file="$2"
                shift 2
                ;;
            -o|--output-dir)
                output_dir="$2"
                shift 2
                ;;
            --max-chunk-size)
                max_chunk_size="$2"
                shift 2
                ;;
            --min-chunk-size)
                min_chunk_size="$2"
                shift 2
                ;;
            --extract-only)
                extract_only=true
                shift
                ;;
            --no-chunks)
                no_chunks=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            *)
                log_error "알 수 없는 extract 옵션: $1"
                return 1
                ;;
        esac
    done
    
    # 필수 인수 확인
    if [ -z "$epub_file" ]; then
        log_error "EPUB 파일이 지정되지 않았습니다. -f 옵션을 사용하세요."
        return 1
    fi
    
    # 파일 존재 확인
    if [ ! -f "$epub_file" ]; then
        log_error "EPUB 파일을 찾을 수 없습니다: $epub_file"
        return 1
    fi
    
    log_info "EPUB 추출 시작: $epub_file"
    
    # 가상환경 활성화
    activate_venv
    
    # Python CLI 실행 인수 구성
    local args=("extract" "$epub_file")
    
    if [ -n "$output_dir" ]; then
        args+=("--output-dir" "$output_dir")
    fi
    
    args+=("--max-chunk-size" "$max_chunk_size")
    args+=("--min-chunk-size" "$min_chunk_size")
    
    if [ "$extract_only" = true ]; then
        args+=("--extract-only")
    fi
    
    if [ "$no_chunks" = true ]; then
        args+=("--no-chunks")
    fi
    
    if [ "$verbose" = true ]; then
        args+=("--verbose")
    fi
    
    # Python 실행
    cd "$SCRIPT_DIR" && python3 -m epub_extractor.cli "${args[@]}"
    
    log_success "EPUB 추출 완료"
}

# 번역 함수
translate_chunks() {
    local input_dir=""
    local output_dir="translated"
    local model="gpt-oss:20b"
    local genre="fantasy"
    local temperature="0.1"
    local max_retries="3"
    local resume=false
    local verbose=false
    
    # 옵션 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -i|--input-dir)
                input_dir="$2"
                shift 2
                ;;
            -o|--output-dir)
                output_dir="$2"
                shift 2
                ;;
            -m|--model)
                model="$2"
                shift 2
                ;;
            -g|--genre)
                genre="$2"
                shift 2
                ;;
            --temperature)
                temperature="$2"
                shift 2
                ;;
            --max-retries)
                max_retries="$2"
                shift 2
                ;;
            --resume)
                resume=true
                shift
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            *)
                log_error "알 수 없는 translate 옵션: $1"
                return 1
                ;;
        esac
    done
    
    # 필수 인수 확인
    if [ -z "$input_dir" ]; then
        log_error "입력 디렉토리가 지정되지 않았습니다. -i 옵션을 사용하세요."
        return 1
    fi
    
    # 디렉토리 존재 확인
    if [ ! -d "$input_dir" ]; then
        log_error "입력 디렉토리를 찾을 수 없습니다: $input_dir"
        return 1
    fi
    
    # 청크 디렉토리 확인
    if [ ! -d "$input_dir/chunks" ]; then
        log_error "청크 디렉토리를 찾을 수 없습니다: $input_dir/chunks"
        log_error "먼저 EPUB 파일을 추출해주세요."
        return 1
    fi
    
    log_info "번역 시작: $input_dir → $output_dir"
    log_info "모델: $model, 장르: $genre"
    
    # 가상환경 활성화
    activate_venv
    
    # Python CLI 실행 인수 구성
    local args=("translate" "$input_dir" "$output_dir")
    args+=("--model" "$model")
    args+=("--genre" "$genre")
    args+=("--temperature" "$temperature")
    args+=("--max-retries" "$max_retries")
    
    if [ "$resume" = true ]; then
        args+=("--resume")
    fi
    
    if [ "$verbose" = true ]; then
        args+=("--verbose")
    fi
    
    # Python 실행
    cd "$SCRIPT_DIR" && python3 -m epub_extractor.cli "${args[@]}"
    
    log_success "번역 완료"
}

# EPUB 통합 함수
combine_epub() {
    local original_file=""
    local input_dir=""
    local output_file=""
    local verbose=false
    
    # 옵션 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--original-file)
                original_file="$2"
                shift 2
                ;;
            -i|--input-dir)
                input_dir="$2"
                shift 2
                ;;
            -o|--output-file)
                output_file="$2"
                shift 2
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            *)
                log_error "알 수 없는 combine 옵션: $1"
                return 1
                ;;
        esac
    done
    
    # 필수 인수 확인
    if [ -z "$original_file" ]; then
        log_error "원본 EPUB 파일이 지정되지 않았습니다. -f 옵션을 사용하세요."
        return 1
    fi
    
    if [ -z "$input_dir" ]; then
        log_error "번역 디렉토리가 지정되지 않았습니다. -i 옵션을 사용하세요."
        return 1
    fi
    
    # 파일/디렉토리 존재 확인
    if [ ! -f "$original_file" ]; then
        log_error "원본 EPUB 파일을 찾을 수 없습니다: $original_file"
        return 1
    fi
    
    if [ ! -d "$input_dir" ]; then
        log_error "번역 디렉토리를 찾을 수 없습니다: $input_dir"
        return 1
    fi
    
    # 번역 파일 확인
    if [ ! -d "$input_dir/translated_chunks" ]; then
        log_error "번역된 청크 디렉토리를 찾을 수 없습니다: $input_dir/translated_chunks"
        log_error "먼저 번역을 수행해주세요."
        return 1
    fi
    
    # 출력 파일명 자동 생성
    if [ -z "$output_file" ]; then
        local base_name=$(basename "$original_file" .epub)
        output_file="${base_name}-ko.epub"
    fi
    
    log_info "EPUB 통합 시작: $original_file + $input_dir → $output_file"
    
    # 가상환경 활성화
    activate_venv
    
    # Python CLI 실행 인수 구성
    local args=("build" "$original_file" "$input_dir" "--output" "$output_file")
    
    if [ "$verbose" = true ]; then
        args+=("--verbose")
    fi
    
    # Python 실행
    cd "$SCRIPT_DIR" && python3 -m epub_extractor.cli "${args[@]}"
    
    log_success "EPUB 통합 완료: $output_file"
}

# 전체 워크플로우 함수
full_workflow() {
    local epub_file=""
    local work_dir=""
    local model="gpt-oss:20b"
    local genre="fantasy"
    local max_chunk_size=3000
    local temperature="0.1"
    local verbose=false
    
    # 옵션 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--file)
                epub_file="$2"
                shift 2
                ;;
            -w|--work-dir)
                work_dir="$2"
                shift 2
                ;;
            -m|--model)
                model="$2"
                shift 2
                ;;
            -g|--genre)
                genre="$2"
                shift 2
                ;;
            --max-chunk-size)
                max_chunk_size="$2"
                shift 2
                ;;
            --temperature)
                temperature="$2"
                shift 2
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            *)
                log_error "알 수 없는 full 옵션: $1"
                return 1
                ;;
        esac
    done
    
    # 필수 인수 확인
    if [ -z "$epub_file" ]; then
        log_error "EPUB 파일이 지정되지 않았습니다. -f 옵션을 사용하세요."
        return 1
    fi
    
    # 파일 존재 확인
    if [ ! -f "$epub_file" ]; then
        log_error "EPUB 파일을 찾을 수 없습니다: $epub_file"
        return 1
    fi
    
    # 작업 디렉토리 자동 생성
    if [ -z "$work_dir" ]; then
        work_dir=$(basename "$epub_file" .epub)
    fi
    
    local translated_dir="${work_dir}/translated"
    local output_file="${work_dir}/$(basename "$epub_file" .epub)-ko.epub"
    
    echo "🚀 전체 번역 워크플로우 시작"
    echo "======================================"
    echo "📖 원본 파일: $epub_file"
    echo "📁 작업 디렉토리: $work_dir"
    echo "🤖 모델: $model"
    echo "📚 장르: $genre"
    echo "📄 출력: $output_file"
    echo "======================================"
    echo ""
    
    # 1. 추출
    log_info "1단계: EPUB 추출"
    local extract_args=("-f" "$epub_file" "-o" "$work_dir" "--max-chunk-size" "$max_chunk_size")
    if [ "$verbose" = true ]; then
        extract_args+=("-v")
    fi
    extract_epub "${extract_args[@]}"
    echo ""
    
    # 2. 번역
    log_info "2단계: 청크 번역"
    local translate_args=("-i" "$work_dir" "-o" "$translated_dir" "-m" "$model" "-g" "$genre" "--temperature" "$temperature")
    if [ "$verbose" = true ]; then
        translate_args+=("-v")
    fi
    translate_chunks "${translate_args[@]}"
    echo ""
    
    # 3. 통합
    log_info "3단계: EPUB 통합"
    local combine_args=("-f" "$epub_file" "-i" "$translated_dir" "-o" "$output_file")
    if [ "$verbose" = true ]; then
        combine_args+=("-v")
    fi
    combine_epub "${combine_args[@]}"
    echo ""
    
    # 완료 메시지
    echo "🎉 전체 번역 워크플로우 완료!"
    echo "======================================"
    echo "📁 작업 디렉토리: $work_dir"
    echo "📖 번역 EPUB: $output_file"
    if [ -f "$output_file" ]; then
        local file_size=$(du -h "$output_file" | cut -f1)
        echo "📊 파일 크기: $file_size"
    fi
    echo ""
    echo "💡 다음 단계:"
    echo "   - EPUB 뷰어에서 번역 결과 확인"
    echo "   - 번역 품질 검토"
    echo "   - 필요시 번역 설정 조정 후 재실행"
}

# 메인 함수
main() {
    # 인수가 없는 경우 도움말 표시
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # 도움말 확인
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi
    
    local command="$1"
    shift
    
    # 명령어별 실행
    case $command in
        extract)
            extract_epub "$@"
            ;;
        translate)
            translate_chunks "$@"
            ;;
        combine)
            combine_epub "$@"
            ;;
        full)
            full_workflow "$@"
            ;;
        *)
            log_error "알 수 없는 명령어: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 스크립트 진입점
main "$@"