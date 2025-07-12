#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ollama
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm

from .prompts import get_translation_prompt

class OllamaTranslator:
    """Ollama Python 라이브러리를 사용한 영어→한국어 번역기"""
    
    def __init__(self, 
                 model_name="llama3.1:8b",
                 temperature=0.1,
                 max_retries=3,
                 genre="fantasy"):
        """
        Args:
            model_name: 사용할 Ollama 모델명
            temperature: 번역 일관성을 위한 낮은 온도값 (0.0-2.0)
            max_retries: 번역 실패시 재시도 횟수
            genre: 소설 장르 (fantasy, sci-fi, romance, mystery, general)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.genre = genre
        
        # Ollama 클라이언트 초기화
        self.client = ollama.Client()
        
        # 장르별 번역 프롬프트 설정
        self.translation_prompt = get_translation_prompt(genre)
    
    def check_ollama_available(self) -> bool:
        """Ollama 서비스 사용 가능 여부 확인"""
        try:
            # 간단한 API 호출로 Ollama 서비스 확인
            self.client.list()
            return True
        except Exception:
            return False
    
    def check_model_available(self) -> bool:
        """지정된 모델 사용 가능 여부 확인"""
        try:
            models = self.client.list()
            model_names = []
            for model in models.get('models', []):
                # API 응답 구조에 따라 다른 필드명 시도
                if hasattr(model, 'model'):
                    model_names.append(model.model)
                elif 'model' in model:
                    model_names.append(model['model'])
                elif 'name' in model:
                    model_names.append(model['name'])
            return self.model_name in model_names
        except Exception as e:
            print(f"모델 확인 오류: {e}")
            return False
    
    def ensure_model_loaded(self) -> bool:
        """모델이 로드되어 있는지 확인하고 필요시 로드"""
        try:
            # 짧은 테스트 프롬프트로 모델 로드 확인
            test_response = self.client.generate(
                model=self.model_name,
                prompt="Hello",
                options={'num_predict': 1}  # 1토큰만 생성
            )
            return True
        except Exception as e:
            print(f"모델 로드 확인 실패: {e}")
            return False
    
    def translate_text(self, text: str) -> Optional[str]:
        """단일 텍스트 블록 번역"""
        if not text.strip():
            return ""
        
        # 프롬프트 생성
        prompt = self.translation_prompt.format(text=text.strip())
        
        for attempt in range(self.max_retries):
            try:
                # Ollama Python 클라이언트로 번역 요청
                response = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={
                        'temperature': self.temperature,
                        'top_p': 0.9,
                        'top_k': 40,
                        'repeat_penalty': 1.1
                    }
                )
                
                translation = response.get('response', '').strip()
                if translation:
                    return translation
                else:
                    print(f"경고: 빈 번역 결과 (시도 {attempt + 1}/{self.max_retries})")
                    
            except ollama.ResponseError as e:
                print(f"Ollama 응답 오류: {e} (시도 {attempt + 1}/{self.max_retries})")
                if "model" in str(e).lower() and "not found" in str(e).lower():
                    print(f"모델 '{self.model_name}'을 찾을 수 없습니다.")
                    print("사용 가능한 모델: ollama list")
                    break
            except ollama.RequestError as e:
                print(f"Ollama 요청 오류: {e} (시도 {attempt + 1}/{self.max_retries})")
                if "connection" in str(e).lower():
                    print("Ollama 서비스가 실행되지 않았을 수 있습니다.")
                    print("서비스 시작: ollama serve")
                    break
            except Exception as e:
                print(f"번역 오류: {e} (시도 {attempt + 1}/{self.max_retries})")
            
            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)  # 지수 백오프
        
        print(f"오류: {self.max_retries}번 시도 후 번역 실패")
        return None
    
    def translate_chunks(self, input_dir: str, output_dir: str) -> Dict[str, any]:
        """청크 디렉토리 전체 번역"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # 입력 디렉토리 확인
        if not input_path.exists():
            raise FileNotFoundError(f"입력 디렉토리를 찾을 수 없습니다: {input_dir}")
        
        chunks_dir = input_path / "chunks"
        if not chunks_dir.exists():
            raise FileNotFoundError(f"청크 디렉토리를 찾을 수 없습니다: {chunks_dir}")
        
        # 청크 인덱스 로드
        chunk_index_file = chunks_dir / "chunk_index.json"
        if not chunk_index_file.exists():
            raise FileNotFoundError(f"청크 인덱스를 찾을 수 없습니다: {chunk_index_file}")
        
        with open(chunk_index_file, 'r', encoding='utf-8') as f:
            chunk_index = json.load(f)
        
        # 출력 디렉토리 생성
        output_path.mkdir(parents=True, exist_ok=True)
        translated_chunks_dir = output_path / "translated_chunks"
        translated_chunks_dir.mkdir(exist_ok=True)
        
        # 번역 진행 상황 파일
        progress_file = output_path / "translation_progress.json"
        progress = self._load_progress(progress_file)
        
        # 번역 통계
        stats = {
            "total_chunks": len(chunk_index["chunks"]),
            "completed": len(progress.get("completed", [])),
            "failed": len(progress.get("failed", [])),
            "start_time": time.time(),
            "model_name": self.model_name
        }
        
        print(f"📚 번역 시작: {stats['total_chunks']}개 청크")
        print(f"🤖 모델: {self.model_name}")
        print(f"✅ 완료: {stats['completed']}개")
        print(f"❌ 실패: {stats['failed']}개")
        print("=" * 50)
        
        # 진행바 설정
        pbar = tqdm(
            chunk_index["chunks"], 
            desc="번역 진행",
            initial=stats['completed']
        )
        
        for chunk_info in pbar:
            chunk_file = chunk_info["file"]
            
            # 이미 완료된 청크 건너뛰기
            if chunk_file in progress.get("completed", []):
                continue
            
            # 청크 파일 읽기
            chunk_path = chunks_dir / chunk_file
            if not chunk_path.exists():
                print(f"경고: 청크 파일을 찾을 수 없습니다: {chunk_file}")
                progress.setdefault("failed", []).append(chunk_file)
                continue
            
            try:
                with open(chunk_path, 'r', encoding='utf-8') as f:
                    original_text = f.read()
                
                # 번역 수행
                pbar.set_description(f"번역 중: {chunk_file}")
                translated_text = self.translate_text(original_text)
                
                if translated_text:
                    # 번역 결과 저장
                    output_file = translated_chunks_dir / f"ko_{chunk_file}"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(translated_text)
                    
                    # 진행 상황 업데이트
                    progress.setdefault("completed", []).append(chunk_file)
                    if chunk_file in progress.get("failed", []):
                        progress["failed"].remove(chunk_file)
                    
                    stats["completed"] += 1
                else:
                    # 실패 기록
                    progress.setdefault("failed", []).append(chunk_file)
                    stats["failed"] += 1
                    print(f"실패: {chunk_file}")
                
                # 진행 상황 저장
                self._save_progress(progress_file, progress)
                
            except Exception as e:
                print(f"오류 처리 중 {chunk_file}: {e}")
                progress.setdefault("failed", []).append(chunk_file)
                stats["failed"] += 1
                self._save_progress(progress_file, progress)
        
        pbar.close()
        
        # 번역 완료 통계
        stats["end_time"] = time.time()
        stats["duration"] = stats["end_time"] - stats["start_time"]
        
        # 번역 인덱스 생성
        self._create_translation_index(output_path, chunk_index, stats)
        
        return stats
    
    def _load_progress(self, progress_file: Path) -> Dict:
        """번역 진행 상황 로드"""
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"completed": [], "failed": []}
    
    def _save_progress(self, progress_file: Path, progress: Dict):
        """번역 진행 상황 저장"""
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"진행 상황 저장 오류: {e}")
    
    def _create_translation_index(self, output_path: Path, original_index: Dict, stats: Dict):
        """번역 인덱스 파일 생성"""
        translation_index = {
            "translation_info": {
                "model": self.model_name,
                "temperature": self.temperature,
                "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats["start_time"])),
                "end_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stats["end_time"])),
                "duration_minutes": round(stats["duration"] / 60, 2),
                "total_chunks": stats["total_chunks"],
                "completed_chunks": stats["completed"],
                "failed_chunks": stats["failed"]
            },
            "original_info": original_index
        }
        
        index_file = output_path / "translation_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(translation_index, f, ensure_ascii=False, indent=2)

