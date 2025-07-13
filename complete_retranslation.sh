#!/bin/bash
# Dragonlance 완전 재번역 및 EPUB 생성 스크립트

echo "📖 Dragonlance 완전 재번역 프로세스"
echo "=================================="

# 1. 번역 진행 상황 확인
echo "1️⃣ 번역 진행 상황 확인..."
cd /Volumes/eyedisk/develop/translator
python3 -c "
import json
with open('dragonlance_retranslated/translation_progress.json', 'r') as f:
    progress = json.load(f)
completed = len(progress['completed'])
failed = len(progress['failed'])
total = 547
print(f'✅ 완료: {completed}/{total} ({completed/total*100:.1f}%)')
print(f'❌ 실패: {failed}')
"

echo ""
echo "2️⃣ 번역 완료 대기 중..."
echo "진행 상황을 확인하려면: tail -f retranslation.log"
echo ""

# 번역 완료 후 실행할 명령들을 준비
cat << 'EOF' > build_final_epub.sh
#!/bin/bash
echo "3️⃣ 최종 EPUB 생성..."
source venv/bin/activate

# 원본 EPUB 파일 확인
if [ -f "dragonlance-legends-1.epub" ]; then
    echo "✅ 원본 EPUB 파일 발견"
    
    # 최종 한국어 EPUB 생성
    python3 -m epub_extractor.cli build dragonlance-legends-1.epub dragonlance_retranslated/ dragonlance-legends-1-korean-final.epub
    
    if [ -f "dragonlance-legends-1-korean-final.epub" ]; then
        echo "✅ 최종 한국어 EPUB 생성 완료!"
        echo "📁 파일 위치: $(pwd)/dragonlance-legends-1-korean-final.epub"
        
        # 파일 크기 확인
        echo "📏 파일 크기:"
        ls -lh dragonlance-legends-1*.epub
        
        echo ""
        echo "🎉 번역 완료!"
        echo "컨텍스트 적용된 최종 EPUB: dragonlance-legends-1-korean-final.epub"
    else
        echo "❌ EPUB 생성 실패"
    fi
else
    echo "❌ 원본 EPUB 파일을 찾을 수 없습니다"
    echo "현재 디렉토리의 EPUB 파일들:"
    ls -la *.epub 2>/dev/null || echo "EPUB 파일 없음"
fi
EOF

chmod +x build_final_epub.sh

echo "번역이 완료되면 다음 명령을 실행하세요:"
echo "./build_final_epub.sh"