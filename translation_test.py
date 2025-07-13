#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
번역 테스트 스크립트

다양한 텍스트 크기와 temperature 값으로 phi4:latest 모델의 번역 품질을 테스트합니다.
"""

import os
import time
from datetime import datetime
from epub_extractor.translator import OllamaTranslator

def test_translation():
    """번역 테스트 실행"""
    
    # 테스트 설정
    model_name = "exaone3.5:7.8b"
    genre = "fantasy"
    # temperature 0.1로 고정
    temperatures = [0.1]
    
    # 테스트 파일들 (크기별)
    test_files = {
        "small": "sample_small.txt",
        "medium": "sample_medium.txt", 
        "full": "sample_full.txt"
    }
    
    # 결과 저장할 디렉토리 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"translation_test_results_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    # 테스트 로그 파일
    log_file = os.path.join(results_dir, "test_log.txt")
    
    with open(log_file, 'w', encoding='utf-8') as log:
        log.write(f"번역 테스트 시작: {datetime.now()}\n")
        log.write(f"모델: {model_name}\n")
        log.write(f"장르: {genre}\n")
        log.write(f"Temperature 범위: {temperatures}\n")
        log.write("=" * 80 + "\n\n")
        
        print(f"📊 번역 테스트 시작")
        print(f"🤖 모델: {model_name}")
        print(f"📁 결과 저장: {results_dir}/")
        print("=" * 50)
        
        # 각 크기별로 테스트
        for size_name, filename in test_files.items():
            if not os.path.exists(filename):
                print(f"❌ 파일을 찾을 수 없습니다: {filename}")
                continue
                
            # 원본 텍스트 읽기
            with open(filename, 'r', encoding='utf-8') as f:
                text = f.read()
            
            text_length = len(text)
            word_count = len(text.split())
            
            print(f"\n📝 테스트 중: {size_name.upper()} ({text_length}자, {word_count}단어)")
            log.write(f"=== {size_name.upper()} 테스트 ({text_length}자, {word_count}단어) ===\n")
            log.write(f"원본 파일: {filename}\n\n")
            
            # 각 temperature별로 테스트
            for temp in temperatures:
                print(f"  🌡️  Temperature: {temp}")
                log.write(f"--- Temperature: {temp} ---\n")
                
                try:
                    # 번역기 초기화
                    translator = OllamaTranslator(
                        model_name=model_name,
                        temperature=temp,
                        genre=genre,
                        enable_cache=False  # 캐시 비활성화로 매번 새로 번역
                    )
                    
                    # 번역 수행
                    start_time = time.time()
                    result = translator.translate_text(text)
                    end_time = time.time()
                    
                    translation_time = end_time - start_time
                    
                    # 결과 파일명 생성
                    result_filename = f"{size_name}_temp{temp}_result.txt"
                    result_path = os.path.join(results_dir, result_filename)
                    
                    # 결과 저장
                    with open(result_path, 'w', encoding='utf-8') as f:
                        f.write(f"=== 번역 테스트 결과 ===\n")
                        f.write(f"모델: {model_name}\n")
                        f.write(f"Temperature: {temp}\n")
                        f.write(f"텍스트 크기: {size_name} ({text_length}자, {word_count}단어)\n")
                        f.write(f"번역 시간: {translation_time:.2f}초\n")
                        f.write(f"테스트 시간: {datetime.now()}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write("원본:\n")
                        f.write(text)
                        f.write("\n\n" + "=" * 50 + "\n\n")
                        f.write("번역 결과:\n")
                        f.write(result)
                    
                    # 로그에 요약 기록
                    log.write(f"번역 시간: {translation_time:.2f}초\n")
                    log.write(f"결과 파일: {result_filename}\n")
                    log.write(f"번역 길이: {len(result)}자\n")
                    
                    # 간단한 품질 체크
                    has_korean = any('\uac00' <= char <= '\ud7af' for char in result)
                    has_english = any('a' <= char.lower() <= 'z' for char in result)
                    has_special_chars = any(char in '<>[]{}' for char in result)
                    
                    log.write(f"한국어 포함: {'예' if has_korean else '아니오'}\n")
                    log.write(f"영어 포함: {'예' if has_english else '아니오'}\n") 
                    log.write(f"특수문자 포함: {'예' if has_special_chars else '아니오'}\n")
                    log.write("\n")
                    
                    print(f"    ✅ 완료 ({translation_time:.1f}초) -> {result_filename}")
                    
                except Exception as e:
                    error_msg = f"오류 발생: {str(e)}"
                    print(f"    ❌ {error_msg}")
                    log.write(f"오류: {error_msg}\n\n")
            
            log.write("\n")
    
    print(f"\n🎉 모든 테스트 완료!")
    print(f"📁 결과 확인: {results_dir}/")
    print(f"📋 로그 파일: {log_file}")

if __name__ == "__main__":
    test_translation()