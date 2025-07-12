#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile
import xml.etree.ElementTree as ET
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

class EPUBExtractor:
    def __init__(self, epub_path):
        self.epub_path = epub_path
        self.zip_file = None
        self.opf_path = None
        self.chapters = []
        
    def extract(self, output_dir=None):
        """EPUB 파일을 챕터별로 분리"""
        if output_dir is None:
            output_dir = Path(self.epub_path).stem
            
        try:
            # EPUB 파일 열기
            self.zip_file = zipfile.ZipFile(self.epub_path, 'r')
            
            # OPF 파일 경로 찾기
            self._find_opf_path()
            
            # 목차 추출
            self._extract_toc()
            
            # 출력 디렉토리 생성
            os.makedirs(output_dir, exist_ok=True)
            
            # 챕터별 파일 생성
            self._create_chapter_files(output_dir)
            
            print(f"✅ 추출 완료: {len(self.chapters)}개 챕터가 '{output_dir}' 디렉토리에 생성되었습니다.")
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        finally:
            if self.zip_file:
                self.zip_file.close()
    
    def _find_opf_path(self):
        """container.xml에서 OPF 파일 경로 찾기"""
        container_xml = self.zip_file.read('META-INF/container.xml')
        root = ET.fromstring(container_xml)
        
        # namespace 처리
        ns = {'container': 'urn:oasis:names:tc:opendocument:xmlns:container'}
        rootfile = root.find('.//container:rootfile', ns)
        
        if rootfile is not None:
            self.opf_path = rootfile.get('full-path')
        else:
            # fallback: 일반적인 경로들 시도
            possible_paths = ['OEBPS/content.opf', 'content.opf', 'EPUB/content.opf']
            for path in possible_paths:
                if path in self.zip_file.namelist():
                    self.opf_path = path
                    break
    
    def _extract_toc(self):
        """OPF 파일에서 목차 정보 추출"""
        if not self.opf_path:
            raise Exception("OPF 파일을 찾을 수 없습니다.")
            
        opf_content = self.zip_file.read(self.opf_path)
        root = ET.fromstring(opf_content)
        
        # namespace 처리
        ns = {'opf': 'http://www.idpf.org/2007/opf'}
        
        # manifest에서 파일 정보 수집
        manifest_items = {}
        for item in root.findall('.//opf:item', ns):
            item_id = item.get('id')
            href = item.get('href')
            if href and item_id:
                manifest_items[item_id] = href
        
        # spine에서 읽기 순서 확인
        spine_items = []
        for itemref in root.findall('.//opf:itemref', ns):
            idref = itemref.get('idref')
            if idref in manifest_items:
                spine_items.append(manifest_items[idref])
        
        # 챕터 정보 생성
        base_dir = os.path.dirname(self.opf_path)
        for i, href in enumerate(spine_items, 1):
            file_path = os.path.join(base_dir, href) if base_dir else href
            
            # 파일명에서 챕터명 추출
            chapter_name = self._extract_chapter_name(file_path, i)
            
            self.chapters.append({
                'name': chapter_name,
                'file_path': file_path,
                'order': i
            })
    
    def _extract_chapter_name(self, file_path, order):
        """파일 경로에서 챕터명 추출"""
        filename = os.path.basename(file_path)
        name = os.path.splitext(filename)[0]
        
        # 일반적인 패턴들 정리
        name = re.sub(r'^(chapter|ch|part|section)[\s_-]*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'^\d+[\s_-]*', '', name)
        
        if not name or name.isdigit():
            name = f"Chapter_{order:03d}"
        
        # 파일명으로 사용할 수 없는 문자 제거
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        
        return name
    
    def _create_chapter_files(self, output_dir):
        """챕터별 파일 생성"""
        for chapter in self.chapters:
            try:
                # EPUB 내 파일 읽기
                content = self.zip_file.read(chapter['file_path']).decode('utf-8')
                
                # HTML 태그 제거하고 텍스트만 추출
                text_content = self._extract_text_from_html(content)
                
                # 파일 저장
                output_file = os.path.join(output_dir, f"{chapter['name']}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                print(f"📄 생성됨: {chapter['name']}.txt")
                
            except Exception as e:
                print(f"⚠️  챕터 '{chapter['name']}' 처리 중 오류: {e}")
    
    def _extract_text_from_html(self, html_content):
        """HTML에서 텍스트 추출"""
        # 간단한 HTML 태그 제거
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        
        # HTML 엔티티 디코딩
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        
        # 공백 정리
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()

def main():
    if len(sys.argv) != 2:
        print("사용법: python epub_extractor.py <epub_파일_경로>")
        sys.exit(1)
    
    epub_path = sys.argv[1]
    
    if not os.path.exists(epub_path):
        print(f"❌ 파일을 찾을 수 없습니다: {epub_path}")
        sys.exit(1)
    
    if not epub_path.lower().endswith('.epub'):
        print("❌ EPUB 파일이 아닙니다.")
        sys.exit(1)
    
    extractor = EPUBExtractor(epub_path)
    extractor.extract()

if __name__ == "__main__":
    main()