#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
전역 설정 파일

모든 스크립트에서 사용하는 기본값들을 중앙 집중식으로 관리합니다.
"""

# 기본 Ollama 모델 설정
DEFAULT_MODEL = "phi4:latest"

# 기본 번역 설정
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_RETRIES = 3
DEFAULT_GENRE = "fantasy"  # None이면 자동 감지

# 기본 청크 크기 설정
DEFAULT_MAX_CHUNK_SIZE = 2000
DEFAULT_MIN_CHUNK_SIZE = 1000

# 기본 캐싱 설정
DEFAULT_ENABLE_CACHE = True

# 지원하는 장르 목록
SUPPORTED_GENRES = ["fantasy", "sci-fi", "romance", "mystery", "horror", "general"]

# 번역 품질 설정
DEFAULT_NUM_GPU_LAYERS = None  # None이면 자동

# 파일 확장자
EPUB_EXTENSION = ".epub"

# 기본 디렉토리 이름
DEFAULT_TRANSLATED_DIR = "translated"
DEFAULT_EXTRACTED_SUFFIX = "_translation_work"

# 진행률 표시 설정
PROGRESS_BAR_ASCII = True  # ASCII 모드 사용
PROGRESS_BAR_NCOLS = 80    # 진행률 바 너비

def get_default_output_filename(input_file: str) -> str:
    """입력 파일명에서 기본 출력 파일명 생성"""
    import os
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    return f"{base_name}-ko{EPUB_EXTENSION}"

def get_work_directory_name(input_file: str) -> str:
    """입력 파일명에서 작업 디렉토리명 생성"""
    import os
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    return f"{base_name}{DEFAULT_EXTRACTED_SUFFIX}"