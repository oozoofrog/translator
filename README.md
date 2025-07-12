# EPUB 파일 추출기 및 번역기 (개선된 버전)

EPUB 파일의 내용을 챕터별로 분리하고 LLM 번역에 적합한 크기의 청크로 나누며, Ollama를 사용하여 영어→한국어 번역을 수행하는 Python 도구입니다.

## ✨ 주요 기능

### 📚 기본 기능
- EPUB 파일의 목차 구조 자동 분석
- 챕터별로 내용을 개별 텍스트 파일로 분리
- 문단 구조를 보존하는 개선된 HTML 파싱
- 제목, 저자 등 메타데이터 자동 추출
- 불필요한 페이지 자동 필터링 (titlepage, cover 등)

### 🤖 LLM 번역 최적화
- **지능형 텍스트 분할**: 문단 → 문장 → 단어 순으로 적절하게 분할
- **번역 적합한 청크 크기**: 기본값 1000-3000자 (조정 가능)
- **문맥 보존**: 문단 경계를 지켜 자연스러운 번역 단위 생성
- **청크 인덱스**: 번역 진행 상황 추적 가능

### 🌏 Ollama 번역 기능
- **자동 번역**: Ollama를 사용한 영어→한국어 자동 번역
- **진행 상황 추적**: 실시간 번역 진행도 표시 및 중단/재개 지원
- **오류 복구**: 번역 실패시 자동 재시도 및 오류 처리
- **번역 품질 최적화**: 소설 번역에 특화된 프롬프트 사용
- **배치 처리**: 여러 청크를 자동으로 순차 번역

### 📚 EPUB 재조립 기능
- **한글 EPUB 생성**: 번역된 텍스트를 원본 구조 그대로 EPUB으로 재조립
- **메타데이터 보존**: 원본의 제목, 저자 등 정보 유지 및 한글판 표시 추가
- **구조 유지**: 원본 EPUB의 챕터 순서와 목차 구조 완전 보존
- **자동 파일명**: 원본 파일명에 `-ko` 접미사를 붙여 자동 생성

## 🚀 설치 및 실행

### 1. 자동 설치 및 설정
```bash
# 모든 것을 자동으로 설치하고 설정
./activate.sh
```

이 스크립트는 다음을 자동으로 수행합니다:
- Ollama 설치 확인 및 자동 설치
- Python 가상환경 생성 및 활성화
- 필요한 의존성 설치
- 기본 번역 모델(llama3.1:8b) 다운로드

### 2. 수동 설치 (필요시)
```bash
# Ollama 수동 설치
curl -fsSL https://ollama.com/install.sh | sh

# 번역 모델 다운로드
ollama pull llama3.1:8b

# Python 의존성 설치
pip install -r requirements.txt
```

### 3. EPUB 파일 추출
```bash
# 기본 추출
./extract.sh "소설파일.epub"

# 작은 청크로 분할 (더 세밀한 번역)
./extract.sh "소설파일.epub" --max-chunk-size 2000 --min-chunk-size 500

# 챕터 파일만 생성 (청크 없음)
./extract.sh "소설파일.epub" --no-chunks

# 출력 디렉토리 지정
./extract.sh "소설파일.epub" --output-dir "번역프로젝트"
```

### 4. 번역 실행
```bash
# 기본 번역 (추출된 디렉토리 → 번역 출력 디렉토리)
./translate.sh "소설파일/" "번역결과/"

# 다른 모델 사용
./translate.sh "소설파일/" "번역결과/" --model llama3:8b

# 번역 설정 조정
./translate.sh "소설파일/" "번역결과/" --temperature 0.1 --max-retries 5

# 중단된 번역 이어서 진행
./translate.sh "소설파일/" "번역결과/" --resume

# 도움말 보기
./translate.sh --help
```

### 5. 한글 EPUB 생성
```bash
# 기본 한글 EPUB 생성 (원본파일명-ko.epub)
./build.sh \"원본.epub\" \"번역결과/\"

# 출력 파일명 지정
./build.sh \"원본.epub\" \"번역결과/\" \"한글소설.epub\"

# 상세 출력으로 생성
./build.sh \"원본.epub\" \"번역결과/\" --verbose
```

### 6. 전체 워크플로우 (원클릭 번역)
```bash
# 영문 EPUB → 한글 EPUB 완전 자동화
./translate_to_korean.sh \"영문소설.epub\"

# 고급 옵션으로 번역
./translate_to_korean.sh \"novel.epub\" --genre sci-fi --model llama3:8b

# 임시 파일 보존 (디버깅용)
./translate_to_korean.sh \"novel.epub\" --keep-temp --verbose
```

## 📁 출력 구조

```
소설파일/                    # 추출 결과
├── info.json              # 📄 책 정보 (제목, 저자, 언어 등)
├── chapters/              # 📁 원본 챕터 파일들
│   ├── Chapter_001.txt
│   ├── Chapter_002.txt
│   └── ...
└── chunks/                # 📁 LLM 번역용 청크들
    ├── Chapter_001_part_01.txt
    ├── Chapter_001_part_02.txt
    ├── chunk_index.json   # 📋 청크 인덱스
    └── ...

번역결과/                    # 번역 결과
├── translated_chunks/     # 📁 번역된 청크 파일들
│   ├── ko_Chapter_001_part_01.txt
│   ├── ko_Chapter_001_part_02.txt
│   └── ...
├── translation_index.json     # 📋 번역 정보 및 통계
└── translation_progress.json  # 📊 번역 진행 상황

소설파일-ko.epub              # 📚 생성된 한글 EPUB 파일
```

## 🔧 CLI 옵션

