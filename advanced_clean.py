#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 번역 후처리 - 모든 문체를 통일된 문어체로 변환
"""

import sys
import re
from pathlib import Path

def comprehensive_style_fix(text: str) -> str:
    """포괄적인 문체 수정"""
    
    # 1단계: 기본 구어체 패턴들
    patterns_1 = [
        # 존댓말 계열
        (r'습니다\.', '다.'),
        (r'습니다,', '다,'),
        (r'습니다;', '다;'),
        (r'했습니다\.', '했다.'),
        (r'였습니다\.', '였다.'),
        (r'었습니다\.', '었다.'),
        (r'입니다\.', '이다.'),
        (r'세요\.', '다.'),
        
        # 해요체
        (r'해요\.', '한다.'),
        (r'해요,', '한다,'),
        (r'해요;', '한다;'),
        (r'했어요\.', '했다.'),
        (r'했어요,', '했다,'),
        (r'였어요\.', '였다.'),
        (r'었어요\.', '었다.'),
        (r'이에요\.', '이다.'),
        (r'예요\.', '다.'),
        
        # 해체
        (r'했어\.', '했다.'),
        (r'했어,', '했다,'),
        (r'였어\.', '였다.'),
        (r'었어\.', '었다.'),
        (r'해\.', '한다.'),
        (r'해,', '한다,'),
        (r'이야\.', '이다.'),
        (r'야\.', '다.'),
        
        # 특수 구어체 표현
        (r'다네\.', '다.'),
        (r'단다\.', '다.'),
        (r'지\.', '다.'),
        (r'구나\.', '다.'),
        (r'네\.', '다.'),
        (r'죠\.', '다.'),
        (r'죠,', '다,'),
        (r'죠;', '다;'),
        (r'거예요\.', '것이다.'),
        (r'거야\.', '것이다.'),
        (r'거네\.', '것이다.'),
        
        # 의문문
        (r'해요\?', '하는가?'),
        (r'해\?', '하는가?'),
        (r'이에요\?', '인가?'),
        (r'예요\?', '인가?'),
        (r'야\?', '인가?'),
        (r'나요\?', '는가?'),
        
        # 감탄문
        (r'해요!', '한다!'),
        (r'해!', '한다!'),
        (r'이에요!', '이다!'),
        (r'예요!', '다!'),
    ]
    
    # 2단계: 복합 표현들
    patterns_2 = [
        # 복합 동사들
        (r'보였어요', '보였다'),
        (r'보였어', '보였다'),
        (r'했던 것 같아요', '했던 것 같다'),
        (r'한 것 같아요', '한 것 같다'),
        (r'할 수 있어요', '할 수 있다'),
        (r'할 수 있어', '할 수 있다'),
        (r'하고 있어요', '하고 있다'),
        (r'하고 있어', '하고 있다'),
        
        # 형용사들
        (r'좋아요', '좋다'),
        (r'나빠요', '나쁘다'),
        (r'커요', '크다'),
        (r'작아요', '작다'),
        (r'많아요', '많다'),
        (r'적어요', '적다'),
    ]
    
    # 3단계: 잔존 구어체 찾기 및 수정
    patterns_3 = [
        # 어미 + 요 패턴
        (r'([가-힣]+)요\.', r'\1다.'),
        (r'([가-힣]+)요,', r'\1다,'),
        (r'([가-힣]+)요;', r'\1다;'),
        
        # 어미 + 어 패턴 (대화문 제외)
        (r'(?<!")([가-힣]+)어\.', r'\1었다.'),
        (r'(?<!")([가-힣]+)어,', r'\1었다,'),
    ]
    
    # 단계별 적용
    for pattern, replacement in patterns_1:
        text = re.sub(pattern, replacement, text)
    
    for pattern, replacement in patterns_2:
        text = re.sub(pattern, replacement, text)
    
    # 3단계는 신중하게 적용 (대화문 보호)
    # for pattern, replacement in patterns_3:
    #     text = re.sub(pattern, replacement, text)
    
    return text

def fix_specific_issues(text: str) -> str:
    """특정 문제들 수정"""
    
    # 관찰하다 → 관찰한다
    text = re.sub(r'관찰하니까요', '관찰한다', text)
    text = re.sub(r'관찰하다', '관찰한다', text)
    
    # 기타 특정 표현들
    text = re.sub(r'기다리시는', '기다리고 있는', text)
    text = re.sub(r'그러했죠', '그러했다', text)
    text = re.sub(r'놓여 있어요', '놓여 있다', text)
    text = re.sub(r'비어있습니다', '비어있다', text)
    
    return text

def format_paragraphs(text: str) -> str:
    """문단 정리"""
    
    # 대화문 후 문단 분리
    text = re.sub(r'(\"[^\"]*\"\.) ([가-힣])', r'\1\n\n\2', text)
    
    # 문장 길이가 긴 경우 자연스러운 분리점에서 문단 나누기
    # 접속사나 전환 표현 앞에서
    connectors = ['그런데', '그러나', '그래서', '하지만', '그리고', '그때', '그는', '그녀', 
                  '한편', '반면', '그러자', '그리하여', '이때', '이에', '따라서']
    
    for connector in connectors:
        pattern = f'(\\.) ({connector})'
        text = re.sub(pattern, r'.\n\n\2', text)
    
    # 연속된 개행 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

def clean_translation_advanced(text: str) -> str:
    """고급 번역 정리"""
    
    # 기본 정리
    cleaned_text = text.strip()
    
    # _TAB_ 제거
    cleaned_text = cleaned_text.replace('_TAB_', ' ')
    
    # <think> 태그 제거
    cleaned_text = re.sub(r'<think>.*?</think>', '', cleaned_text, flags=re.DOTALL)
    
    # 문체 통일
    cleaned_text = comprehensive_style_fix(cleaned_text)
    
    # 특정 문제 수정
    cleaned_text = fix_specific_issues(cleaned_text)
    
    # 문단 정리
    cleaned_text = format_paragraphs(cleaned_text)
    
    # 공백 정리
    cleaned_text = re.sub(r' +', ' ', cleaned_text)
    cleaned_text = re.sub(r'\n +', '\n', cleaned_text)
    cleaned_text = re.sub(r' +\n', '\n', cleaned_text)
    
    return cleaned_text

def main():
    if len(sys.argv) != 2:
        print("사용법: python advanced_clean.py <파일경로>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    
    if not file_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        sys.exit(1)
    
    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    print(f"📖 고급 후처리 중: {file_path}")
    print(f"📏 원본 길이: {len(original_text)}자")
    
    # 고급 후처리 적용
    cleaned_text = clean_translation_advanced(original_text)
    
    print(f"📏 정리 후 길이: {len(cleaned_text)}자")
    
    # 백업 파일 생성
    backup_path = file_path.with_suffix('.advanced.bak')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_text)
    
    # 정리된 텍스트 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    
    print(f"✅ 고급 후처리 완료!")
    print(f"💾 백업: {backup_path}")
    print(f"📄 정리됨: {file_path}")

if __name__ == "__main__":
    main()