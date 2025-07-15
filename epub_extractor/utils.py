#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
유틸리티 모듈

EPUB 추출 과정에서 사용되는 다양한 유틸리티 함수들을 제공합니다.
"""

import os
import re


def extract_chapter_name(file_path, order):
    """
    파일 경로에서 챕터명 추출

    Args:
        file_path (str): 파일 경로
        order (int): 챕터 순서

    Returns:
        str: 정리된 챕터명
    """
    filename = os.path.basename(file_path)
    name = os.path.splitext(filename)[0]

    # 일반적인 패턴들 정리
    name = re.sub(r"^(chapter|ch|part|section)[\s_-]*", "", name, flags=re.IGNORECASE)
    name = re.sub(r"^\d+[\s_-]*", "", name)

    if not name or name.isdigit():
        name = f"Chapter_{order:03d}"

    # 파일명으로 사용할 수 없는 문자 제거
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip("_")

    return name


def should_skip_chapter(filename, chapter_name):
    """
    챕터를 건너뛸지 판단 (titlepage, cover 등 불필요한 내용)

    Args:
        filename (str): 원본 파일명
        chapter_name (str): 추출된 챕터명

    Returns:
        bool: 건너뛸 경우 True
    """
    skip_patterns = [
        r"title.*page",
        r"cover",
        r"copyright",
        r"toc",
        r"table.*of.*contents",
        r"front.*matter",
        r"dedication",
        r"epigraph",
    ]

    filename_lower = filename.lower()
    chapter_name_lower = chapter_name.lower()

    for pattern in skip_patterns:
        if re.search(pattern, filename_lower) or re.search(pattern, chapter_name_lower):
            return True

    return False


def clean_text(text):
    """
    텍스트 정리 (과도한 공백, 줄바꿈 제거)

    Args:
        text (str): 정리할 텍스트

    Returns:
        str: 정리된 텍스트
    """
    # 과도한 줄바꿈 제거
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 과도한 공백 제거
    text = re.sub(r"[ \t]+", " ", text)

    # 줄 시작/끝 공백 제거
    lines = text.split("\n")
    lines = [line.strip() for line in lines]
    text = "\n".join(lines)

    return text.strip()


def validate_chunk_sizes(max_chunk_size, min_chunk_size):
    """
    청크 크기 설정 검증

    Args:
        max_chunk_size (int): 최대 청크 크기
        min_chunk_size (int): 최소 청크 크기

    Returns:
        bool: 유효한 설정인 경우 True

    Raises:
        ValueError: 잘못된 설정인 경우
    """
    if max_chunk_size <= 0:
        raise ValueError("최대 청크 크기는 0보다 커야 합니다.")

    if min_chunk_size <= 0:
        raise ValueError("최소 청크 크기는 0보다 커야 합니다.")

    if max_chunk_size < min_chunk_size:
        raise ValueError("최대 청크 크기가 최소 청크 크기보다 작습니다.")

    if min_chunk_size < 100:
        print("⚠️  경고: 최소 청크 크기가 너무 작습니다 (권장: 100자 이상)")

    if max_chunk_size > 10000:
        print("⚠️  경고: 최대 청크 크기가 너무 큽니다 (권장: 10000자 이하)")

    return True


def get_common_opf_paths():
    """
    일반적인 OPF 파일 경로들 반환

    Returns:
        List[str]: OPF 파일 경로 후보들
    """
    return ["OEBPS/content.opf", "content.opf", "EPUB/content.opf", "OPS/content.opf", "book.opf"]


def normalize_path(path):
    """
    경로 정규화 (슬래시 통일, 중복 제거)

    Args:
        path (str): 정규화할 경로

    Returns:
        str: 정규화된 경로
    """
    if not path:
        return ""

    # 백슬래시를 슬래시로 변환
    path = path.replace("\\", "/")

    # 중복 슬래시 제거
    path = re.sub(r"/+", "/", path)

    # 시작 슬래시 제거
    path = path.lstrip("/")

    return path


def format_file_size(size_bytes):
    """
    바이트 크기를 읽기 쉬운 형태로 변환

    Args:
        size_bytes (int): 바이트 크기

    Returns:
        str: 형식화된 크기 문자열
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def create_safe_filename(text, max_length=100):
    """
    안전한 파일명 생성 (운영체제 호환)

    Args:
        text (str): 원본 텍스트
        max_length (int): 최대 길이

    Returns:
        str: 안전한 파일명
    """
    # 위험한 문자들 제거/변환
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", text)

    # 연속된 언더스코어 제거
    safe_name = re.sub(r"_+", "_", safe_name)

    # 앞뒤 언더스코어 제거
    safe_name = safe_name.strip("_")

    # 길이 제한
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length].rstrip("_")

    # 빈 문자열 방지
    if not safe_name:
        safe_name = "untitled"

    return safe_name