### 추출 옵션
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--max-chunk-size N` | 최대 청크 크기 (문자 수) | 3000 |
| `--min-chunk-size N` | 최소 청크 크기 (문자 수) | 1000 |
| `--no-chunks` | 청크 파일 생성하지 않음 | false |
| `--output-dir DIR` | 출력 디렉토리 지정 | EPUB 파일명 |
| `--verbose, -v` | 상세한 출력 표시 | false |
| `--help, -h` | 도움말 표시 | - |

### 번역 옵션
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--model MODEL` | 사용할 Ollama 모델명 | llama3.1:8b |
| `--temperature N` | 번역 온도 (0.0-2.0) | 0.1 |
| `--max-retries N` | 재시도 횟수 | 3 |
| `--genre GENRE` | 소설 장르 | fantasy |
| `--resume` | 이전 번역 작업 이어서 진행 | false |
| `--verbose, -v` | 상세한 출력 표시 | false |
| `--help, -h` | 도움말 표시 | - |

### 빌드 옵션
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--output FILE, -o` | 출력 EPUB 파일 경로 | 원본파일명-ko.epub |
| `--verbose, -v` | 상세한 출력 표시 | false |
| `--help, -h` | 도움말 표시 | - |

### 통합 번역 옵션 (translate_to_korean.sh)
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--model MODEL` | 사용할 Ollama 모델명 | llama3.1:8b |
| `--genre GENRE` | 소설 장르 | fantasy |
| `--max-chunk-size N` | 최대 청크 크기 | 3000 |
| `--min-chunk-size N` | 최소 청크 크기 | 1000 |
| `--temperature N` | 번역 온도 (0.0-2.0) | 0.1 |
| `--output FILE` | 출력 EPUB 파일명 | 원본파일명-ko.epub |
| `--keep-temp` | 임시 파일들 보존 | false |
| `--resume` | 중단된 번역 이어서 진행 | false |
| `--verbose, -v` | 상세한 출력 표시 | false |
| `--help, -h` | 도움말 표시 | - |

## 🎯 번역 워크플로우

### 자동 워크플로우 (권장)
```bash
# 원클릭으로 영문 EPUB → 한글 EPUB 변환
./translate_to_korean.sh "영문소설.epub"
```

### 수동 워크플로우 (단계별 제어)

#### 1단계: EPUB 추출
```bash
./extract.sh "novel.epub"
```

#### 2단계: 책 정보 확인
```bash
cat novel/info.json
```

#### 3단계: 번역 실행
```bash
./translate.sh "novel/" "translated/"
```

#### 4단계: 한글 EPUB 생성
```bash
./build.sh "novel.epub" "translated/"
```

### API 사용 (프로그래밍)
```python
from epub_extractor import EPUBExtractor, OllamaTranslator, build_korean_epub

# 1. 추출
extractor = EPUBExtractor("novel.epub")
extractor.extract("extracted/")

# 2. 번역
translator = OllamaTranslator(genre="fantasy")
translator.translate_chunks("extracted/", "translated/")

# 3. 한글 EPUB 생성
korean_epub = build_korean_epub("novel.epub", "translated/")
```

## 🛠️ 기술적 특징

### 지능형 분할 알고리즘
1. **문단 우선**: 연속된 줄바꿈(`\n\n`)을 기준으로 문단 단위 분할
2. **문장 보완**: 문단이 너무 큰 경우 문장 단위(`.!?`)로 추가 분할
3. **단어 분할**: 최후 수단으로 단어 단위 분할 (문맥 보존 최우선)

### HTML 파싱 개선
- `<p>`, `<div>`, `<section>` 등을 문단으로 인식
- `<script>`, `<style>` 태그 내용 제외
- HTML 엔티티 자동 디코딩
- 원문의 문단 구조 최대한 보존

### 메타데이터 추출
- Dublin Core 표준 준수
- 제목, 저자, 언어, 출판사, 설명 등 자동 추출
- JSON 형태로 구조화된 정보 제공

## 📋 요구사항

- **Python**: 3.6 이상
- **의존성**: 표준 라이브러리만 사용 (추가 설치 불필요)
- **지원 형식**: EPUB 2.0/3.0 (ZIP 기반)

## 🗂️ 프로젝트 구조

```
novels/
├── epub_extractor/           # 📦 모듈형 패키지 (v2.0.0)
│   ├── __init__.py          # 패키지 초기화
│   ├── extractor.py         # EPUB 추출 엔진
│   ├── chunker.py           # 지능형 텍스트 분할기
│   ├── parser.py            # HTML → 텍스트 파서
│   ├── translator.py        # Ollama 번역기
│   ├── builder.py           # EPUB 재조립기
│   ├── prompts.py           # 장르별 번역 프롬프트
│   ├── utils.py             # 유틸리티 함수들
│   └── cli.py               # 명령줄 인터페이스
├── extract.sh               # 🔧 EPUB 추출 스크립트
├── translate.sh             # 🌏 번역 실행 스크립트
├── build.sh                 # 📚 EPUB 빌드 스크립트
├── translate_to_korean.sh   # 🎯 통합 번역 스크립트 (원클릭)
├── activate.sh              # 🐍 환경 설정 스크립트
├── requirements.txt         # 📋 Python 의존성
├── CLAUDE.md                # 🤖 Claude Code 작업 가이드
├── venv/                    # 📁 Python 가상환경
└── README.md                # 📖 사용 설명서
```

## 💡 팁

- **작은 청크**: 더 정확한 번역을 원한다면 `--max-chunk-size 2000` 사용
- **큰 청크**: 문맥을 더 보존하고 싶다면 `--max-chunk-size 4000` 사용
- **청크 없음**: 원본 텍스트만 필요하다면 `--no-chunks` 사용
- **파일명**: 특수문자가 포함된 EPUB 파일명은 따옴표로 감싸기