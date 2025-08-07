#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
번역 모듈

Hugging Face Transformers를 사용한 텍스트 번역 기능을 제공합니다.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    import torch
except ImportError:
    raise ImportError("Hugging Face 패키지가 설치되지 않았습니다. 'pip install transformers torch accelerate'로 설치해주세요.")

from .prompts import get_translation_prompt, get_system_prompt


class HuggingFaceTranslator:
    """Hugging Face Transformers를 사용한 번역기"""
    
    def __init__(self, model_name="openai/gpt-oss-20b", temperature=0.1, max_retries=3, genre="fantasy", device=None):
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.genre = genre
        self.translation_prompt = get_translation_prompt(genre)
        
        # 디바이스 설정 (MPS, CUDA, CPU 순서로 우선순위)
        if device is None or device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        else:
            self.device = device
            
        # 모델과 토크나이저 초기화
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        
        print(f"🤖 Hugging Face 번역기 초기화 중...")
        print(f"   모델: {model_name}")
        print(f"   디바이스: {self.device}")
        
        self._load_model()
    
    def _load_model(self):
        """모델과 토크나이저 로드"""
        try:
            print(f"📥 모델 다운로드 중: {self.model_name}")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # 모델 로드 (MPS, CUDA, CPU 지원)
            if self.device == "cuda":
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    low_cpu_mem_usage=True
                )
            elif self.device == "mps":
                # MPS에서 MXFP4 양자화 모델 지원을 위한 설정
                try:
                    # 먼저 기본 설정으로 시도
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float16,
                        low_cpu_mem_usage=True,
                        trust_remote_code=True,    # 원격 코드 신뢰
                        attn_implementation="eager",  # 어텐션 구현 방식
                        load_in_8bit=False,       # 8bit 양자화 비활성화
                        load_in_4bit=False        # 4bit 양자화 비활성화
                    )
                    self.model = self.model.to("mps")
                except Exception as mps_error:
                    print(f"⚠️  MPS에서 모델 로드 실패: {mps_error}")
                    print("🔄 CPU로 대체하여 로드 중...")
                    # MPS 실패 시 CPU로 대체
                    self.device = "cpu"
                    try:
                        self.model = AutoModelForCausalLM.from_pretrained(
                            self.model_name,
                            torch_dtype=torch.float32,
                            low_cpu_mem_usage=True,
                            trust_remote_code=True,
                            load_in_8bit=False,
                            load_in_4bit=False
                        )
                    except Exception as cpu_error:
                        print(f"❌ CPU에서도 모델 로드 실패: {cpu_error}")
                        print("💡 이 모델은 특별한 GPU 요구사항이 있습니다.")
                        print("   다른 모델을 사용하거나 GPU 환경에서 실행해주세요.")
                        raise
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True
                )
            
            # 패딩 토큰 설정
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # 파이프라인 생성
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device,
                torch_dtype=torch.float16 if self.device in ["cuda", "mps"] else torch.float32
            )
            
            print(f"✅ 모델 로드 완료!")
            
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            raise
    
    def check_model_available(self):
        """모델이 사용 가능한지 확인"""
        try:
            return self.model is not None and self.tokenizer is not None
        except Exception:
            return False
    
    def translate_text(self, text: str) -> str:
        """단일 텍스트 번역"""
        if not self.check_model_available():
            raise RuntimeError("모델이 로드되지 않았습니다.")
        
        # 번역 프롬프트 생성
        system_prompt = get_system_prompt()
        translation_prompt = self.translation_prompt
        
        # 모델의 최대 시퀀스 길이 확인
        max_model_length = self.tokenizer.model_max_length if hasattr(self.tokenizer, 'model_max_length') else 1024
        
        # 입력 텍스트가 너무 길면 자르기 (더 관대한 길이 설정)
        max_text_length = max_model_length - 512  # 512는 프롬프트와 생성 토큰을 위한 여유 공간
        encoded_text = self.tokenizer.encode(text)
        
        if len(encoded_text) > max_text_length:
            # 텍스트를 자르기 (문장 단위로 자르기 시도)
            truncated_text = self.tokenizer.decode(encoded_text[:max_text_length], skip_special_tokens=True)
            # 마지막 완전한 문장으로 자르기
            sentences = truncated_text.split('.')
            if len(sentences) > 1:
                truncated_text = '.'.join(sentences[:-1]) + '.'
            text = truncated_text
            print(f"⚠️  텍스트가 너무 길어서 자릅니다. (최대 길이: {max_text_length} 토큰)")
        
        full_prompt = f"{system_prompt}\n\n{translation_prompt}\n\n영어 텍스트:\n{text}\n\n한국어 번역:\n"
        
        for attempt in range(self.max_retries):
            try:
                # 텍스트 생성 (모델의 최대 길이 고려)
                outputs = self.pipeline(
                    full_prompt,
                    max_new_tokens=512,  # 새로 생성할 토큰 수 증가
                    temperature=self.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    num_return_sequences=1,
                    truncation=True,  # 자동 자르기 활성화
                    max_length=max_model_length  # 모델의 최대 길이 사용
                )
                
                # 결과 추출
                generated_text = outputs[0]['generated_text']
                
                # 번역 부분만 추출 (프롬프트 제거)
                if "한국어 번역:" in generated_text:
                    translation = generated_text.split("한국어 번역:")[-1].strip()
                else:
                    # 프롬프트가 없는 경우 전체 텍스트 사용
                    translation = generated_text[len(full_prompt):].strip()
                
                # 빈 번역 체크
                if not translation or translation.isspace():
                    raise ValueError("빈 번역 결과")
                
                return translation
                
            except Exception as e:
                print(f"⚠️  번역 시도 {attempt + 1}/{self.max_retries} 실패: {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # 지수 백오프
        
        return None
    
    def translate_chunks(self, work_dir: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
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
            'device': self.device,
            'total_chunks': chunk_index['total_chunks'],
            'completed_chunks': 0,
            'failed_chunks': 0,
            'start_time': time.time()
        }
        
        print(f"🔄 번역 시작: {chunk_index['total_chunks']}개 청크")
        print(f"   모델: {self.model_name}")
        print(f"   장르: {self.genre}")
        print(f"   디바이스: {self.device}")
        
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


# 하위 호환성을 위한 별칭
OllamaTranslator = HuggingFaceTranslator