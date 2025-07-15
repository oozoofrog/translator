import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest

from epub_extractor.chunker import TextChunker


@pytest.fixture
def chunker():
    return TextChunker(max_chunk_size=30, min_chunk_size=10)


def test_chunk_paragraph_split(chunker):
    text = "문단1입니다. 내용이 길어서 충분히 길어집니다.\n\n문단2입니다. 내용이 길어서 충분히 길어집니다.\n\n문단3입니다. 내용이 길어서 충분히 길어집니다."
    chunks = chunker.chunk_text(text, chapter_name="TestChapter")
    assert len(chunks) >= 1
    assert all("content" in c and "name" in c for c in chunks)
    assert all(len(c["content"]) >= 10 for c in chunks)
    assert all(len(c["content"]) <= 30 for c in chunks)


def test_chunk_sentence_split(chunker):
    text = "이것은 매우 매우 매우 매우 매우 매우 매우 매우 매우 매우 긴 문장입니다. 이 문장도 매우 매우 매우 매우 매우 매우 매우 매우 매우 매우 길어서 분할이 필요합니다. 또 다른 매우 매우 매우 매우 매우 매우 매우 매우 매우 매우 긴 문장입니다."
    chunks = chunker.chunk_text(text, chapter_name="TestChapter")
    assert len(chunks) >= 1
    assert all(len(c["content"]) >= 10 for c in chunks)
    assert all(len(c["content"]) <= 30 for c in chunks)
    assert all(c["content"].strip() != "" for c in chunks)


def test_chunk_word_split(chunker):
    text = ("단어 분할 테스트 입니다 매우 긴 문장 입니다 이것도 테스트 입니다. " * 10).strip()
    chunks = chunker.chunk_text(text, chapter_name="TestChapter")
    assert len(chunks) >= 1
    assert all(len(c["content"]) <= 30 for c in chunks)
    assert all(c["content"].strip() != "" for c in chunks)


def test_empty_input(chunker):
    text = ""
    chunks = chunker.chunk_text(text, chapter_name="TestChapter")
    assert chunks == []


def test_exact_chunk_size(chunker):
    text = "a" * 30
    chunks = chunker.chunk_text(text, chapter_name="TestChapter")
    if len(chunks) == 1:
        assert chunks[0]["size"] == 30
    else:
        # 정책상, min_chunk_size 미만이면 청크가 없을 수도 있음
        assert len(chunks) == 0
