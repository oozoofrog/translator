#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import zipfile
import xml.etree.ElementTree as ET
import os
import re
import sys
import json
import argparse
import html.parser
from pathlib import Path
from urllib.parse import unquote

class TextChunker:
    """LLM 번역에 적합한 크기로 텍스트를 지능적으로 분할하는 클래스"""
    
    def __init__(self, max_chunk_size=3000, min_chunk_size=1000):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
    
    def chunk_text(self, text, chapter_name=""):
        """텍스트를 적절한 크기의 청크로 분할"""
        chunks = []
        
        # 1단계: 문단별로 분할 시도
        paragraphs = self._split_paragraphs(text)
        current_chunk = ""
        chunk_number = 1
        
        for paragraph in paragraphs:
            # 현재 청크에 문단을 추가해도 크기가 적당한 경우
            if len(current_chunk + "\n\n" + paragraph) <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 현재 청크 저장 (크기가 충분한 경우)
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'name': f"{chapter_name}_part_{chunk_number:02d}",
                        'size': len(current_chunk)
                    })
                    chunk_number += 1
                    current_chunk = paragraph
                else:
                    # 크기가 작으면 현재 문단과 합쳐서 계속
                    current_chunk += "\n\n" + paragraph
                
                # 문단이 너무 큰 경우 문장별로 분할
                if len(current_chunk) > self.max_chunk_size:
                    sentence_chunks = self._split_by_sentences(current_chunk, chapter_name, chunk_number)
                    chunks.extend(sentence_chunks)
                    chunk_number += len(sentence_chunks)
                    current_chunk = ""
        
        # 마지막 청크 처리
        if current_chunk.strip():
            if len(current_chunk) >= self.min_chunk_size or not chunks:
                chunks.append({
                    'content': current_chunk.strip(),
                    'name': f"{chapter_name}_part_{chunk_number:02d}",
                    'size': len(current_chunk)
                })
            else:
                # 마지막 청크가 너무 작으면 이전 청크와 병합
                if chunks:
                    chunks[-1]['content'] += "\n\n" + current_chunk.strip()
                    chunks[-1]['size'] = len(chunks[-1]['content'])
        
        return chunks
    
    def _split_paragraphs(self, text):
        """텍스트를 문단별로 분할"""
        # 연속된 줄바꿈을 문단 구분자로 사용
        paragraphs = re.split(r'\n\s*\n', text.strip())
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _split_by_sentences(self, text, chapter_name, start_chunk_num):
        """긴 문단을 문장별로 분할"""
        chunks = []
        # 문장 구분자: . ! ? 뒤에 공백이나 줄바꿈
        sentences = re.split(r'([.!?])\s+', text)
        
        current_chunk = ""
        chunk_number = start_chunk_num
        
        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else "")
            
            if len(current_chunk + " " + sentence) <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'name': f"{chapter_name}_part_{chunk_number:02d}",
                        'size': len(current_chunk)
                    })
                    chunk_number += 1
                
                # 문장이 여전히 너무 긴 경우 단어별로 분할
                if len(sentence) > self.max_chunk_size:
                    word_chunks = self._split_by_words(sentence, chapter_name, chunk_number)
                    chunks.extend(word_chunks)
                    chunk_number += len(word_chunks)
                    current_chunk = ""
                else:
                    current_chunk = sentence
        
        # 마지막 청크 처리
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'name': f"{chapter_name}_part_{chunk_number:02d}",
                'size': len(current_chunk)
            })
        
        return chunks
    
    def _split_by_words(self, text, chapter_name, start_chunk_num):
        """긴 문장을 단어별로 분할 (최후 수단)"""
        chunks = []
        words = text.split()
        current_chunk = ""
        chunk_number = start_chunk_num
        
        for word in words:
            if len(current_chunk + " " + word) <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word
            else:
                if current_chunk:
                    chunks.append({
                        'content': current_chunk.strip(),
                        'name': f"{chapter_name}_part_{chunk_number:02d}",
                        'size': len(current_chunk)
                    })
                    chunk_number += 1
                current_chunk = word
        
        if current_chunk.strip():
            chunks.append({
                'content': current_chunk.strip(),
                'name': f"{chapter_name}_part_{chunk_number:02d}",
                'size': len(current_chunk)
            })
        
        return chunks


