#!/bin/bash

# EPUB 추출기 및 번역기 - 통합 설치 및 가상환경 활성화 스크립트

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📚 EPUB 추출기 및 번역기 - 통합 설정"
echo "========================================"

# Ollama 설치 확인 및 자동 설치
check_and_install_ollama() {
    echo "🔍 Ollama 설치 상태 확인 중..."
    
    if command -v ollama &> /dev/null; then
        echo "✅ Ollama가 이미 설치되어 있습니다."
        ollama --version
        return 0
    fi
    
    echo "❗ Ollama가 설치되지 않았습니다."
    echo "🚀 Ollama 자동 설치를 시작합니다..."
    
    # OS 확인
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux용 설치
        if command -v curl &> /dev/null; then
            echo "   Linux용 Ollama 설치 중..."
            curl -fsSL https://ollama.com/install.sh | sh
        else
            echo "❌ curl이 설치되지 않았습니다. 먼저 curl을 설치해주세요."
            echo "   Ubuntu/Debian: sudo apt install curl"
            echo "   CentOS/RHEL: sudo yum install curl"
            return 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS용 설치
        if command -v brew &> /dev/null; then
            echo "   macOS용 Ollama 설치 중..."
            brew install ollama
        else
            echo "   Homebrew를 사용하여 설치합니다..."
            echo "   Homebrew가 없다면 https://ollama.com 에서 수동 설치해주세요."
            return 1
        fi
    else
        echo "❌ 지원하지 않는 운영체제입니다."
        echo "   https://ollama.com 에서 수동으로 설치해주세요."
        return 1
    fi
    
    # 설치 확인
    if command -v ollama &> /dev/null; then
        echo "✅ Ollama 설치 완료!"
        ollama --version
        return 0
    else
        echo "❌ Ollama 설치에 실패했습니다."
        return 1
    fi
}

# 기본 번역 모델 다운로드
download_translation_model() {
    local model_name="llama3.1:8b"
    
    echo "🤖 번역 모델 확인 중..."
    
    # Ollama 서비스 시작 (백그라운드)
    if ! pgrep -f "ollama serve" > /dev/null; then
        echo "   Ollama 서비스 시작 중..."
        ollama serve &
        sleep 3
    fi
    
    # 모델 설치 여부 확인
    if ollama list | grep -q "$model_name"; then
        echo "✅ 번역 모델($model_name)이 이미 설치되어 있습니다."
        return 0
    fi
    
    echo "📥 번역 모델($model_name) 다운로드 중..."
    echo "   (최초 다운로드는 시간이 걸릴 수 있습니다)"
    
    if ollama pull "$model_name"; then
        echo "✅ 번역 모델 다운로드 완료!"
        return 0
    else
        echo "❌ 번역 모델 다운로드에 실패했습니다."
        echo "   나중에 수동으로 다운로드하세요: ollama pull $model_name"
        return 1
    fi
}

# Python 의존성 설치
install_python_dependencies() {
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo "🐍 Python 의존성 설치 중..."
        pip install -r "$SCRIPT_DIR/requirements.txt"
        if [ $? -eq 0 ]; then
            echo "✅ Python 의존성 설치 완료!"
        else
            echo "❌ Python 의존성 설치에 실패했습니다."
            return 1
        fi
    fi
}

# Ollama 설치 및 설정
check_and_install_ollama

echo ""

# 가상환경 설정
setup_python_environment() {
    echo "🐍 Python 가상환경 설정 중..."
    
    # 가상환경 생성 (없는 경우)
    if [ ! -d "$SCRIPT_DIR/venv" ]; then
        echo "   가상환경을 생성합니다..."
        if python3 -m venv "$SCRIPT_DIR/venv"; then
            echo "✅ 가상환경 생성 완료!"
        else
            echo "❌ 가상환경 생성에 실패했습니다."
            echo "   python3-venv 패키지가 설치되어 있는지 확인해주세요."
            return 1
        fi
    fi
    
    # 가상환경 활성화
    echo "   가상환경을 활성화합니다..."
    source "$SCRIPT_DIR/venv/bin/activate"
    
    # 활성화 확인
    if [ "$VIRTUAL_ENV" != "" ]; then
        echo "✅ 가상환경이 활성화되었습니다: $(basename $VIRTUAL_ENV)"
        echo "🔍 Python 버전: $(python --version)"
        
        # Python 의존성 설치
        install_python_dependencies
        
        return 0
    else
        echo "❌ 가상환경 활성화에 실패했습니다."
        return 1
    fi
}

# Python 환경 설정
if setup_python_environment; then
    echo ""
    echo "🎯 번역 모델 다운로드..."
    download_translation_model
    
    echo ""
    echo "=========================================="
    echo "✅ 모든 설정이 완료되었습니다!"
    echo ""
    echo "📖 사용 가능한 명령어:"
    echo "  ./extract.sh \"파일명.epub\"                    - EPUB 파일 추출"
    echo "  ./translate.sh \"추출폴더/\" \"번역폴더/\"         - 번역 실행"
    echo "  ./translate.sh \"폴더/\" \"번역/\" --genre sci-fi  - 장르별 번역"
    echo "  deactivate                                   - 가상환경 비활성화"
    echo ""
    echo "💡 번역 지원 장르: fantasy, sci-fi, romance, mystery, general"
    echo "🤖 기본 모델: llama3.1:8b"
    echo ""
    ollama start
else
    echo "❌ Python 환경 설정에 실패했습니다."
    exit 1
fi