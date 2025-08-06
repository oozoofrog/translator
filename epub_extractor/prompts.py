#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
번역 프롬프트 모듈

장르별 번역 프롬프트와 설정을 관리합니다.
"""

from config.config import SUPPORTED_GENRES


def get_genre_list():
    """지원되는 장르 목록 반환"""
    return SUPPORTED_GENRES


def get_translation_prompt(genre="general"):
    """장르별 번역 프롬프트 생성"""
    base_prompt = """다음 영어 텍스트를 자연스러운 한국어로 번역해주세요.

번역 지침:
1. 원문의 의미와 뉘앙스를 정확히 전달
2. 한국어 문체와 어법에 맞게 자연스럽게 표현
3. 고유명사는 원문 그대로 유지
4. 문맥을 고려한 번역"""

    genre_specific = {
        "fantasy": """
5. 판타지 소설의 특성을 고려하여 마법, 모험 등의 용어를 적절히 번역
6. 등장인물의 대화체는 자연스럽고 생동감 있게 표현""",
        
        "sci-fi": """
5. SF 소설의 특성을 고려하여 과학기술 용어를 정확히 번역
6. 미래적 개념이나 기술 용어는 이해하기 쉽게 설명""",
        
        "romance": """
5. 로맨스 소설의 감정적 표현을 섬세하고 자연스럽게 번역
6. 등장인물 간의 감정 변화와 관계를 잘 드러내도록 번역""",
        
        "mystery": """
5. 미스터리 소설의 긴장감과 서스펜스를 잘 살려서 번역
6. 단서나 추리 과정을 명확하고 논리적으로 표현""",
        
        "horror": """
5. 공포 소설의 분위기와 긴장감을 효과적으로 전달
6. 공포스러운 장면이나 묘사를 적절히 번역""",
        
        "general": """
5. 일반적인 문학 작품의 문체와 톤을 고려하여 번역
6. 작품의 분위기와 스타일을 잘 살려서 번역"""
    }
    
    full_prompt = base_prompt + genre_specific.get(genre, genre_specific["general"])
    full_prompt += "\n\n텍스트:\n"
    
    return full_prompt


def get_system_prompt():
    """시스템 프롬프트 반환"""
    return """당신은 전문적인 영어→한국어 번역가입니다. 
문학 작품의 번역에 특화되어 있으며, 원문의 의미와 문체를 정확히 전달하면서도 
한국어로 자연스럽게 읽힐 수 있도록 번역합니다."""