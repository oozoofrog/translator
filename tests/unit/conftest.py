import os
import shutil
import tempfile
import zipfile

import pytest


@pytest.fixture
def temp_dir():
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)


@pytest.fixture
def sample_epub(temp_dir):
    epub_path = os.path.join(temp_dir, "sample.epub")
    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr(
            "META-INF/container.xml",
            '<container><rootfiles><rootfile full-path="content.opf"/></rootfiles></container>',
        )
        zf.writestr(
            "content.opf",
            '<package><metadata><dc:title>Sample</dc:title></metadata><manifest><item id="test" href="test.html"/></manifest><spine><itemref idref="test"/></spine></package>',
        )
        zf.writestr("test.html", "<html><body>Test</body></html>")
    yield epub_path
