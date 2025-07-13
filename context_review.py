#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
번역 컨텍스트 검토 및 재번역 도구

사용법:
1. 컨텍스트 검토: python3 context_review.py review <work_dir>
2. 특정 청크 재번역: python3 context_review.py retranslate <work_dir> <chunk_file>
3. 용어 업데이트: python3 context_review.py update <work_dir> <original> <korean> [category]
"""

import sys
import os
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from epub_extractor.context_manager import TranslationContextManager
from epub_extractor.translator import OllamaTranslator
from config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_GENRE

def review_context(work_dir: str):
    """번역 컨텍스트 검토"""
    manager = TranslationContextManager("Unknown", work_dir)
    manager.review_and_update_context()

def retranslate_chunk(work_dir: str, chunk_file: str):
    """특정 청크를 컨텍스트 정보와 함께 재번역"""
    chunk_path = Path(chunk_file)
    if not chunk_path.exists():
        print(f"❌ 청크 파일을 찾을 수 없습니다: {chunk_file}")
        return
    
    # 원본 텍스트 읽기
    with open(chunk_path, 'r', encoding='utf-8') as f:
        original_text = f.read().strip()
    
    print(f"📖 청크 파일: {chunk_file}")
    print(f"📏 원본 길이: {len(original_text)}자")
    
    # 번역기 초기화
    translator = OllamaTranslator(
        model_name=DEFAULT_MODEL,
        temperature=DEFAULT_TEMPERATURE,
        genre=DEFAULT_GENRE
    )
    
    # 컨텍스트 매니저 초기화
    manager = TranslationContextManager("Dragonlance", work_dir)
    
    print("\n🔄 컨텍스트 정보를 반영하여 재번역 중...")
    
    # 재번역 수행
    retranslated = manager.retranslate_with_context(original_text, translator)
    
    # 결과 저장
    output_file = Path(work_dir) / f"retranslated_{chunk_path.name}"
    with open(output_file, 'w', encoding='utf-8') as f:
        # 컨텍스트 정보도 함께 저장
        context_info = manager.get_context_for_translation()
        f.write(f"=== 번역 컨텍스트 정보 ===\n{context_info}\n\n")
        f.write(f"=== 원본 텍스트 ===\n{original_text}\n\n")
        f.write(f"=== 번역 결과 ===\n{retranslated}\n")
    
    print(f"✅ 재번역 완료: {output_file}")
    print(f"📏 번역 길이: {len(retranslated)}자")

def update_translation(work_dir: str, original: str, korean: str, category: str = "terms"):
    """번역 용어 업데이트"""
    manager = TranslationContextManager("Unknown", work_dir)
    manager.update_translation_from_user(original, korean, category)
    print(f"✅ 번역 업데이트 완료: {original} → {korean} ({category})")

def main():
    parser = argparse.ArgumentParser(
        description="번역 컨텍스트 검토 및 재번역 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 컨텍스트 검토
  python3 context_review.py review dragonlance_test/
  
  # 특정 청크 재번역
  python3 context_review.py retranslate dragonlance_test/ dragonlance_test/chunks/split_000_part_10.txt
  
  # 용어 업데이트
  python3 context_review.py update dragonlance_test/ "Raistlin" "라이스틸" characters
  python3 context_review.py update dragonlance_test/ "Shoikan Grove" "쇼이칸 숲" places
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='사용할 명령')
    
    # review 명령
    review_parser = subparsers.add_parser('review', help='번역 컨텍스트 검토')
    review_parser.add_argument('work_dir', help='작업 디렉토리')
    
    # retranslate 명령
    retrans_parser = subparsers.add_parser('retranslate', help='특정 청크 재번역')
    retrans_parser.add_argument('work_dir', help='작업 디렉토리')
    retrans_parser.add_argument('chunk_file', help='재번역할 청크 파일')
    
    # update 명령
    update_parser = subparsers.add_parser('update', help='번역 용어 업데이트')
    update_parser.add_argument('work_dir', help='작업 디렉토리')
    update_parser.add_argument('original', help='원문 용어')
    update_parser.add_argument('korean', help='한국어 번역')
    update_parser.add_argument('category', nargs='?', default='terms', 
                             choices=['characters', 'places', 'terms'],
                             help='용어 카테고리 (기본값: terms)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'review':
            review_context(args.work_dir)
        elif args.command == 'retranslate':
            retranslate_chunk(args.work_dir, args.chunk_file)
        elif args.command == 'update':
            update_translation(args.work_dir, args.original, args.korean, args.category)
    except KeyboardInterrupt:
        print("\n⚠️  사용자가 중단했습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()