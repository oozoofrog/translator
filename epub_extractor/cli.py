#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI 모듈

명령줄 인터페이스와 관련된 기능들을 제공합니다.
"""

import argparse
import os
import sys

from config.config import (
    DEFAULT_GENRE,
    DEFAULT_MAX_CHUNK_SIZE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MIN_CHUNK_SIZE,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_TRANSLATED_DIR,
    SUPPORTED_GENRES,
)

from .builder import build_korean_epub, rebuild_epub_from_extracted
from .extractor import EPUBExtractor
from .prompts import get_genre_list
from .translator import OllamaTranslator
from .utils import validate_chunk_sizes

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def create_parser():
    """
    명령줄 인수 파서 생성

    Returns:
        argparse.ArgumentParser: 설정된 파서
    """
    parser = argparse.ArgumentParser(
        description="EPUB 파일을 챕터별로 분리하고 LLM 번역용 청크로 나누는 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  %(prog)s extract novel.epub                     # 기본 설정으로 추출
  %(prog)s extract novel.epub --max-chunk-size 2000 # 작은 청크로 분할
  %(prog)s extract novel.epub --no-chunks         # 챕터만 추출
  %(prog)s translate novel/ translated/           # 번역 수행
  %(prog)s translate novel/ translated/ --model llama3.1:8b
  %(prog)s build novel.epub translated/           # 한글 EPUB 생성
  %(prog)s fix translated/                        # 번역 문제 감지 및 재번역

청크 크기 가이드라인:
  - 작은 청크 (1000-2000자): 더 정확한 번역, 문맥 손실 가능
  - 중간 청크 (2000-4000자): 균형있는 번역 품질 (권장)
  - 큰 청크 (4000-6000자): 문맥 보존, 번역 속도 저하 가능
        """,
    )

    # 서브커맨드 생성
    subparsers = parser.add_subparsers(dest="command", help="사용할 명령")

    # extract 명령어
    extract_parser = subparsers.add_parser("extract", help="EPUB 파일 추출")
    extract_parser = _add_extract_arguments(extract_parser)

    # translate 명령어
    translate_parser = subparsers.add_parser("translate", help="추출된 청크 번역")
    translate_parser = _add_translate_arguments(translate_parser)

    # build 명령어
    build_parser = subparsers.add_parser("build", help="번역된 텍스트로 한글 EPUB 생성")
    build_parser = _add_build_arguments(build_parser)

    # rebuild 명령어
    rebuild_parser = subparsers.add_parser("rebuild", help="추출된 HTML 파일로 EPUB 재구성")
    rebuild_parser = _add_rebuild_arguments(rebuild_parser)

    # fix 명령어
    fix_parser = subparsers.add_parser("fix", help="번역된 파일의 문제점 감지 및 재번역")
    fix_parser = _add_fix_arguments(fix_parser)

    return parser


def _add_extract_arguments(parser):
    """추출 명령어 인수 추가"""

    parser.add_argument("epub_file", help="추출할 EPUB 파일 경로")

    parser.add_argument(
        "--max-chunk-size",
        type=int,
        default=DEFAULT_MAX_CHUNK_SIZE,
        metavar="N",
        help=f"최대 청크 크기 (문자 수, 기본값: {DEFAULT_MAX_CHUNK_SIZE})",
    )

    parser.add_argument(
        "--min-chunk-size",
        type=int,
        default=DEFAULT_MIN_CHUNK_SIZE,
        metavar="N",
        help=f"최소 청크 크기 (문자 수, 기본값: {DEFAULT_MIN_CHUNK_SIZE})",
    )

    parser.add_argument("--no-chunks", action="store_true", help="청크 파일 생성하지 않음 (챕터 파일만 생성)")

    parser.add_argument("--output-dir", "-o", metavar="DIR", help="출력 디렉토리 (기본값: EPUB 파일명)")

    parser.add_argument("--verbose", "-v", action="store_true", help="상세한 출력 표시")

    parser.add_argument("--extract-only", action="store_true", help="청크 분할 없이 원본 HTML 파일만 추출")

    return parser


