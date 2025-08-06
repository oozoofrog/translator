#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB 빌더 모듈

번역된 텍스트로 새로운 EPUB 파일을 생성합니다.
"""

import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path


def build_korean_epub(original_epub_path, translated_dir, output_path=None):
    """번역된 텍스트로 한글 EPUB 생성"""
    
    if output_path is None:
        base_name = Path(original_epub_path).stem
        output_path = f"{base_name}-ko.epub"
    
    # 번역 인덱스 확인
    translation_index_path = os.path.join(translated_dir, 'translation_index.json')
    if not os.path.exists(translation_index_path):
        raise FileNotFoundError(f"번역 인덱스 파일을 찾을 수 없습니다: {translation_index_path}")
    
    translated_chunks_dir = os.path.join(translated_dir, 'translated_chunks')
    if not os.path.exists(translated_chunks_dir):
        raise FileNotFoundError(f"번역된 청크 디렉토리를 찾을 수 없습니다: {translated_chunks_dir}")
    
    print(f"📚 한글 EPUB 생성 중: {output_path}")
    
    # 임시 디렉토리에서 작업
    with tempfile.TemporaryDirectory() as temp_dir:
        # 원본 EPUB 압축 해제
        with zipfile.ZipFile(original_epub_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 번역된 텍스트로 HTML 파일들 교체
        _replace_html_content(temp_dir, translated_chunks_dir)
        
        # 메타데이터 업데이트 (한글판 표시)
        _update_metadata(temp_dir)
        
        # 새로운 EPUB 파일 생성
        _create_epub_file(temp_dir, output_path)
    
    print(f"✅ 한글 EPUB 생성 완료: {output_path}")
    return output_path


def rebuild_epub_from_extracted(original_epub_path, extracted_dir, output_path=None):
    """추출된 디렉토리에서 EPUB 재구성"""
    
    if output_path is None:
        base_name = Path(original_epub_path).stem
        output_path = f"{base_name}-rebuilt.epub"
    
    print(f"📚 EPUB 재구성 중: {output_path}")
    
    # 기본적으로는 build_korean_epub과 동일한 로직
    # 하지만 번역되지 않은 원본 텍스트 사용
    
    # 임시 디렉토리에서 작업
    with tempfile.TemporaryDirectory() as temp_dir:
        # 원본 EPUB 압축 해제
        with zipfile.ZipFile(original_epub_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 새로운 EPUB 파일 생성
        _create_epub_file(temp_dir, output_path)
    
    print(f"✅ EPUB 재구성 완료: {output_path}")
    return output_path


def _replace_html_content(epub_temp_dir, translated_chunks_dir):
    """HTML 파일의 내용을 번역된 텍스트로 교체"""
    # 이 함수는 복잡한 구현이 필요합니다.
    # 현재는 placeholder로 둡니다.
    print("⚠️  HTML 내용 교체는 아직 구현되지 않았습니다.")
    print("   번역된 텍스트 파일들을 수동으로 확인해주세요.")


def _update_metadata(epub_temp_dir):
    """메타데이터에 한글판 표시 추가"""
    try:
        # OPF 파일 찾기 및 업데이트
        opf_files = list(Path(epub_temp_dir).rglob('*.opf'))
        if opf_files:
            opf_path = opf_files[0]
            print(f"📝 메타데이터 업데이트: {opf_path.name}")
            # 실제 메타데이터 업데이트 로직은 복잡하므로 placeholder
    except Exception as e:
        print(f"⚠️  메타데이터 업데이트 실패: {e}")


def _create_epub_file(source_dir, output_path):
    """디렉토리에서 EPUB 파일 생성"""
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            # mimetype 파일을 먼저 추가 (압축하지 않음)
            mimetype_path = os.path.join(source_dir, 'mimetype')
            if os.path.exists(mimetype_path):
                zip_ref.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
            
            # 나머지 파일들 추가
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    if file == 'mimetype':
                        continue  # 이미 추가됨
                    
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, source_dir)
                    zip_ref.write(file_path, arc_name)
        
        print(f"📦 EPUB 파일 생성됨: {output_path}")
        
    except Exception as e:
        print(f"❌ EPUB 생성 실패: {e}")
        raise