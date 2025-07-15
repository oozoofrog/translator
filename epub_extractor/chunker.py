#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TextChunker 모듈

LLM 번역에 적합한 크기로 텍스트를 지능적으로 분할하는 기능을 제공합니다.
"""

import re


class TextChunker:
    """LLM 번역에 적합한 크기로 텍스트를 지능적으로 분할하는 클래스"""

    def __init__(self, max_chunk_size=3500, min_chunk_size=1500):
        """
        청킹 객체 초기화

        Args:
            max_chunk_size (int): 최대 청크 크기 (문자 수, 기본값 3500으로 최적화)
            min_chunk_size (int): 최소 청크 크기 (문자 수, 기본값 1500으로 최적화)
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk_text(self, text, chapter_name=""):
        """
        텍스트를 적절한 크기의 청크로 분할

        Args:
            text (str): 분할할 텍스트
            chapter_name (str): 챕터명 (청크 파일명에 사용)

        Returns:
            List[Dict]: 청크 정보 리스트
                - content: 청크 내용
                - name: 청크 파일명
                - size: 청크 크기 (문자 수)
        """
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
                    chunks.append(
                        {
                            "content": current_chunk.strip(),
                            "name": f"{chapter_name}_part_{chunk_number:02d}",
                            "size": len(current_chunk),
                        }
                    )
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
                chunks.append(
                    {
                        "content": current_chunk.strip(),
                        "name": f"{chapter_name}_part_{chunk_number:02d}",
                        "size": len(current_chunk),
                    }
                )
            else:
                # 마지막 청크가 너무 작으면 이전 청크와 병합
                if chunks:
                    chunks[-1]["content"] += "\n\n" + current_chunk.strip()
                    chunks[-1]["size"] = len(chunks[-1]["content"])

        return chunks

    def _split_paragraphs(self, text):
        """
        텍스트를 문단별로 분할

        Args:
            text (str): 분할할 텍스트

        Returns:
            List[str]: 문단 리스트
        """
        # 연속된 줄바꿈을 문단 구분자로 사용
        paragraphs = re.split(r"\n\s*\n", text.strip())
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_by_sentences(self, text, chapter_name, start_chunk_num):
        """
        긴 문단을 문장별로 분할

        Args:
            text (str): 분할할 텍스트
            chapter_name (str): 챕터명
            start_chunk_num (int): 시작 청크 번호

        Returns:
            List[Dict]: 청크 정보 리스트
        """
        chunks = []
        # 문장 구분자: . ! ? 뒤에 공백이나 줄바꿈
        sentences = re.split(r"([.!?])\s+", text)

        current_chunk = ""
        chunk_number = start_chunk_num

        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")

            if len(current_chunk + " " + sentence) <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                if current_chunk:
                    chunks.append(
                        {
                            "content": current_chunk.strip(),
                            "name": f"{chapter_name}_part_{chunk_number:02d}",
                            "size": len(current_chunk),
                        }
                    )
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
            chunks.append(
                {
                    "content": current_chunk.strip(),
                    "name": f"{chapter_name}_part_{chunk_number:02d}",
                    "size": len(current_chunk),
                }
            )

        return chunks

    def _split_by_words(self, text, chapter_name, start_chunk_num):
        """
        긴 문장을 단어별로 분할 (최후 수단)

        Args:
            text (str): 분할할 텍스트
            chapter_name (str): 챕터명
            start_chunk_num (int): 시작 청크 번호

        Returns:
            List[Dict]: 청크 정보 리스트
        """
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
                    chunks.append(
                        {
                            "content": current_chunk.strip(),
                            "name": f"{chapter_name}_part_{chunk_number:02d}",
                            "size": len(current_chunk),
                        }
                    )
                    chunk_number += 1
                current_chunk = word

        if current_chunk.strip():
            chunks.append(
                {
                    "content": current_chunk.strip(),
                    "name": f"{chapter_name}_part_{chunk_number:02d}",
                    "size": len(current_chunk),
                }
            )

        return chunks