def _add_translate_arguments(parser):
    """번역 명령어 인수 추가"""

    parser.add_argument("input_dir", help="추출된 청크가 있는 디렉토리")

    parser.add_argument(
        "output_dir",
        nargs="?",
        default=DEFAULT_TRANSLATED_DIR,
        help=f"번역 결과를 저장할 디렉토리 (기본값: {DEFAULT_TRANSLATED_DIR})",
    )

    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"사용할 Ollama 모델명 (기본값: {DEFAULT_MODEL})")

    parser.add_argument(
        "--temperature", type=float, default=DEFAULT_TEMPERATURE, help=f"번역 온도 (기본값: {DEFAULT_TEMPERATURE})"
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"번역 실패시 재시도 횟수 (기본값: {DEFAULT_MAX_RETRIES})",
    )

    parser.add_argument(
        "--genre",
        choices=get_genre_list(),
        default=DEFAULT_GENRE,
        help=f'소설 장르 (기본값: {DEFAULT_GENRE or "자동 감지"}, 선택: {", ".join(SUPPORTED_GENRES)})',
    )

    parser.add_argument("--resume", action="store_true", help="이전 번역 작업 이어서 진행")

    parser.add_argument("--no-cache", action="store_true", help="번역 캐싱 비활성화")

    parser.add_argument("--num-gpu-layers", type=int, metavar="N", help="GPU에 로드할 레이어 수 (자동 설정시 생략)")

    parser.add_argument("--verbose", "-v", action="store_true", help="상세한 출력 표시")

    return parser


def _add_build_arguments(parser):
    """빌드 명령어 인수 추가"""

    parser.add_argument("original_epub", help="원본 EPUB 파일 경로")

    parser.add_argument("translated_dir", help="번역 결과 디렉토리")

    parser.add_argument("--output", "-o", metavar="FILE", help="출력 EPUB 파일 경로 (기본값: 원본파일명-ko.epub)")

    parser.add_argument("--verbose", "-v", action="store_true", help="상세한 출력 표시")

    return parser


def _add_rebuild_arguments(parser):
    """재구성 명령어 인수 추가"""

    parser.add_argument("original_epub", help="원본 EPUB 파일 경로")

    parser.add_argument("extracted_dir", help="추출된 HTML 파일이 있는 디렉토리")

    parser.add_argument("--output", "-o", metavar="FILE", help="출력 EPUB 파일 경로 (기본값: 원본파일명-rebuilt.epub)")

    parser.add_argument("--verbose", "-v", action="store_true", help="상세한 출력 표시")

    return parser


def _add_fix_arguments(parser):
    """재번역 명령어 인수 추가"""

    parser.add_argument("translated_dir", help="번역된 파일들이 있는 디렉토리")

    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"사용할 Ollama 모델명 (기본값: {DEFAULT_MODEL})")

    parser.add_argument(
        "--temperature", type=float, default=DEFAULT_TEMPERATURE, help=f"번역 온도 (기본값: {DEFAULT_TEMPERATURE})"
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"번역 실패시 재시도 횟수 (기본값: {DEFAULT_MAX_RETRIES})",
    )

    parser.add_argument(
        "--genre",
        choices=get_genre_list(),
        default=DEFAULT_GENRE,
        help=f'소설 장르 (기본값: {DEFAULT_GENRE or "자동 감지"}, 선택: {", ".join(SUPPORTED_GENRES)})',
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="상세한 출력 표시")

    return parser


def validate_extract_arguments(args):
    """
    추출 명령줄 인수 검증

    Args:
        args: 파싱된 인수 객체

    Returns:
        bool: 유효한 인수인 경우 True

    Raises:
        SystemExit: 잘못된 인수인 경우
    """
    # EPUB 파일 존재 확인
    if not os.path.exists(args.epub_file):
        print(f"❌ 파일을 찾을 수 없습니다: {args.epub_file}")
        sys.exit(1)

    # EPUB 파일 확장자 확인
    if not args.epub_file.lower().endswith(".epub"):
        print("❌ EPUB 파일이 아닙니다.")
        sys.exit(1)

    # 청크 크기 검증 (청크 생성하는 경우만)
    if not args.no_chunks and not args.extract_only:
        try:
            validate_chunk_sizes(args.max_chunk_size, args.min_chunk_size)
        except ValueError as e:
            print(f"❌ {e}")
            sys.exit(1)

    return True


def validate_translate_arguments(args):
    """
    번역 명령줄 인수 검증

    Args:
        args: 파싱된 인수 객체

    Returns:
        bool: 유효한 인수인 경우 True

    Raises:
        SystemExit: 잘못된 인수인 경우
    """
    # 입력 디렉토리 존재 확인
    if not os.path.exists(args.input_dir):
        print(f"❌ 입력 디렉토리를 찾을 수 없습니다: {args.input_dir}")
        sys.exit(1)

    # 청크 디렉토리 확인
    chunks_dir = os.path.join(args.input_dir, "chunks")
    if not os.path.exists(chunks_dir):
        print(f"❌ 청크 디렉토리를 찾을 수 없습니다: {chunks_dir}")
        print("먼저 EPUB 파일을 추출해주세요.")
        sys.exit(1)

    # 청크 인덱스 파일 확인
    index_file = os.path.join(chunks_dir, "chunk_index.json")
    if not os.path.exists(index_file):
        print(f"❌ 청크 인덱스 파일을 찾을 수 없습니다: {index_file}")
        sys.exit(1)

    # 온도값 검증
    if not 0.0 <= args.temperature <= 2.0:
        print("❌ 온도값은 0.0~2.0 사이여야 합니다.")
        sys.exit(1)

    return True


