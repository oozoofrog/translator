#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB 추출기 - 모듈형 버전

모듈화된 EPUB 추출기의 메인 실행 파일입니다.
이 파일은 epub_extractor 패키지를 사용하여 간단한 인터페이스를 제공합니다.
"""

# 패키지에서 main 함수 임포트
from epub_extractor.cli import main

if __name__ == "__main__":
    main()