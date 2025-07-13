#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ollama
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import hashlib
from functools import lru_cache

from .prompts import get_translation_prompt

class OllamaTranslator:
    """Ollama Python 라이브러리를 사용한 영어→한국어 번역기"""
    
    def __init__(self, 
                 model_name="qwen2.5:14b",
                 temperature=0.1,
                 max_retries=3,
                 genre=None,  # None이면 자동 감지
                 max_workers=4,
                 batch_size=5,
                 enable_cache=True,
                 num_gpu_layers=None):
        """
        Args:
            model_name: 사용할 Ollama 모델명
            temperature: 번역 일관성을 위한 낮은 온도값 (0.0-2.0)
            max_retries: 번역 실패시 재시도 횟수
            genre: 소설 장르 (fantasy, sci-fi, romance, mystery, general)
            max_workers: 병렬 처리 워커 수 (기본값: 4)
            batch_size: 배치 처리 크기 (기본값: 5)
            enable_cache: 캐싱 활성화 여부 (기본값: True)
            num_gpu_layers: GPU에 로드할 레이어 수 (None이면 자동)
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries
        self.genre = genre
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.enable_cache = enable_cache
        self.num_gpu_layers = num_gpu_layers
        
        # Ollama 클라이언트 초기화
        self.client = ollama.Client()
        
        # 장르 설정 (자동 감지 지원)
        self.genre = genre if genre is not None else "fantasy"  # 기본값
        self.auto_detect_genre = genre is None  # 자동 감지 여부
        
        # 장르별 번역 프롬프트 설정
        self.translation_prompt = get_translation_prompt(self.genre)
        
        # 캐시 초기화
        if enable_cache:
            self.cache_lock = threading.Lock()
            self.translation_cache = {}
        
        # 통계 추적
        self.stats_lock = threading.Lock()
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_translations": 0
        }
    
    def check_ollama_available(self) -> bool:
        """Ollama 서비스 사용 가능 여부 확인"""
        try:
            # 간단한 API 호출로 Ollama 서비스 확인
            self.client.list()
            return True
        except Exception:
            return False
    
    def detect_genre_from_text(self, text_sample: str) -> str:
        """텍스트 샘플을 분석하여 자동으로 장르를 감지합니다"""
        try:
            # 장르 감지용 프롬프트
            genre_prompt = f"""다음 텍스트를 분석하여 소설의 장르를 판단해주세요.
가능한 장르: fantasy, sci-fi, romance, mystery, horror, general

텍스트:
{text_sample[:1000]}