def validate_build_arguments(args):
    """
    빌드 명령줄 인수 검증

    Args:
        args: 파싱된 인수 객체

    Returns:
        bool: 유효한 인수인 경우 True

    Raises:
        SystemExit: 잘못된 인수인 경우
    """
    # 원본 EPUB 파일 존재 확인
    if not os.path.exists(args.original_epub):
        print(f"❌ 원본 EPUB 파일을 찾을 수 없습니다: {args.original_epub}")
        sys.exit(1)

    # EPUB 파일 확장자 확인
    if not args.original_epub.lower().endswith(".epub"):
        print("❌ 원본 파일이 EPUB 파일이 아닙니다.")
        sys.exit(1)

    # 번역 디렉토리 존재 확인
    if not os.path.exists(args.translated_dir):
        print(f"❌ 번역 디렉토리를 찾을 수 없습니다: {args.translated_dir}")
        sys.exit(1)

    # 번역된 청크 디렉토리 확인
    translated_chunks_dir = os.path.join(args.translated_dir, "translated_chunks")
    if not os.path.exists(translated_chunks_dir):
        print(f"❌ 번역된 청크 디렉토리를 찾을 수 없습니다: {translated_chunks_dir}")
        print("먼저 번역을 수행해주세요.")
        sys.exit(1)

    # 번역 인덱스 파일 확인
    translation_index_file = os.path.join(args.translated_dir, "translation_index.json")
    if not os.path.exists(translation_index_file):
        print(f"❌ 번역 인덱스 파일을 찾을 수 없습니다: {translation_index_file}")
        sys.exit(1)

    return True


def validate_rebuild_arguments(args):
    """
    재구성 명령줄 인수 검증

    Args:
        args: 파싱된 인수 객체

    Returns:
        bool: 유효한 인수인 경우 True

    Raises:
        SystemExit: 잘못된 인수인 경우
    """
    # 원본 EPUB 파일 존재 확인
    if not os.path.exists(args.original_epub):
        print(f"❌ 원본 EPUB 파일을 찾을 수 없습니다: {args.original_epub}")
        sys.exit(1)

    # EPUB 파일 확장자 확인
    if not args.original_epub.lower().endswith(".epub"):
        print("❌ 원본 파일이 EPUB 파일이 아닙니다.")
        sys.exit(1)

    # 추출 디렉토리 존재 확인
    if not os.path.exists(args.extracted_dir):
        print(f"❌ 추출 디렉토리를 찾을 수 없습니다: {args.extracted_dir}")
        sys.exit(1)

    # chapters 디렉토리 확인
    chapters_dir = os.path.join(args.extracted_dir, "chapters")
    if not os.path.exists(chapters_dir):
        print(f"❌ chapters 디렉토리를 찾을 수 없습니다: {chapters_dir}")
        print("먼저 EPUB을 --extract-only 옵션으로 추출해주세요.")
        sys.exit(1)

    # info.json 파일 확인
    info_file = os.path.join(args.extracted_dir, "info.json")
    if not os.path.exists(info_file):
        print(f"❌ info.json 파일을 찾을 수 없습니다: {info_file}")
        sys.exit(1)

    return True


def print_extract_banner(args):
    """
    추출 시작 배너 출력

    Args:
        args: 파싱된 인수 객체
    """
    print("📚 EPUB 추출기 v2.0.0")
    print("=" * 40)
    print(f"📖 파일: {args.epub_file}")

    if args.extract_only:
        print("📋 모드: 원본 HTML 추출 (청크 분할 없음)")
    elif not args.no_chunks:
        print(f"📐 청크 크기: {args.min_chunk_size}-{args.max_chunk_size} 문자")
    else:
        print("📋 모드: 챕터 파일만 생성")

    if args.output_dir:
        print(f"📁 출력: {args.output_dir}")

    print()


