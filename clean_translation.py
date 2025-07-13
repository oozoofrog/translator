#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
번역 파일 후처리 도구 - 문체 통일 및 문단 정리
"""

import sys
import re
from pathlib import Path

def normalize_korean_style(text: str) -> str:
    """한국어 문체를 표준 문어체로 통일"""
    
    # 구어체 종결어미를 문어체로 변환
    style_patterns = [
        # 과거형 통일
        (r'했어요\.', '했다.'),
        (r'했어\.', '했다.'),
        (r'였어요\.', '였다.'),
        (r'였어\.', '였다.'),
        (r'었어요\.', '었다.'),
        (r'었어\.', '었다.'),
        (r'됐어요\.', '되었다.'),
        (r'됐어\.', '되었다.'),
        (r'습니다\.', '다.'),
        (r'세요\.', '다.'),
        
        # 현재형 통일
        (r'해요\.', '한다.'),
        (r'해\.', '한다.'),
        (r'이에요\.', '이다.'),
        (r'예요\.', '다.'),
        (r'이야\.', '이다.'),
        (r'야\.', '다.'),
        
        # 기타 구어체 표현
        (r'다네\.', '다.'),
        (r'단다\.', '다.'),
        (r'지\.', '다.'),
        (r'구나\.', '다.'),
        (r'네\.', '다.'),
        (r'는군\.', '다.'),
        (r'는구나\.', '다.'),
        (r'죠;', '다;'),
        (r'어요;', '다;'),
        (r'죠\.', '다.'),
        
        # 특수 표현
        (r'니까요\.', '다.'),
        (r'니까\.', '다.'),
        (r'거예요\.', '것이다.'),
        (r'거야\.', '것이다.'),
        
        # 의문문 통일
        (r'해요\?', '하는가?'),
        (r'해\?', '하는가?'),
        (r'이에요\?', '인가?'),
        (r'예요\?', '인가?'),
        (r'야\?', '인가?'),
        
        # 감탄문 통일
        (r'해요!', '한다!'),
        (r'해!', '한다!'),
        (r'이에요!', '이다!'),
        (r'예요!', '다!'),
    ]
    
    for pattern, replacement in style_patterns:
        text = re.sub(pattern, replacement, text)
    
    return text

def format_paragraphs(text: str) -> str:
    """문단 구분과 들여쓰기 정리"""
    
    # 문장 끝에서 자연스러운 문단 분리 찾기
    paragraph_patterns = [
        # 대화문 후 문단 분리
        (r'(\"[^\"]*\"\.) ([가-힣])', r'\1\n\n\2'),
        (r'(\'[^\']*\'\.) ([가-힣])', r'\1\n\n\2'),
        
        # 긴 문장 후 자연스러운 분리점
        (r'(\.) (그런데|그러나|그래서|하지만|그리고|그때|그는|그녀)', r'.\n\n\2'),
        
        # 시간이나 장소 변화 표현 후
        (r'(\.) (그때|그순간|잠시후|잠깐|한편|반면)', r'.\n\n\2'),
        
        # 새로운 화자나 상황 전환
        (r'(\.) ([가-힣]{2,}는|[가-힣]{2,}가|[가-힣]{2,}은|[가-힣]{2,}이)', r'.\n\n\2'),
    ]
    
    for pattern, replacement in paragraph_patterns:
        text = re.sub(pattern, replacement, text)
    
    # 연속된 개행 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

def clean_translation(text: str) -> str:
    """번역 결과 종합 정리"""
    
    # 기본 정리
    cleaned_text = text.strip()
    
    # _TAB_ 제거
    cleaned_text = cleaned_text.replace('_TAB_', ' ')
    
    # <think> 태그 제거
    cleaned_text = re.sub(r'<think>.*?</think>', '', cleaned_text, flags=re.DOTALL)
    
    # 문체 통일
    cleaned_text = normalize_korean_style(cleaned_text)
    
    # 문단 정리
    cleaned_text = format_paragraphs(cleaned_text)
    
    # 다중 공백 정리
    cleaned_text = re.sub(r' +', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n +', '\n', cleaned_text)
    
    return cleaned_text

def main():
    if len(sys.argv) != 2:
        print("사용법: python clean_translation.py <파일경로>")
        print("예시: python clean_translation.py ko_split_000_part_04.txt")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        sys.exit(1)
    
    # 파일 읽기
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_text = f.read()
    except Exception as e:
        print(f"❌ 파일 읽기 실패: {e}")
        sys.exit(1)
    
    print(f"📖 처리 중: {file_path}")
    print(f"📏 원본 길이: {len(original_text)}자")
    
    # 후처리 적용
    cleaned_text = clean_translation(original_text)
    
    print(f"📏 정리 후 길이: {len(cleaned_text)}자")
    
    # 백업 파일 생성
    backup_path = file_path.with_suffix('.bak')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_text)
    
    # 정리된 텍스트 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    
    print(f"✅ 후처리 완료!")
    print(f"💾 백업: {backup_path}")
    print(f"📄 정리됨: {file_path}")

if __name__ == "__main__":
    main()