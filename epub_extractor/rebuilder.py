#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB 재구성 모듈

추출된 HTML 파일들을 다시 EPUB으로 재구성하는 기능을 제공합니다.
번역되지 않은 원본 HTML 파일들을 그대로 사용하여 EPUB을 재생성합니다.
"""

import zipfile
import json
import os
import shutil
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET


class EPUBRebuilder:
    """추출된 HTML 파일들을 EPUB으로 재구성하는 클래스"""
    
    def __init__(self, original_epub_path, extracted_dir):
        """
        EPUB 재구성기 초기화
        
        Args:
            original_epub_path (str): 원본 EPUB 파일 경로
            extracted_dir (str): 추출된 HTML 파일이 있는 디렉토리
        """
        self.original_epub_path = original_epub_path
        self.extracted_dir = Path(extracted_dir)
        self.original_epub = None
        self.temp_dir = None
        self.info_data = None
        
    def rebuild_epub(self, output_path=None):
        """
        추출된 HTML 파일들을 사용하여 EPUB 파일 재구성
        
        Args:
            output_path (str, optional): 출력 EPUB 파일 경로. None이면 자동 생성.
            
        Returns:
            str: 생성된 EPUB 파일 경로
        """
        if output_path is None:
            base_name = Path(self.original_epub_path).stem
            output_path = f"{base_name}-rebuilt.epub"
        
        print(f"📚 EPUB 재구성 시작...")
        
        try:
            # 1. 정보 파일 로드
            self._load_info_file()
            
            # 2. 임시 디렉토리 생성
            self.temp_dir = tempfile.mkdtemp()
            print(f"📁 임시 디렉토리 생성: {self.temp_dir}")
            
            # 3. 원본 EPUB 추출
            self._extract_original_epub()
            
            # 4. HTML 파일 교체
            self._replace_html_files()
            
            # 5. 새 EPUB 생성
            self._create_new_epub(output_path)
            
            print(f"✅ EPUB 재구성 완료: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ EPUB 재구성 중 오류 발생: {e}")
            raise
        finally:
            # 임시 디렉토리 정리
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("🗑️  임시 파일 정리 완료")
                
    def _load_info_file(self):
        """info.json 파일 로드"""
        info_file = self.extracted_dir / 'info.json'
        if not info_file.exists():
            raise FileNotFoundError(f"info.json 파일을 찾을 수 없습니다: {info_file}")
            
        with open(info_file, 'r', encoding='utf-8') as f:
            self.info_data = json.load(f)
        
        print(f"📄 정보 파일 로드 완료")
        
    def _extract_original_epub(self):
        """원본 EPUB 파일을 임시 디렉토리에 추출"""
        self.original_epub = zipfile.ZipFile(self.original_epub_path, 'r')
        self.original_epub.extractall(self.temp_dir)
        self.original_epub.close()
        
        print(f"📖 원본 EPUB 추출 완료")
        
    def _replace_html_files(self):
        """추출된 HTML 파일들로 교체"""
        chapters_dir = self.extracted_dir / 'chapters'
        if not chapters_dir.exists():
            raise FileNotFoundError(f"chapters 디렉토리를 찾을 수 없습니다: {chapters_dir}")
        
        replaced_count = 0
        
        # 각 챕터 정보를 순회하며 HTML 파일 교체
        for chapter in self.info_data.get('chapters', []):
            chapter_name = chapter['name']
            original_path = chapter['file_path']
            
            # 추출된 HTML 파일 경로
            extracted_html = chapters_dir / f"{chapter_name}.html"
            
            if extracted_html.exists():
                # 임시 디렉토리의 대상 파일 경로
                target_path = os.path.join(self.temp_dir, original_path)
                
                # 디렉토리가 없으면 생성
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # HTML 파일 복사
                shutil.copy2(extracted_html, target_path)
                replaced_count += 1
                print(f"📝 교체: {chapter_name}.html → {original_path}")
            else:
                print(f"⚠️  경고: {chapter_name}.html 파일을 찾을 수 없습니다")
        
        print(f"✅ {replaced_count}개 HTML 파일 교체 완료")
        
    def _create_new_epub(self, output_path):
        """새로운 EPUB 파일 생성"""
        # 기존 파일이 있으면 삭제
        if os.path.exists(output_path):
            os.remove(output_path)
        
        # 새 EPUB 파일 생성
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as new_epub:
            # mimetype 파일은 압축하지 않고 첫 번째로 추가
            mimetype_path = os.path.join(self.temp_dir, 'mimetype')
            if os.path.exists(mimetype_path):
                new_epub.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
            
            # 나머지 파일들 추가
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    if file == 'mimetype':
                        continue  # 이미 추가함
                        
                    file_path = os.path.join(root, file)
                    # ZIP 파일 내 경로 계산
                    arc_path = os.path.relpath(file_path, self.temp_dir)
                    new_epub.write(file_path, arc_path)


def rebuild_epub_from_extracted(original_epub, extracted_dir, output_path=None):
    """
    추출된 HTML 파일들로부터 EPUB 재구성 (편의 함수)
    
    Args:
        original_epub (str): 원본 EPUB 파일 경로
        extracted_dir (str): 추출된 HTML 파일이 있는 디렉토리
        output_path (str, optional): 출력 EPUB 파일 경로
        
    Returns:
        str: 생성된 EPUB 파일 경로
    """
    rebuilder = EPUBRebuilder(original_epub, extracted_dir)
    return rebuilder.rebuild_epub(output_path)