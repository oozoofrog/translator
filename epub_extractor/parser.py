#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 파싱 모듈

EPUB의 HTML/XHTML 컨텐츠를 텍스트로 변환하며 문단 구조를 보존합니다.
"""

import html.parser


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