def print_translate_banner(args):
    """
    번역 시작 배너 출력

    Args:
        args: 파싱된 인수 객체
    """
    print("🌏 Ollama 번역기 v2.0.0")
    print("=" * 40)
    print(f"📁 입력: {args.input_dir}")
    print(f"📁 출력: {args.output_dir}")
    print(f"🤖 모델: {args.model}")
    print(f"📚 장르: {args.genre}")
    print(f"🌡️ 온도: {args.temperature}")
    print("⚡ 처리 방식: 순차 처리")
    print(f"💾 캐싱: {'활성화' if not args.no_cache else '비활성화'}")
    if args.num_gpu_layers:
        print(f"🎮 GPU 레이어: {args.num_gpu_layers}")
    if args.resume:
        print("🔄 모드: 이어서 진행")
    print()


def print_build_banner(args):
    """
    빌드 시작 배너 출력

    Args:
        args: 파싱된 인수 객체
    """
    print("📚 EPUB 빌더 v1.0.0")
    print("=" * 40)
    print(f"📖 원본: {args.original_epub}")
    print(f"📁 번역: {args.translated_dir}")
    if args.output:
        print(f"📄 출력: {args.output}")
    else:
        base_name = os.path.splitext(os.path.basename(args.original_epub))[0]
        print(f"📄 출력: {base_name}-ko.epub")
    print()


def print_rebuild_banner(args):
    """
    재구성 시작 배너 출력

    Args:
        args: 파싱된 인수 객체
    """
    print("📚 EPUB 재구성기 v1.0.0")
    print("=" * 40)
    print(f"📖 원본: {args.original_epub}")
    print(f"📁 추출: {args.extracted_dir}")
    if args.output:
        print(f"📄 출력: {args.output}")
    else:
        base_name = os.path.splitext(os.path.basename(args.original_epub))[0]
        print(f"📄 출력: {base_name}-rebuilt.epub")
    print()


def run_extract_command(args):
    """
    추출 명령어 실행

    Args:
        args: 파싱된 인수 객체
    """
    # 인수 검증
    validate_extract_arguments(args)

    # 시작 배너 출력
    if args.verbose or True:  # 항상 표시
        print_extract_banner(args)

    # 추출기 생성 및 실행
    if args.extract_only:
        # extract_only 모드: 청크 생성 없이 원본 HTML만 추출
        extractor = EPUBExtractor(
            args.epub_file,
            max_chunk_size=args.max_chunk_size,
            min_chunk_size=args.min_chunk_size,
            create_chunks=False,
            extract_raw_html=True,
        )
    else:
        # 일반 모드
        create_chunks = not args.no_chunks
        extractor = EPUBExtractor(
            args.epub_file,
            max_chunk_size=args.max_chunk_size,
            min_chunk_size=args.min_chunk_size,
            create_chunks=create_chunks,
        )

    extractor.extract(args.output_dir)

    # 성공 메시지
    if args.verbose:
        metadata = extractor.get_metadata()
        print("\n📊 추출 통계:")
        print(f"   📚 총 챕터: {extractor.get_chapter_count()}개")
        if metadata.get("title"):
            print(f"   📖 제목: {metadata['title']}")
        if metadata.get("author"):
            print(f"   ✍️  저자: {metadata['author']}")


def run_translate_command(args):
    """
    번역 명령어 실행

    Args:
        args: 파싱된 인수 객체
    """
    # 인수 검증
    validate_translate_arguments(args)

    # 시작 배너 출력
    if args.verbose or True:  # 항상 표시
        print_translate_banner(args)

    # 번역기 생성
    translator = OllamaTranslator(
        model_name=args.model,
        temperature=args.temperature,
        max_retries=args.max_retries,
        genre=args.genre,
        enable_cache=not args.no_cache,
        num_gpu_layers=args.num_gpu_layers,
    )

    # Ollama 서비스 확인
    if not translator.check_ollama_available():
        print("❌ Ollama 서비스에 연결할 수 없습니다.")
        print("Ollama가 실행되고 있는지 확인해주세요.")
        print("서비스 시작: ollama serve")
        print("또는 자동 설치: ./activate.sh")
        sys.exit(1)

    if not translator.check_model_available():
        print(f"❌ 모델 '{args.model}'을 찾을 수 없습니다.")
        print("사용 가능한 모델 목록을 확인해주세요: ollama list")
        print(f"모델 다운로드: ollama pull {args.model}")
        sys.exit(1)

    print("✅ Ollama 설정 확인 완료")

    # 모델 사전 로드 (첫 번째 번역을 빠르게 하기 위해)
    print("🚀 모델 로딩 중...")
    if translator.ensure_model_loaded():
        print("✅ 모델 로딩 완료!")
    print()

    # 번역 수행
    stats = translator.translate_chunks(args.input_dir, args.output_dir)

    # 완료 메시지
    print("\n" + "=" * 50)
    print("📊 번역 완료!")
    print(f"총 청크: {stats['total_chunks']}개")
    print(f"완료: {stats['completed']}개")
    print(f"실패: {stats['failed']}개")
    print(f"소요 시간: {stats['duration'] / 60:.1f}분")
    if "cache_stats" in stats:
        print(f"캐시 히트율: {stats['cache_stats']['hit_rate']:.1f}%")
    print(f"번역 결과: {args.output_dir}")


