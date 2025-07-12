#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB 빌더 모듈

번역된 청크들을 다시 EPUB 파일로 재조립하는 기능을 제공합니다.
"""

import zipfile
import json
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET


class EPUBBuilder:
    """번역된 텍스트를 EPUB 파일로 재조립하는 클래스"""
    
    def __init__(self, original_epub_path, translated_dir):
        """
        EPUB 빌더 초기화
        
        Args:
            original_epub_path (str): 원본 EPUB 파일 경로
            translated_dir (str): 번역된 텍스트가 있는 디렉토리
        """
        self.original_epub_path = original_epub_path
        self.translated_dir = Path(translated_dir)
        self.original_epub = None
        self.temp_dir = None
        self.info_data = None
        self.translation_index = None
        
    def build_korean_epub(self, output_path=None):
        """
        번역된 텍스트를 사용하여 한글 EPUB 파일 생성
        
        Args:
            output_path (str, optional): 출력 EPUB 파일 경로. None이면 자동 생성.
            
        Returns:
            str: 생성된 EPUB 파일 경로
        """
        if output_path is None:
            base_name = Path(self.original_epub_path).stem
            output_path = f"{base_name}-ko.epub"
        
        try:
            # 필요한 데이터 로드
            self._load_translation_data()
            
            # 임시 작업 디렉토리 생성
            self.temp_dir = tempfile.mkdtemp()
            
            # 원본 EPUB 구조 복사
            self._extract_original_structure()
            
            # 번역된 텍스트로 HTML 파일들 교체
            self._replace_content_with_translation()
            
            # 메타데이터 업데이트 (한국어 표시 추가)
            self._update_metadata()
            
            # 새로운 EPUB 파일 생성
            self._create_epub_file(output_path)
            
            print(f"✅ 한글 EPUB 생성 완료: {output_path}")
            return output_path
            
        finally:
            self._cleanup()
    
    def _load_translation_data(self):
        """번역 관련 데이터 로드"""
        # info.json 로드
        info_file = self.translated_dir.parent / "info.json"
        if not info_file.exists():
            raise FileNotFoundError(f"원본 정보 파일을 찾을 수 없습니다: {info_file}")
        
        with open(info_file, 'r', encoding='utf-8') as f:
            self.info_data = json.load(f)
        
        # translation_index.json 로드
        translation_index_file = self.translated_dir / "translation_index.json"
        if not translation_index_file.exists():
            raise FileNotFoundError(f"번역 인덱스 파일을 찾을 수 없습니다: {translation_index_file}")
        
        with open(translation_index_file, 'r', encoding='utf-8') as f:
            self.translation_index = json.load(f)
    
    def _extract_original_structure(self):
        """원본 EPUB 구조를 임시 디렉토리에 추출"""
        with zipfile.ZipFile(self.original_epub_path, 'r') as epub_zip:
            epub_zip.extractall(self.temp_dir)
        
        print("📦 원본 EPUB 구조 추출 완료")
    
    def _replace_content_with_translation(self):
        """HTML 파일들의 내용을 번역된 텍스트로 교체"""
        # 번역된 텍스트 재조립
        translated_chapters = self._reassemble_translated_text()
        
        # 챕터별 HTML 파일 교체
        for chapter_info in self.info_data['chapters']:
            chapter_name = chapter_info['name']
            
            if chapter_name in translated_chapters:
                self._update_html_file(chapter_info, translated_chapters[chapter_name])
                print(f"📝 {chapter_name} 번역 적용")
            else:
                print(f"⚠️  {chapter_name} 번역을 찾을 수 없음")
    
    def _reassemble_translated_text(self):
        """번역된 청크들을 챕터별로 재조립"""
        translated_chunks_dir = self.translated_dir / "translated_chunks"
        chunk_index_file = self.translated_dir.parent / "chunks" / "chunk_index.json"
        
        # 청크 인덱스 로드
        with open(chunk_index_file, 'r', encoding='utf-8') as f:
            chunk_index = json.load(f)
        
        # 챕터별로 청크들 그룹화
        chapters = {}
        for chunk_info in chunk_index['chunks']:
            chapter_name = chunk_info['chapter']
            chunk_file = chunk_info['file']
            ko_chunk_file = f"ko_{chunk_file}"
            
            # 번역된 청크 파일 읽기
            ko_chunk_path = translated_chunks_dir / ko_chunk_file
            if ko_chunk_path.exists():
                with open(ko_chunk_path, 'r', encoding='utf-8') as f:
                    chunk_content = f.read()
                
                if chapter_name not in chapters:
                    chapters[chapter_name] = []
                
                chapters[chapter_name].append(chunk_content)
        
        # 챕터별로 청크들 합치기
        assembled_chapters = {}
        for chapter_name, chunks in chapters.items():
            # 청크들을 순서대로 합치기 (이미 올바른 순서로 저장됨)
            assembled_text = '\n\n'.join(chunks)
            assembled_chapters[chapter_name] = assembled_text
        
        print(f"🔗 {len(assembled_chapters)}개 챕터 재조립 완료")
        return assembled_chapters
    
    def _update_html_file(self, chapter_info, translated_text):
        """개별 HTML 파일을 번역된 텍스트로 업데이트"""
        original_filename = chapter_info['original_filename']
        
        # 원본 HTML 파일 찾기
        html_file_path = None
        for root, dirs, files in os.walk(self.temp_dir):
            if original_filename in files:
                html_file_path = os.path.join(root, original_filename)
                break
        
        if not html_file_path:
            print(f"⚠️  HTML 파일을 찾을 수 없음: {original_filename}")
            return
        
        # 번역된 텍스트를 HTML 형태로 변환
        translated_html = self._text_to_html(translated_text)
        
        # HTML 파일 업데이트
        try:
            # 기존 HTML 파일 읽기
            with open(html_file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # HTML 구조 유지하면서 본문만 교체
            updated_content = self._replace_html_body(original_content, translated_html)
            
            # 파일 저장
            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
        except Exception as e:
            print(f"⚠️  HTML 파일 업데이트 오류 ({original_filename}): {e}")
    
    def _text_to_html(self, text):
        """일반 텍스트를 HTML 문단으로 변환"""
        # 빈 줄로 구분된 문단들을 <p> 태그로 감싸기
        paragraphs = text.split('\n\n')
        html_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if para:
                # 줄바꿈을 <br/> 태그로 변환
                para = para.replace('\n', '<br/>')
                html_paragraphs.append(f'<p>{para}</p>')
        
        return '\n'.join(html_paragraphs)
    
    def _replace_html_body(self, original_html, new_body_content):
        """HTML 파일의 body 내용만 교체"""
        try:
            # XML/HTML 파싱 시도
            root = ET.fromstring(original_html)
            
            # body 태그 찾기
            body = root.find('.//body')
            if body is not None:
                # body 내용 모두 제거
                body.clear()
                body.text = None
                body.tail = None
                
                # 새로운 내용을 XML 요소로 추가
                temp_html = f"<div>{new_body_content}</div>"
                temp_root = ET.fromstring(temp_html)
                
                for child in temp_root:
                    body.append(child)
                
                # XML을 문자열로 변환
                return ET.tostring(root, encoding='unicode', method='html')
            else:
                # body 태그가 없는 경우 간단한 문자열 교체
                return self._simple_body_replace(original_html, new_body_content)
                
        except ET.ParseError:
            # XML 파싱 실패 시 간단한 문자열 교체
            return self._simple_body_replace(original_html, new_body_content)
    
    def _simple_body_replace(self, original_html, new_body_content):
        """간단한 문자열 교체로 body 내용 변경"""
        import re
        
        # body 태그 내용 찾아서 교체
        body_pattern = r'(<body[^>]*>)(.*?)(</body>)'
        
        def replace_body(match):
            return f"{match.group(1)}\n{new_body_content}\n{match.group(3)}"
        
        updated_html = re.sub(body_pattern, replace_body, original_html, flags=re.DOTALL | re.IGNORECASE)
        
        # body 태그가 없는 경우 전체 내용 교체
        if updated_html == original_html:
            return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Translated Chapter</title>
</head>
<body>
{new_body_content}
</body>
</html>"""
        
        return updated_html
    
    def _update_metadata(self):
        """OPF 파일의 메타데이터 업데이트 (한국어 표시)"""
        # OPF 파일 찾기
        opf_files = []
        for root, dirs, files in os.walk(self.temp_dir):
            for file in files:
                if file.endswith('.opf'):
                    opf_files.append(os.path.join(root, file))
        
        if not opf_files:
            print("⚠️  OPF 파일을 찾을 수 없음")
            return
        
        opf_path = opf_files[0]  # 첫 번째 OPF 파일 사용
        
        try:
            # OPF 파일 읽기
            with open(opf_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # XML 파싱
            root = ET.fromstring(content)
            
            # namespace 정의
            ns = {
                'opf': 'http://www.idpf.org/2007/opf',
                'dc': 'http://purl.org/dc/elements/1.1/'
            }
            
            # 제목에 [한글판] 추가
            title_elem = root.find('.//dc:title', ns)
            if title_elem is not None and title_elem.text:
                if '[한글판]' not in title_elem.text:
                    title_elem.text = f"{title_elem.text} [한글판]"
            
            # 언어를 한국어로 변경
            lang_elem = root.find('.//dc:language', ns)
            if lang_elem is not None:
                lang_elem.text = 'ko'
            
            # 번역 정보 추가
            metadata_elem = root.find('.//opf:metadata', ns)
            if metadata_elem is not None:
                # 번역자 정보 추가
                translator_elem = ET.SubElement(metadata_elem, '{http://purl.org/dc/elements/1.1/}contributor')
                translator_elem.text = 'Ollama AI Translation'
                translator_elem.set('opf:role', 'trl')
                
                # 번역 날짜 추가
                date_elem = ET.SubElement(metadata_elem, '{http://purl.org/dc/elements/1.1/}date')
                date_elem.text = datetime.now().strftime('%Y-%m-%d')
                date_elem.set('opf:event', 'translation')
            
            # 업데이트된 내용 저장
            updated_content = ET.tostring(root, encoding='unicode', method='xml')
            
            # XML 선언 추가
            if not updated_content.startswith('<?xml'):
                updated_content = '<?xml version="1.0" encoding="utf-8"?>\n' + updated_content
            
            with open(opf_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("📝 메타데이터 업데이트 완료 (한글판 표시 추가)")
            
        except Exception as e:
            print(f"⚠️  메타데이터 업데이트 오류: {e}")
    
    def _create_epub_file(self, output_path):
        """임시 디렉토리 내용을 EPUB 파일로 압축"""
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
            # mimetype 파일 먼저 추가 (압축 없이)
            mimetype_path = os.path.join(self.temp_dir, 'mimetype')
            if os.path.exists(mimetype_path):
                epub_zip.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
            
            # 나머지 파일들 추가
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    if file == 'mimetype':
                        continue  # 이미 추가함
                    
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, self.temp_dir)
                    epub_zip.write(file_path, arc_path)
        
        print(f"📦 EPUB 파일 생성: {output_path}")
    
    def _cleanup(self):
        """임시 파일들 정리"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


def build_korean_epub(original_epub_path, translated_dir, output_path=None):
    """
    편의 함수: 번역된 텍스트로 한글 EPUB 생성
    
    Args:
        original_epub_path (str): 원본 EPUB 파일 경로
        translated_dir (str): 번역 결과 디렉토리
        output_path (str, optional): 출력 EPUB 파일 경로
        
    Returns:
        str: 생성된 EPUB 파일 경로
    """
    builder = EPUBBuilder(original_epub_path, translated_dir)
    return builder.build_korean_epub(output_path)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="번역된 텍스트로 한글 EPUB 생성")
    parser.add_argument("original_epub", help="원본 EPUB 파일 경로")
    parser.add_argument("translated_dir", help="번역 결과 디렉토리")
    parser.add_argument("--output", "-o", help="출력 EPUB 파일 경로")
    
    args = parser.parse_args()
    
    try:
        output_file = build_korean_epub(args.original_epub, args.translated_dir, args.output)
        print(f"\n✅ 한글 EPUB 생성 완료: {output_file}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")