class ImprovedHTMLParser(html.parser.HTMLParser):
    """문단 구조를 보존하는 HTML 파서"""
    
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.current_paragraph = []
        self.in_paragraph = False
        self.skip_tags = {'script', 'style', 'head', 'title'}
        self.current_tag = None
    
    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.skip_tags:
            self.current_tag = tag.lower()
            return
            
        if tag.lower() in {'p', 'div', 'section', 'article', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            if self.current_paragraph:
                self.text_content.append(' '.join(self.current_paragraph))
                self.current_paragraph = []
            self.in_paragraph = True
        elif tag.lower() == 'br':
            if self.current_paragraph:
                self.text_content.append(' '.join(self.current_paragraph))
                self.current_paragraph = []
    
    def handle_endtag(self, tag):
        if tag.lower() in self.skip_tags:
            self.current_tag = None
            return
            
        if tag.lower() in {'p', 'div', 'section', 'article', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            if self.current_paragraph:
                self.text_content.append(' '.join(self.current_paragraph))
                self.current_paragraph = []
            self.in_paragraph = False
    
    def handle_data(self, data):
        if self.current_tag in self.skip_tags:
            return
            
        text = data.strip()
        if text:
            self.current_paragraph.append(text)
    
    def get_text(self):
        # 남은 텍스트 처리
        if self.current_paragraph:
            self.text_content.append(' '.join(self.current_paragraph))
        
        # 문단들을 이중 줄바꿈으로 연결
        result = '\n\n'.join(self.text_content)
        
        # HTML 엔티티 디코딩
        result = result.replace('&nbsp;', ' ')
        result = result.replace('&lt;', '<')
        result = result.replace('&gt;', '>')
        result = result.replace('&amp;', '&')
        result = result.replace('&quot;', '"')
        result = result.replace('&#39;', "'")
        
        return result


class EPUBExtractor:
    def __init__(self, epub_path, max_chunk_size=3000, min_chunk_size=1000, create_chunks=True):
        self.epub_path = epub_path
        self.zip_file = None
        self.opf_path = None
        self.chapters = []
        self.metadata = {}
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.create_chunks = create_chunks
        self.chunker = TextChunker(max_chunk_size, min_chunk_size) if create_chunks else None
        
    def extract(self, output_dir=None):
        """EPUB 파일을 챕터별로 분리"""
        if output_dir is None:
            output_dir = Path(self.epub_path).stem
            
        try:
            # EPUB 파일 열기
            self.zip_file = zipfile.ZipFile(self.epub_path, 'r')
            
            # OPF 파일 경로 찾기
            self._find_opf_path()
            
            # 메타데이터 추출
            self._extract_metadata()
            
            # 목차 추출
            self._extract_toc()
            
            # 불필요한 챕터 필터링
            self._filter_chapters()
            
            # 출력 디렉토리 구조 생성
            self._create_output_structure(output_dir)
            
            # 메타데이터 저장
            self._save_metadata(output_dir)
            
            # 챕터별 파일 생성
            self._create_chapter_files(output_dir)
            
            # 청크 파일 생성 (옵션)
            if self.create_chunks:
                self._create_chunk_files(output_dir)
            
            print(f"✅ 추출 완료: {len(self.chapters)}개 챕터")
            if self.create_chunks:
                print(f"   📁 chapters/ : 원본 챕터 파일들")
                print(f"   📁 chunks/   : LLM 번역용 청크 파일들")
            print(f"   📄 info.json : 책 정보")
            
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
    
    def _extract_metadata(self):
        """OPF 파일에서 메타데이터 추출"""
        if not self.opf_path:
            raise Exception("OPF 파일을 찾을 수 없습니다.")
            
        opf_content = self.zip_file.read(self.opf_path)
        root = ET.fromstring(opf_content)
        
        # namespace 처리
        ns = {
            'opf': 'http://www.idpf.org/2007/opf',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        
        # 기본 메타데이터 추출
        self.metadata = {
            'title': '',
            'author': '',
            'language': '',
            'publisher': '',
            'date': '',
            'description': '',
            'epub_file': os.path.basename(self.epub_path)
        }
        
        # Dublin Core 메타데이터 추출
        title_elem = root.find('.//dc:title', ns)
        if title_elem is not None:
            self.metadata['title'] = title_elem.text or ''
            
        author_elem = root.find('.//dc:creator', ns)
        if author_elem is not None:
            self.metadata['author'] = author_elem.text or ''
            
        lang_elem = root.find('.//dc:language', ns)
        if lang_elem is not None:
            self.metadata['language'] = lang_elem.text or ''
            
        publisher_elem = root.find('.//dc:publisher', ns)
        if publisher_elem is not None:
            self.metadata['publisher'] = publisher_elem.text or ''
            
        date_elem = root.find('.//dc:date', ns)
        if date_elem is not None:
            self.metadata['date'] = date_elem.text or ''
            
        desc_elem = root.find('.//dc:description', ns)
        if desc_elem is not None:
            self.metadata['description'] = desc_elem.text or ''
    
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
            media_type = item.get('media-type', '')
            if href and item_id:
                manifest_items[item_id] = {
                    'href': href,
                    'media_type': media_type
                }
        
        # spine에서 읽기 순서 확인
        spine_items = []
        for itemref in root.findall('.//opf:itemref', ns):
            idref = itemref.get('idref')
            if idref in manifest_items:
                spine_items.append(manifest_items[idref]['href'])
        
        # 챕터 정보 생성
        base_dir = os.path.dirname(self.opf_path)
        for i, href in enumerate(spine_items, 1):
            file_path = os.path.join(base_dir, href) if base_dir else href
            
            # 파일명에서 챕터명 추출
            chapter_name = self._extract_chapter_name(file_path, i)
            
            self.chapters.append({
                'name': chapter_name,
                'file_path': file_path,
                'order': i,
                'original_filename': os.path.basename(file_path)
            })
    
    def _filter_chapters(self):
        """불필요한 챕터들 필터링 (titlepage, cover 등)"""
        skip_patterns = [
            r'title.*page',
            r'cover',
            r'copyright',
            r'toc',
            r'table.*of.*contents',
            r'front.*matter',
            r'dedication',
            r'epigraph'
        ]
        
        filtered_chapters = []
        for chapter in self.chapters:
            filename = chapter['original_filename'].lower()
            chapter_name = chapter['name'].lower()
            
            # 패턴 매칭으로 스킵할 챕터 확인
            should_skip = False
            for pattern in skip_patterns:
                if re.search(pattern, filename) or re.search(pattern, chapter_name):
                    should_skip = True
                    print(f"⏭️  건너뜀: {chapter['name']} (불필요한 내용)")
                    break
            
            if not should_skip:
                filtered_chapters.append(chapter)
        
        self.chapters = filtered_chapters
        
        # 순서 재정렬
        for i, chapter in enumerate(self.chapters, 1):
            chapter['order'] = i
    
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
        name = name.strip('_')
        
        return name
    
    def _create_output_structure(self, output_dir):
        """출력 디렉토리 구조 생성"""
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, 'chapters'), exist_ok=True)
        
        if self.create_chunks:
            os.makedirs(os.path.join(output_dir, 'chunks'), exist_ok=True)
    
    def _save_metadata(self, output_dir):
        """메타데이터를 info.json 파일로 저장"""
        info_data = {
            'book_info': self.metadata,
            'extraction_info': {
                'total_chapters': len(self.chapters),
                'chunking_enabled': self.create_chunks,
                'max_chunk_size': self.max_chunk_size if self.create_chunks else None,
                'min_chunk_size': self.min_chunk_size if self.create_chunks else None
            },
            'chapters': [
                {
                    'order': ch['order'],
                    'name': ch['name'],
                    'original_filename': ch['original_filename']
                } for ch in self.chapters
            ]
        }
        
        info_path = os.path.join(output_dir, 'info.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 메타데이터 저장됨: info.json")
        print(f"   📖 제목: {self.metadata['title']}")
        print(f"   ✍️  저자: {self.metadata['author']}")
    
    def _create_chapter_files(self, output_dir):
        """챕터별 파일 생성"""
        chapters_dir = os.path.join(output_dir, 'chapters')
        
        for chapter in self.chapters:
            try:
                # EPUB 내 파일 읽기
                content = self.zip_file.read(chapter['file_path']).decode('utf-8')
                
                # 개선된 HTML 파싱으로 문단 구조 보존
                text_content = self._extract_text_with_structure(content)
                
                # 파일 저장
                output_file = os.path.join(chapters_dir, f"{chapter['name']}.txt")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                # 챕터 객체에 텍스트 내용 저장 (청킹용)
                chapter['content'] = text_content
                
                print(f"📄 {chapter['name']}.txt")
                
            except Exception as e:
                print(f"⚠️  챕터 '{chapter['name']}' 처리 중 오류: {e}")
    
    def _create_chunk_files(self, output_dir):
        """LLM 번역용 청크 파일들 생성"""
        chunks_dir = os.path.join(output_dir, 'chunks')
        all_chunks = []
        
        print(f"\n🔄 LLM 번역용 청크 생성 중...")
        
        for chapter in self.chapters:
            if 'content' not in chapter:
                continue
                
            try:
                # 챕터를 청크로 분할
                chunks = self.chunker.chunk_text(chapter['content'], chapter['name'])
                
                for chunk in chunks:
                    # 청크 파일 저장
                    chunk_file = os.path.join(chunks_dir, f"{chunk['name']}.txt")
                    with open(chunk_file, 'w', encoding='utf-8') as f:
                        f.write(chunk['content'])
                    
                    # 전체 청크 리스트에 추가
                    all_chunks.append({
                        'file': f"{chunk['name']}.txt",
                        'chapter': chapter['name'],
                        'size': chunk['size']
                    })
                
                print(f"   📦 {chapter['name']}: {len(chunks)}개 청크")
                
            except Exception as e:
                print(f"⚠️  챕터 '{chapter['name']}' 청킹 중 오류: {e}")
        
        # 청크 인덱스 파일 생성
        chunk_index = {
            'total_chunks': len(all_chunks),
            'chunk_settings': {
                'max_size': self.max_chunk_size,
                'min_size': self.min_chunk_size
            },
            'chunks': all_chunks
        }
        
        index_path = os.path.join(chunks_dir, 'chunk_index.json')
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(chunk_index, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 총 {len(all_chunks)}개 청크 생성 완료")
        print(f"📋 청크 인덱스: chunks/chunk_index.json")
    
    def _extract_text_with_structure(self, html_content):
        """문단 구조를 보존하며 HTML에서 텍스트 추출"""
        parser = ImprovedHTMLParser()
        parser.feed(html_content)
        text = parser.get_text()
        
        # 추가 정리
        text = re.sub(r'\n{3,}', '\n\n', text)  # 과도한 줄바꿈 제거
        text = re.sub(r'[ \t]+', ' ', text)     # 과도한 공백 제거
        
        return text.strip()


def main():
    parser = argparse.ArgumentParser(description='EPUB 파일을 챕터별로 분리하고 LLM 번역용 청크로 나누는 도구')
    parser.add_argument('epub_file', help='추출할 EPUB 파일 경로')
    parser.add_argument('--max-chunk-size', type=int, default=3000, 
                       help='최대 청크 크기 (문자 수, 기본값: 3000)')
    parser.add_argument('--min-chunk-size', type=int, default=1000,
                       help='최소 청크 크기 (문자 수, 기본값: 1000)')
    parser.add_argument('--no-chunks', action='store_true',
                       help='청크 파일 생성하지 않음 (챕터 파일만 생성)')
    parser.add_argument('--output-dir', '-o', help='출력 디렉토리 (기본값: EPUB 파일명)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.epub_file):
        print(f"❌ 파일을 찾을 수 없습니다: {args.epub_file}")
        sys.exit(1)
    
    if not args.epub_file.lower().endswith('.epub'):
        print("❌ EPUB 파일이 아닙니다.")
        sys.exit(1)
    
    # 청크 크기 검증
    if args.max_chunk_size < args.min_chunk_size:
        print("❌ 최대 청크 크기가 최소 청크 크기보다 작습니다.")
        sys.exit(1)
    
    create_chunks = not args.no_chunks
    
    print(f"📚 EPUB 추출기 시작")
    print(f"   파일: {args.epub_file}")
    if create_chunks:
        print(f"   청크 크기: {args.min_chunk_size}-{args.max_chunk_size} 문자")
    else:
        print(f"   모드: 챕터 파일만 생성")
    print()
    
    extractor = EPUBExtractor(
        args.epub_file, 
        max_chunk_size=args.max_chunk_size,
        min_chunk_size=args.min_chunk_size,
        create_chunks=create_chunks
    )
    extractor.extract(args.output_dir)


if __name__ == "__main__":
    main()