#!/bin/bash

# EPUB 추출기 및 번역기 - 통합 설치 및 가상환경 활성화 스크립트 (Hugging Face 버전)

# 스크립트 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📚 EPUB 추출기 및 번역기 - Hugging Face 통합 설정"
echo "================================================"

# Python 의존성 설치
install_python_dependencies() {
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo "🐍 Python 의존성 설치 중..."
        
        # sentencepiece 설치 문제 해결을 위해 먼저 기본 패키지들 설치
        echo "   기본 패키지 설치 중..."
        pip install transformers torch accelerate tqdm
        
        # sentencepiece는 선택적으로 설치 (실패해도 계속 진행)
        echo "   sentencepiece 설치 시도 중..."
        if pip install sentencepiece; then
            echo "✅ sentencepiece 설치 완료!"
        else
            echo "⚠️  sentencepiece 설치 실패 (선택적 패키지)"
            echo "   번역 기능은 정상 작동하지만 일부 모델에서 최적화가 제한될 수 있습니다."
        fi
        
        echo "✅ Python 의존성 설치 완료!"
        return 0
    else
        echo "❌ requirements.txt 파일을 찾을 수 없습니다."
        return 1
    fi
}

# Hugging Face 모델 확인
check_huggingface_model() {
    local model_name="openai/gpt-oss-20b"
    
    echo "🤖 Hugging Face 모델 확인 중..."
    echo "   모델: $model_name"
    
    # Python을 사용하여 모델 접근 가능 여부 확인
    python3 -c "
import sys
try:
    from transformers import AutoTokenizer
    print('✅ Hugging Face Transformers 로드 성공')
    print('📥 모델 토크나이저 다운로드 중...')
    tokenizer = AutoTokenizer.from_pretrained('$model_name', trust_remote_code=True)
    print('✅ 모델 토크나이저 다운로드 완료!')
except ImportError as e:
    print(f'❌ Hugging Face 패키지가 설치되지 않았습니다: {e}')
    sys.exit(1)
except Exception as e:
    print(f'⚠️  모델 다운로드 중 오류 발생: {e}')
    print('   인터넷 연결을 확인하거나 나중에 수동으로 다운로드하세요.')
except KeyboardInterrupt:
    print('⏸️  사용자에 의해 중단되었습니다.')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo "✅ Hugging Face 모델 확인 완료!"
        return 0
    else
        echo "⚠️  모델 확인에 실패했습니다."
        return 1
    fi
}

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
    echo "🎯 Hugging Face 모델 확인..."
    check_huggingface_model
    
    echo ""
    echo "=========================================="
    echo "✅ 모든 설정이 완료되었습니다!"
    echo ""
    echo "📖 사용 가능한 명령어:"
    echo "  ./translation.sh extract -f \"파일명.epub\"           - EPUB 파일 추출"
    echo "  ./translation.sh translate -i \"추출폴더/\"           - 번역 실행"
    echo "  ./translation.sh full -f \"파일명.epub\"             - 전체 워크플로우"
    echo "  deactivate                                        - 가상환경 비활성화"
    echo ""
    echo "💡 번역 지원 장르: fantasy, sci-fi, romance, mystery, horror, general"
    echo "🤖 기본 모델: openai/gpt-oss-20b"
    echo "💻 디바이스: auto (CPU/GPU 자동 감지)"
    echo ""
    echo "🔧 문제 해결:"
    echo "  - GPU 사용: ./translation.sh translate -i folder/ --device cuda"
    echo "  - CPU 사용: ./translation.sh translate -i folder/ --device cpu"
    echo "  - 다른 모델: ./translation.sh translate -i folder/ -m openai/gpt-oss-120b"
else
    echo "❌ Python 환경 설정에 실패했습니다."
    exit 1
fi