위 텍스트의 장르를 하나만 선택하여 답해주세요 (단어만): """

            response = self.client.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": genre_prompt}],
                options={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "num_gpu_layers": self.num_gpu_layers
                }
            )
            
            detected_genre = response['message']['content'].strip().lower()
            
            # 유효한 장르인지 확인
            valid_genres = ["fantasy", "sci-fi", "romance", "mystery", "horror", "general"]
            if detected_genre in valid_genres:
                return detected_genre
            else:
                # 부분 매칭 시도
                for genre in valid_genres:
                    if genre in detected_genre:
                        return genre
                return "general"  # 기본값
                
        except Exception as e:
            print(f"⚠️  장르 자동 감지 실패: {e}")
            return "general"  # 실패시 기본값
    
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
    
    def _get_cache_key(self, text: str) -> str:
        """텍스트의 캐시 키 생성"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _check_cache(self, text: str) -> Optional[str]:
        """캐시에서 번역 확인"""
        if not self.enable_cache:
            return None
        
        cache_key = self._get_cache_key(text)
        with self.cache_lock:
            if cache_key in self.translation_cache:
                with self.stats_lock:
                    self.stats["cache_hits"] += 1
                return self.translation_cache[cache_key]
        
        with self.stats_lock:
            self.stats["cache_misses"] += 1
        return None
    
    def _save_to_cache(self, text: str, translation: str):
        """번역을 캐시에 저장"""
        if not self.enable_cache:
            return
        
        cache_key = self._get_cache_key(text)
        with self.cache_lock:
            self.translation_cache[cache_key] = translation
    
    def translate_text(self, text: str) -> Optional[str]:
        """단일 텍스트 블록 번역"""
        if not text.strip():
            return ""
        
        # 캐시 확인
        cached_translation = self._check_cache(text)
        if cached_translation:
            return cached_translation
        
        # 프롬프트 생성
        prompt = self.translation_prompt.format(text=text.strip())
        
        for attempt in range(self.max_retries):
            try:
                # 모델 옵션 설정
                options = {
                    'temperature': self.temperature,
                    'top_p': 0.9,
                    'top_k': 40,
                    'repeat_penalty': 1.1
                }
                
                # GPU 레이어 설정이 있으면 추가
                if self.num_gpu_layers is not None:
                    options['num_gpu'] = self.num_gpu_layers
                
                # Ollama Python 클라이언트로 번역 요청
                response = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options=options
                )
                
                translation = response.get('response', '').strip()
                if translation:
                    # 캐시에 저장
                    self._save_to_cache(text, translation)
                    with self.stats_lock:
                        self.stats["total_translations"] += 1
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
    
    def translate_batch(self, texts: List[str]) -> List[Optional[str]]:
        """배치 텍스트 번역"""
        results = []
        for text in texts:
            result = self.translate_text(text)
            results.append(result)
        return results
    
    def _translate_chunk_worker(self, chunk_info: Dict, chunks_dir: Path, 
                                translated_chunks_dir: Path, progress: Dict, 
                                progress_file: Path, pbar: tqdm) -> Tuple[str, bool]:
        """단일 청크 번역 워커"""
        chunk_file = chunk_info["file"]
        
        # 이미 완료된 청크 건너뛰기
        if chunk_file in progress.get("completed", []):
            return chunk_file, True
        
        # 청크 파일 읽기
        chunk_path = chunks_dir / chunk_file
        if not chunk_path.exists():
            print(f"경고: 청크 파일을 찾을 수 없습니다: {chunk_file}")
            with self.stats_lock:
                progress.setdefault("failed", []).append(chunk_file)
            return chunk_file, False
        
        try:
            with open(chunk_path, 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            # 번역 수행
            translated_text = self.translate_text(original_text)
            
            if translated_text:
                # 번역 결과 저장
                output_file = translated_chunks_dir / f"ko_{chunk_file}"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(translated_text)
                
                # 진행 상황 업데이트
                with self.stats_lock:
                    progress.setdefault("completed", []).append(chunk_file)
                    if chunk_file in progress.get("failed", []):
                        progress["failed"].remove(chunk_file)
                    pbar.update(1)
                
                return chunk_file, True
            else:
                # 실패 기록
                with self.stats_lock:
                    progress.setdefault("failed", []).append(chunk_file)
                print(f"실패: {chunk_file}")
                return chunk_file, False
                
        except Exception as e:
            print(f"오류 처리 중 {chunk_file}: {e}")
            with self.stats_lock:
                progress.setdefault("failed", []).append(chunk_file)
            return chunk_file, False
    
    def translate_chunks(self, input_dir: str, output_dir: str, use_parallel: bool = True) -> Dict[str, any]:
        """청크 디렉토리 전체 번역 (병렬 처리 지원)"""
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
            "model_name": self.model_name,
            "parallel_mode": use_parallel,
            "max_workers": self.max_workers if use_parallel else 1
        }
        
        # 자동 장르 감지 (필요한 경우)
        if self.auto_detect_genre and len(chunk_index["chunks"]) > 0:
            print("🔍 장르 자동 감지 중...")
            
            # 첫 번째 청크를 사용하여 장르 감지
            first_chunk_file = chunk_index["chunks"][0]["file"]
            first_chunk_path = chunks_dir / first_chunk_file
            
            try:
                with open(first_chunk_path, 'r', encoding='utf-8') as f:
                    sample_text = f.read()
                
                detected_genre = self.detect_genre_from_text(sample_text)
                
                if detected_genre != self.genre:
                    print(f"📚 감지된 장르: {detected_genre} (기본값 {self.genre}에서 변경)")
                    self.genre = detected_genre
                    # 프롬프트 업데이트
                    from .prompts import get_translation_prompt
                    self.translation_prompt = get_translation_prompt(self.genre)
                else:
                    print(f"📚 장르: {self.genre} (자동 감지로 확인됨)")
            except Exception as e:
                print(f"⚠️  장르 감지 실패, 기본값 사용: {self.genre}")
        else:
            print(f"📚 장르: {self.genre} (사용자 지정)")

        print(f"📚 번역 시작: {stats['total_chunks']}개 청크")
        print(f"🤖 모델: {self.model_name}")
        print(f"⚡ 병렬 처리: {'활성화' if use_parallel else '비활성화'} (워커: {stats['max_workers']})")
        print(f"✅ 완료: {stats['completed']}개")
        print(f"❌ 실패: {stats['failed']}개")
        if self.enable_cache:
            print(f"💾 캐싱: 활성화")
        print("=" * 50)
        
        # 진행바 설정 (macOS zsh + oh-my-zsh 호환)
        # 터미널 환경 체크
        term = os.environ.get('TERM', '')
        is_dumb_terminal = term in ['dumb', ''] or os.environ.get('CI') == 'true'
        
        pbar = tqdm(
            total=len(chunk_index["chunks"]),
            desc="번역 진행",
            initial=stats['completed'],
            ncols=80,  # 터미널 너비 고정
            ascii=True,  # ASCII 문자 사용 (유니코드 문제 방지)
            bar_format='{desc}: {percentage:3.0f}%|{bar:20}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
            disable=is_dumb_terminal,  # dumb 터미널에서는 비활성화
            dynamic_ncols=False,  # 동적 너비 비활성화
            leave=True,  # 완료 후에도 진행바 유지
            mininterval=0.5,  # 업데이트 최소 간격 (0.5초)
            maxinterval=2.0   # 업데이트 최대 간격 (2초)
        )
        
        if use_parallel:
            # 병렬 처리
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 미완료 청크만 추출
                pending_chunks = [
                    chunk for chunk in chunk_index["chunks"]
                    if chunk["file"] not in progress.get("completed", [])
                ]
                
                # 배치별로 나누어 처리
                for i in range(0, len(pending_chunks), self.batch_size):
                    batch = pending_chunks[i:i + self.batch_size]
                    
                    # 배치 단위로 작업 제출
                    futures = {
                        executor.submit(
                            self._translate_chunk_worker,
                            chunk_info, chunks_dir, translated_chunks_dir,
                            progress, progress_file, pbar
                        ): chunk_info for chunk_info in batch
                    }
                    
                    # 완료된 작업 처리
                    for future in as_completed(futures):
                        chunk_file, success = future.result()
                        if success:
                            stats["completed"] = len(progress.get("completed", []))
                        else:
                            stats["failed"] = len(progress.get("failed", []))
                        
                        # 진행 상황 저장 (배치마다)
                        self._save_progress(progress_file, progress)
        else:
            # 순차 처리 (기존 방식)
            for chunk_info in chunk_index["chunks"]:
                chunk_file, success = self._translate_chunk_worker(
                    chunk_info, chunks_dir, translated_chunks_dir,
                    progress, progress_file, pbar
                )
                if success:
                    stats["completed"] = len(progress.get("completed", []))
                else:
                    stats["failed"] = len(progress.get("failed", []))
                
                # 진행 상황 저장
                self._save_progress(progress_file, progress)
        
        pbar.close()
        
        # 번역 완료 통계
        stats["end_time"] = time.time()
        stats["duration"] = stats["end_time"] - stats["start_time"]
        
        # 캐시 통계 추가
        if self.enable_cache:
            stats["cache_stats"] = {
                "hits": self.stats["cache_hits"],
                "misses": self.stats["cache_misses"],
                "hit_rate": (self.stats["cache_hits"] / 
                           (self.stats["cache_hits"] + self.stats["cache_misses"]) * 100
                           if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0 else 0)
            }
        
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
    parser.add_argument("--temperature", type=float, default=0.1, help="번역 온도")
    parser.add_argument("--genre", default="fantasy", choices=["fantasy", "sci-fi", "romance", "mystery", "general"],
                       help="소설 장르")
    parser.add_argument("--max-workers", type=int, default=4, help="병렬 처리 워커 수")
    parser.add_argument("--batch-size", type=int, default=5, help="배치 처리 크기")
    parser.add_argument("--no-parallel", action="store_true", help="병렬 처리 비활성화")
    parser.add_argument("--no-cache", action="store_true", help="캐싱 비활성화")
    parser.add_argument("--num-gpu-layers", type=int, help="GPU에 로드할 레이어 수")
    
    args = parser.parse_args()
    
    # 번역기 초기화
    translator = OllamaTranslator(
        model_name=args.model,
        temperature=args.temperature,
        genre=args.genre,
        max_workers=args.max_workers,
        batch_size=args.batch_size,
        enable_cache=not args.no_cache,
        num_gpu_layers=args.num_gpu_layers
    )
    
    # 연결 확인
    if not translator.check_ollama_available():
        print("❌ Ollama 서버에 연결할 수 없습니다.")
        print("Ollama가 실행 중인지 확인해주세요.")
        return
    
    if not translator.check_model_available():
        print(f"❌ 모델 '{args.model}'을 찾을 수 없습니다.")
        print("사용 가능한 모델 목록을 확인해주세요: ollama list")
        return
    
    print("✅ Ollama 연결 확인 완료")
    
    # 번역 수행
    try:
        stats = translator.translate_chunks(
            args.input_dir, 
            args.output_dir,
            use_parallel=not args.no_parallel
        )
        
        print("\n" + "=" * 50)
        print("📊 번역 완료!")
        print(f"총 청크: {stats['total_chunks']}개")
        print(f"완료: {stats['completed']}개")
        print(f"실패: {stats['failed']}개")
        print(f"소요 시간: {stats['duration'] / 60:.1f}분")
        if "cache_stats" in stats:
            print(f"캐시 히트율: {stats['cache_stats']['hit_rate']:.1f}%")
        print(f"번역 결과: {args.output_dir}")
        
    except Exception as e:
        print(f"❌ 번역 오류: {e}")

if __name__ == "__main__":
    main()