def main():
    """번역기 테스트 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ollama 번역기")
    parser.add_argument("input_dir", help="입력 디렉토리 (청크가 있는 디렉토리)")
    parser.add_argument("output_dir", help="출력 디렉토리")
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama 모델명")
    parser.add_argument("--url", default="http://localhost:11434", help="Ollama 서버 URL")
    parser.add_argument("--temperature", type=float, default=0.1, help="번역 온도")
    
    args = parser.parse_args()
    
    # 번역기 초기화
    translator = OllamaTranslator(
        model_name=args.model,
        base_url=args.url,
        temperature=args.temperature
    )
    
    # 연결 확인
    if not translator.check_ollama_connection():
        print("❌ Ollama 서버에 연결할 수 없습니다.")
        print(f"서버 URL: {args.url}")
        print("Ollama가 실행 중인지 확인해주세요.")
        return
    
    if not translator.check_model_available():
        print(f"❌ 모델 '{args.model}'을 찾을 수 없습니다.")
        print("사용 가능한 모델 목록을 확인해주세요: ollama list")
        return
    
    print("✅ Ollama 연결 확인 완료")
    
    # 번역 수행
    try:
        stats = translator.translate_chunks(args.input_dir, args.output_dir)
        
        print("\n" + "=" * 50)
        print("📊 번역 완료!")
        print(f"총 청크: {stats['total_chunks']}개")
        print(f"완료: {stats['completed']}개")
        print(f"실패: {stats['failed']}개")
        print(f"소요 시간: {stats['duration'] / 60:.1f}분")
        print(f"번역 결과: {args.output_dir}")
        
    except Exception as e:
        print(f"❌ 번역 오류: {e}")

if __name__ == "__main__":
    main()