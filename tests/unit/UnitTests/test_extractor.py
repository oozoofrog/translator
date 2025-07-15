import sys
import os
import tempfile
import zipfile
import json
import shutil
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from epub_extractor.extractor import EPUBExtractor

# 최소한의 EPUB 구조를 가진 임시 파일 생성
@pytest.fixture
def minimal_epub_file():
    tmp_dir = tempfile.mkdtemp()
    epub_path = os.path.join(tmp_dir, 'test.epub')
    with zipfile.ZipFile(epub_path, 'w') as zf:
        # mimetype 파일 (필수)
        zf.writestr('mimetype', 'application/epub+zip')
        # META-INF/container.xml (필수)
        zf.writestr('META-INF/container.xml', '''<?xml version="1.0"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n  <rootfiles>\n    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n  </rootfiles>\n</container>''')
        # OEBPS/content.opf (메타데이터 및 매니페스트)
        zf.writestr('OEBPS/content.opf', '''<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">\n  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n    <dc:title>테스트 책</dc:title>\n    <dc:creator>저자</dc:creator>\n    <dc:language>ko</dc:language>\n    <dc:identifier id="BookId">test-id</dc:identifier>\n  </metadata>\n  <manifest>\n    <item id="chap1" href="chapter1.html" media-type="application/xhtml+xml"/>\n  </manifest>\n  <spine>\n    <itemref idref="chap1"/>\n  </spine>\n</package>''')
        # OEBPS/chapter1.html (본문)
        zf.writestr('OEBPS/chapter1.html', '<html><body><h1>챕터1</h1><p>본문입니다.</p></body></html>')
    yield epub_path
    shutil.rmtree(tmp_dir)

def test_epub_extractor_basic(minimal_epub_file):
    # 임시 출력 디렉토리
    with tempfile.TemporaryDirectory() as out_dir:
        extractor = EPUBExtractor(minimal_epub_file, max_chunk_size=100, min_chunk_size=10, create_chunks=True)
        extractor.extract(output_dir=out_dir)
        # info.json, chapters/, chunks/ 폴더가 생성되어야 함
        assert os.path.exists(os.path.join(out_dir, 'info.json'))
        assert os.path.isdir(os.path.join(out_dir, 'chapters'))
        assert os.path.isdir(os.path.join(out_dir, 'chunks'))
        # info.json의 메타데이터 확인
        with open(os.path.join(out_dir, 'info.json'), encoding='utf-8') as f:
            info = json.load(f)
        assert info['book_info']['title'] == '테스트 책'
        assert info['book_info']['author'] == '저자'
        # 챕터 파일 존재 확인 (info.json의 name 필드 기준)
        chapter_name = info['chapters'][0]['name']
        chapter_file = os.path.join(out_dir, 'chapters', f'{chapter_name}.txt')
        assert os.path.exists(chapter_file)
        # 청크 파일 존재 확인
        chunk_files = os.listdir(os.path.join(out_dir, 'chunks'))
        assert any(fn.endswith('.txt') for fn in chunk_files) 