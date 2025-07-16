#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB 추출기 패키지

EPUB 파일을 챕터별로 분리하고 LLM 번역에 적합한 청크로 나누는 도구입니다.

이 패키지는 다음과 같은 모듈들로 구성되어 있습니다:
- chunker: 텍스트를 지능적으로 분할하는 기능
- parser: HTML을 문단 구조를 보존하며 파싱하는 기능
- extractor: EPUB 파일을 추출하는 핵심 기능
- utils: 다양한 유틸리티 함수들
- cli: 명령줄 인터페이스
"""

__version__ = "2.0.0"
__author__ = "EPUB Extractor Team"
__license__ = "MIT"

from .extractor import EPUBExtractor

__all__ = [
    "EPUBExtractor",
]


def extract_epub(epub_path, output_dir=None, max_chunk_size=3000, min_chunk_size=1000, create_chunks=True):
    """
    EPUB 파일을 추출하는 편의 함수

    Args:
        epub_path (str): EPUB 파일 경로
        output_dir (str, optional): 출력 디렉토리
        max_chunk_size (int): 최대 청크 크기
        min_chunk_size (int): 최소 청크 크기
        create_chunks (bool): 청크 파일 생성 여부

    Returns:
        EPUBExtractor: 추출기 인스턴스

    Example:
        >>> import epub_extractor
        >>> extractor = epub_extractor.extract_epub("novel.epub")
        >>> print(f"추출된 챕터 수: {extractor.get_chapter_count()}")
    """
    extractor = EPUBExtractor(
        epub_path=epub_path, max_chunk_size=max_chunk_size, min_chunk_size=min_chunk_size, create_chunks=create_chunks
    )

    extractor.extract(output_dir)
    return extractor


def get_version():
    """
    패키지 버전 반환

    Returns:
        str: 버전 문자열
    """
    return __version__


def get_package_info():
    """
    패키지 정보 반환

    Returns:
        dict: 패키지 정보 딕셔너리
    """
    return {
        "name": "epub_extractor",
        "version": __version__,
        "author": __author__,
        "license": __license__,
        "description": "EPUB 파일을 챕터별로 분리하고 LLM 번역용 청크로 나누는 도구",
    }
