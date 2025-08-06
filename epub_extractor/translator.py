#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
번역 모듈

Ollama를 사용한 텍스트 번역 기능을 제공합니다.
"""

import json
import os
import time
from pathlib import Path

try:
    import ollama
except ImportError:
    ollama = None

from .prompts import get_translation_prompt, get_system_prompt


class OllamaTranslator:
    """Ollama를 사용한 번역기"""
    
    def __init__(self, model_name="gpt-oss:20b", temperature=0.1, max_retries=3, genre="fantasy"):
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.genre = genre
        self.translation_prompt = get_translation_prompt(genre)
        
        if ollama is None:
            raise ImportError("ollama 패키지가 설치되지 않았습니다. 'pip install ollama'로 설치해주세요.")
    
    def translate_text(self, text):
        """단일 텍스트 번역"""
        prompt = self.translation_prompt + text
        
        for attempt in range(self.max_retries):
            try:
                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": get_system_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    options={
                        "temperature": self.temperature
                    }
                )
                
                return response['message']['content'].strip()
                
            except Exception as e:
                print(f"⚠️  번역 시도 {attempt + 1}/{self.max_retries} 실패: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 지수 백오프
        
        return None
    
    def translate_chunks(self, work_dir, output_dir=None):
        """청크 파일들을 번역"""
        if output_dir is None:
            output_dir = work_dir
            
        chunks_dir = os.path.join(work_dir, 'chunks')
        translated_dir = os.path.join(output_dir, 'translated_chunks')
        
        os.makedirs(translated_dir, exist_ok=True)
        
        # 청크 인덱스 읽기
        chunk_index_path = os.path.join(chunks_dir, 'chunk_index.json')
        if not os.path.exists(chunk_index_path):
            raise FileNotFoundError(f"청크 인덱스 파일을 찾을 수 없습니다: {chunk_index_path}")
        
        with open(chunk_index_path, 'r', encoding='utf-8') as f:
            chunk_index = json.load(f)
        
        # 번역 진행 상황 추적
        translation_info = {
            'model': self.model_name,
            'genre': self.genre,
            'temperature': self.temperature,
            'total_chunks': chunk_index['total_chunks'],
            'completed_chunks': 0,
            'failed_chunks': 0,
            'start_time': time.time()
        }
        
        print(f"🔄 번역 시작: {chunk_index['total_chunks']}개 청크")
        print(f"   모델: {self.model_name}")
        print(f"   장르: {self.genre}")
        
        # 각 청크 번역
        for i, chunk_info in enumerate(chunk_index['chunks'], 1):
            chunk_file = chunk_info['file']
            chunk_path = os.path.join(chunks_dir, chunk_file)
            
            # 번역된 파일명 생성
            translated_file = f"ko_{chunk_file}"
            translated_path = os.path.join(translated_dir, translated_file)
            
            # 이미 번역된 파일이 있으면 건너뛰기
            if os.path.exists(translated_path):
                print(f"⏭️  건너뜀: {chunk_file} (이미 번역됨)")
                translation_info['completed_chunks'] += 1
                continue
            
            try:
                # 원본 청크 읽기
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    chunk_text = f.read()
                
                print(f"🌐 번역 중: {chunk_file} ({i}/{chunk_index['total_chunks']})")
                
                # 번역 수행
                translated_text = self.translate_text(chunk_text)
                
                # 번역 결과 저장
                with open(translated_path, 'w', encoding='utf-8') as f:
                    f.write(translated_text)
                
                translation_info['completed_chunks'] += 1
                print(f"✅ 완료: {translated_file}")
                
            except Exception as e:
                print(f"❌ 실패: {chunk_file} - {e}")
                translation_info['failed_chunks'] += 1
        
        # 번역 정보 저장
        translation_info['end_time'] = time.time()
        translation_info['duration'] = translation_info['end_time'] - translation_info['start_time']
        
        translation_index_path = os.path.join(output_dir, 'translation_index.json')
        with open(translation_index_path, 'w', encoding='utf-8') as f:
            json.dump({'translation_info': translation_info}, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 번역 완료 통계:")
        print(f"   완료: {translation_info['completed_chunks']}개")
        print(f"   실패: {translation_info['failed_chunks']}개")
        print(f"   소요시간: {translation_info['duration']:.1f}초")
        
        return translation_info