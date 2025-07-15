import json
import os
import shutil
import sys
import tempfile
import zipfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from epub_extractor.builder import EPUBBuilder


def create_minimal_epub(epub_path):
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0"?>\n<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n  <rootfiles>\n    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n  </rootfiles>\n</container>""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">\n  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n    <dc:title>테스트 책</dc:title>\n    <dc:creator>저자</dc:creator>\n    <dc:language>en</dc:language>\n    <dc:identifier id="BookId">test-id</dc:identifier>\n  </metadata>\n  <manifest>\n    <item id="chap1" href="chapter1.html" media-type="application/xhtml+xml"/>\n  </manifest>\n  <spine>\n    <itemref idref="chap1"/>\n  </spine>\n</package>""",
        )
        zf.writestr("OEBPS/chapter1.html", "<html><body><h1>Chapter 1</h1><p>Original text.</p></body></html>")


@pytest.fixture
def builder_test_env():
    tmp_dir = tempfile.mkdtemp()
    # 원본 EPUB
    epub_path = os.path.join(tmp_dir, "test.epub")
    create_minimal_epub(epub_path)
    # 번역 디렉토리
    translated_dir = os.path.join(tmp_dir, "translated_chunks")
    os.makedirs(translated_dir)
    # info.json
    info = {
        "book_info": {"title": "테스트 책", "author": "저자", "language": "en", "epub_file": "test.epub"},
        "extraction_info": {},
        "chapters": [{"order": 1, "name": "Chapter_001", "original_filename": "chapter1.html"}],
    }
    with open(os.path.join(tmp_dir, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False)
    # translation_index.json
    translation_index = {"translation_info": {}, "original_info": {}}
    with open(os.path.join(translated_dir, "translation_index.json"), "w", encoding="utf-8") as f:
        json.dump(translation_index, f, ensure_ascii=False)
    # 번역된 청크 파일
    with open(os.path.join(translated_dir, "Chapter_001.txt"), "w", encoding="utf-8") as f:
        f.write("번역된 텍스트입니다.")
    # chunks/chunk_index.json (최소 구조)
    chunks_dir = os.path.join(tmp_dir, "chunks")
    os.makedirs(chunks_dir)
    chunk_index = {
        "total_chunks": 1,
        "chunk_settings": {"max_size": 100, "min_size": 10},
        "statistics": {"avg_chunk_size": 10, "total_characters": 10},
        "chunks": [
            {"chapter": "Chapter_001", "name": "Chapter_001.txt", "order": 1, "size": 10, "file": "Chapter_001.txt"}
        ],
    }
    with open(os.path.join(chunks_dir, "chunk_index.json"), "w", encoding="utf-8") as f:
        json.dump(chunk_index, f, ensure_ascii=False)
    yield epub_path, translated_dir, tmp_dir
    shutil.rmtree(tmp_dir)


def test_epub_builder_basic(builder_test_env):
    epub_path, translated_dir, tmp_dir = builder_test_env
    builder = EPUBBuilder(epub_path, translated_dir)
    output_path = os.path.join(tmp_dir, "output.epub")
    result = builder.build_korean_epub(output_path=output_path)
    assert os.path.exists(result)
    # 생성된 EPUB 파일에서 OPF 파일을 추출해 [한글판]이 제목에 포함됐는지 확인
    with zipfile.ZipFile(result, "r") as zf:
        opf_files = [f for f in zf.namelist() if f.endswith(".opf")]
        assert opf_files
        opf_content = zf.read(opf_files[0]).decode("utf-8")
        assert "[한글판]" in opf_content
        assert "<dc:language>ko</dc:language>" in opf_content
