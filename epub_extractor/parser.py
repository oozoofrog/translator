#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 파서 모듈

문단 구조를 보존하면서 EPUB HTML 콘텐츠를 텍스트로 변환하는 기능을 제공합니다.
"""

import html.parser


class ImprovedHTMLParser(html.parser.HTMLParser):
    """문단 구조를 보존하는 HTML 파서"""
    
    def __init__(self):
        """HTML 파서 초기화"""
        super().__init__()
        self.text_content = []
        self.current_paragraph = []
        self.in_paragraph = False
        self.skip_tags = {'script', 'style', 'head', 'title'}
        self.current_tag = None
    
    def handle_starttag(self, tag, attrs):
        """
        HTML 시작 태그 처리
        
        Args:
            tag (str): 태그명
            attrs (List[Tuple]): 태그 속성들
        """
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
        """
        HTML 종료 태그 처리
        
        Args:
            tag (str): 태그명
        """
        if tag.lower() in self.skip_tags:
            self.current_tag = None
            return
            
        if tag.lower() in {'p', 'div', 'section', 'article', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            if self.current_paragraph:
                self.text_content.append(' '.join(self.current_paragraph))
                self.current_paragraph = []
            self.in_paragraph = False
    
    def handle_data(self, data):
        """
        HTML 텍스트 데이터 처리
        
        Args:
            data (str): 텍스트 데이터
        """
        if self.current_tag in self.skip_tags:
            return
            
        text = data.strip()
        if text:
            self.current_paragraph.append(text)
    
    def get_text(self):
        """
        파싱된 텍스트 반환
        
        Returns:
            str: 문단 구조가 보존된 텍스트
        """
        # 남은 텍스트 처리
        if self.current_paragraph:
            self.text_content.append(' '.join(self.current_paragraph))
        
        # 문단들을 이중 줄바꿈으로 연결
        result = '\n\n'.join(self.text_content)
        
        # HTML 엔티티 디코딩
        result = self._decode_html_entities(result)
        
        return result
    
    def _decode_html_entities(self, text):
        """
        HTML 엔티티를 일반 문자로 변환
        
        Args:
            text (str): HTML 엔티티가 포함된 텍스트
            
        Returns:
            str: 엔티티가 디코딩된 텍스트
        """
        # 일반적인 HTML 엔티티들 변환
        replacements = {
            '&nbsp;': ' ',
            '&lt;': '<',
            '&gt;': '>',
            '&amp;': '&',
            '&quot;': '"',
            '&#39;': "'",
            '&apos;': "'",
            '&hellip;': '…',
            '&mdash;': '—',
            '&ndash;': '–',
            '&ldquo;': '"',
            '&rdquo;': '"',
            '&lsquo;': ''',
            '&rsquo;': '''
        }
        
        for entity, char in replacements.items():
            text = text.replace(entity, char)
        
        return text


def extract_text_from_html(html_content):
    """
    HTML 콘텐츠에서 문단 구조를 보존하며 텍스트 추출
    
    Args:
        html_content (str): HTML 콘텐츠
        
    Returns:
        str: 추출된 텍스트
    """
    import re
    
    parser = ImprovedHTMLParser()
    parser.feed(html_content)
    text = parser.get_text()
    
    # 추가 정리
    text = re.sub(r'\n{3,}', '\n\n', text)  # 과도한 줄바꿈 제거
    text = re.sub(r'[ \t]+', ' ', text)     # 과도한 공백 제거
    
    return text.strip()