def run_build_command(args):
    """
    빌드 명령어 실행

    Args:
        args: 파싱된 인수 객체
    """
    # 인수 검증
    validate_build_arguments(args)

    # 시작 배너 출력
    if args.verbose or True:  # 항상 표시
        print_build_banner(args)

    try:
        # EPUB 빌드 수행
        output_file = build_korean_epub(args.original_epub, args.translated_dir, args.output)

        # 완료 메시지
        print("\n" + "=" * 50)
        print("📚 한글 EPUB 생성 완료!")
        print(f"원본: {args.original_epub}")
        print(f"출력: {output_file}")

        # 파일 정보 표시
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            print(f"크기: {file_size:.1f} MB")

    except Exception as e:
        print(f"\n❌ EPUB 생성 중 오류 발생: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def run_rebuild_command(args):
    """
    재구성 명령어 실행

    Args:
        args: 파싱된 인수 객체
    """
    # 인수 검증
    validate_rebuild_arguments(args)

    # 시작 배너 출력
    if args.verbose or True:  # 항상 표시
        print_rebuild_banner(args)

    try:
        # EPUB 재구성 수행
        output_file = rebuild_epub_from_extracted(args.original_epub, args.extracted_dir, args.output)

        # 완료 메시지
        print("\n" + "=" * 50)
        print("📚 EPUB 재구성 완료!")
        print(f"원본: {args.original_epub}")
        print(f"출력: {output_file}")

        # 파일 정보 표시
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
            print(f"크기: {file_size:.1f} MB")

    except Exception as e:
        print(f"\n❌ EPUB 재구성 중 오류 발생: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def run_fix_command(args):
    """
    재번역 명령어 실행

    Args:
        args: 파싱된 인수 객체
    """
    # 인수 검증
    if not os.path.exists(args.translated_dir):
        print(f"❌ 번역 디렉토리를 찾을 수 없습니다: {args.translated_dir}")
        sys.exit(1)

    # 시작 배너 출력
    if args.verbose or True:  # 항상 표시
        print("=" * 50)
        print("🔧 번역 문제점 검사 및 재번역")
        print("=" * 50)
        print(f"번역 디렉토리: {args.translated_dir}")
        print(f"모델: {args.model}")
        print(f"장르: {args.genre or '자동 감지'}")
        print("=" * 50)

    try:
        # 번역기 초기화
        translator = OllamaTranslator(
            model_name=args.model, temperature=args.temperature, max_retries=args.max_retries, genre=args.genre
        )

        # Ollama 연결 확인
        if not translator.check_ollama_available():
            print("❌ Ollama 서버에 연결할 수 없습니다.")
            print("Ollama가 실행 중인지 확인해주세요: ollama serve")
            sys.exit(1)

        if not translator.check_model_available():
            print(f"❌ 모델 '{args.model}'을 찾을 수 없습니다.")
            print("사용 가능한 모델 목록을 확인해주세요: ollama list")
            sys.exit(1)

        print("✅ Ollama 연결 확인 완료")

        # 재번역 수행
        stats = translator.fix_translated_chunks(args.translated_dir)

        # 성공 메시지
        if len(stats["fixed_files"]) > 0:
            print("\n🎉 재번역이 완료되었습니다!")
            print("이제 build 명령어로 새로운 EPUB을 생성할 수 있습니다.")
        else:
            print("\n✨ 모든 번역 파일이 정상적입니다!")

    except Exception as e:
        print(f"\n❌ 재번역 중 오류 발생: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def main():
    """
    메인 실행 함수
    """
    try:
        # 명령줄 인수 파싱
        parser = create_parser()
        args = parser.parse_args()

        # 명령어가 지정되지 않은 경우
        if not args.command:
            parser.print_help()
            sys.exit(1)

        # 명령어별 실행
        if args.command == "extract":
            run_extract_command(args)
        elif args.command == "translate":
            run_translate_command(args)
        elif args.command == "build":
            run_build_command(args)
        elif args.command == "rebuild":
            run_rebuild_command(args)
        elif args.command == "fix":
            run_fix_command(args)
        else:
            print(f"❌ 알 수 없는 명령어: {args.command}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏸️  사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 예상치 못한 오류가 발생했습니다: {e}")
        if hasattr(args, "verbose") and args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
