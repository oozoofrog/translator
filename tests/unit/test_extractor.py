import os
import shutil
import tempfile
import zipfile
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import pytest
from epub_extractor.extractor import EPUBExtractor

@pytest.fixture
def minimal_epub_file():
    tmp_dir = tempfile.mkdtemp()
    epub_path = os.path.join(tmp_dir, "test.epub")
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", """<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>""")
        zf.writestr("OEBPS/content.opf", """<?xml version="1.0"?><package xmlns="http://www.idpf.org/2007/opf"><metadata><dc:title>Test</dc:title></metadata><manifest><item id="chap1" href="chap1.html" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="chap1"/></spine></package>""")
        zf.writestr("OEBPS/chap1.html", "<html><body><p>Test content</p></body></html>")
    yield epub_path
    shutil.rmtree(tmp_dir)

def test_extract_to_folder_structure(minimal_epub_file):
    output_dir = tempfile.mkdtemp()
    extractor = EPUBExtractor(minimal_epub_file)
    extractor.extract(output_dir)
    
    assert os.path.exists(os.path.join(output_dir, "mimetype"))
    assert os.path.exists(os.path.join(output_dir, "META-INF/container.xml"))
    assert os.path.exists(os.path.join(output_dir, "OEBPS/content.opf"))
    assert os.path.exists(os.path.join(output_dir, "OEBPS/chap1.html"))
    
    shutil.rmtree(output_dir) 