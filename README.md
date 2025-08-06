# 📚 EPUB 번역기 (EPUB Translator)

영어 EPUB 파일을 한국어로 자동 번역하는 도구입니다. Ollama를 사용하여 로컬에서 고품질 번역을 수행합니다.

## ✨ 주요 기능

### 📖 EPUB 처리
- **자동 추출**: EPUB 파일에서 텍스트 자동 추출
- **구조 보존**: 원본 챕터 구조와 메타데이터 완벽 보존
- **지능형 청킹**: LLM 번역에 최적화된 텍스트 분할
- **한글 EPUB 생성**: 번역된 텍스트로 새로운 EPUB 자동 생성

### 🤖 번역 기능
- **로컬 LLM**: Ollama를 통한 프라이버시 보호 번역
- **다양한 모델 지원**: `gpt-oss:20b` (기본값) 외 다양한 모델 사용 가능
- **장르별 최적화**: 판타지, SF, 로맨스 등 장르별 번역 스타일
- **진행 상황 추적**: 실시간 번역 진도 표시 및 중단/재개 지원
- **캐싱 시스템**: 번역 결과 캐싱으로 재번역 속도 향상

### 🛠️ 개발자 친화적
- **모듈식 구조**: 재사용 가능한 Python 패키지
- **CLI 인터페이스**: 간편한 명령줄 도구
- **배치 스크립트**: 원클릭 번역 자동화
- **상세한 로깅**: 디버깅을 위한 verbose 모드

## 🚀 빠른 시작

### 1. 설치
```bash
# Python 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Ollama 설치 (macOS/Linux)
curl -fsSL https://ollama.com/install.sh | sh

# 번역 모델 다운로드
ollama pull gpt-oss:20b
```

### 2. 원클릭 번역
```bash
# 영문 EPUB → 한글 EPUB 완전 자동화
./translation.sh full -f "영문소설.epub" -m gpt-oss:20b
```

### 3. 단계별 사용법
```bash
# 1단계: EPUB 텍스트 추출
./translation.sh extract -f "sample.epub"

# 2단계: 번역 실행
./translation.sh translate -i "sample/" -m gpt-oss:20b

# 3단계: 한글 EPUB 생성
./translation.sh combine -f "sample.epub" -i "sample/translated"
```

## 📁 프로젝트 구조

```
translator/
├── epub_extractor/          # 핵심 Python 패키지
│   ├── __init__.py         # 패키지 초기화
│   ├── cli.py              # CLI 인터페이스
│   ├── extractor.py        # EPUB 추출 엔진
│   ├── translator.py       # 번역 엔진
│   ├── chunker.py          # 텍스트 분할
│   ├── parser.py           # HTML 파싱
│   ├── builder.py          # EPUB 생성
│   ├── prompts.py          # 번역 프롬프트
│   └── utils.py            # 유틸리티 함수
├── config/                  # 설정 파일
│   └── config.py           # 기본 설정값
├── tests/                   # 테스트 코드
│   ├── unit/               # 단위 테스트
│   └── resources/          # 테스트 리소스
├── translated/              # 번역 결과물
├── translation.sh          # 통합 번역 스크립트
├── activate.sh             # 환경 설정 스크립트
├── rebuild.sh              # HTML 재구성 스크립트
├── requirements.txt        # Python 의존성
└── README.md               # 이 문서
```

## 🔧 상세 사용법

### 통합 번역 스크립트 (translation.sh)

새로운 통합 스크립트로 모든 번역 과정을 간편하게 수행할 수 있습니다.

#### 사용법
```bash
./translation.sh <command> [options]
```

#### Commands

**extract** - EPUB을 챕터와 청크로 추출
```bash
./translation.sh extract -f "novel.epub" [OPTIONS]

옵션:
  -f, --file <file>         EPUB 파일 경로 (필수)
  -o, --output-dir <dir>    출력 디렉토리
  --max-chunk-size <size>   최대 청크 크기 (기본값: 3000)
  --min-chunk-size <size>   최소 청크 크기 (기본값: 1000)
  --extract-only            청크 없이 원본 HTML만 추출
  --no-chunks               챕터 파일만 생성
  -v, --verbose             상세한 출력 표시
```

**translate** - 추출된 청크를 한글로 번역
```bash
./translation.sh translate -i "novel/" [OPTIONS]

옵션:
  -i, --input-dir <dir>     입력 디렉토리 (필수)
  -o, --output-dir <dir>    출력 디렉토리 (기본값: translated/)
  -m, --model <model>       사용할 Ollama 모델 (기본값: gpt-oss:20b)
  -g, --genre <genre>       소설 장르 (기본값: fantasy)
  --temperature <temp>      번역 온도 (기본값: 0.1)
  --max-retries <num>       최대 재시도 횟수 (기본값: 3)
  --resume                  이전 번역 작업 이어서 진행
  -v, --verbose             상세한 출력 표시
```

**combine** - 번역된 청크를 EPUB으로 통합
```bash
./translation.sh combine -f "novel.epub" -i "translated/" [OPTIONS]

옵션:
  -f, --original-file <file>    원본 EPUB 파일 (필수)
  -i, --input-dir <dir>         번역 디렉토리 (필수)
  -o, --output-file <file>      출력 EPUB 파일 (기본값: 원본-ko.epub)
  -v, --verbose                 상세한 출력 표시
```

**full** - 전체 워크플로우 (추출 → 번역 → 통합)
```bash
./translation.sh full -f "novel.epub" [OPTIONS]

옵션:
  -f, --file <file>             EPUB 파일 경로 (필수)
  -w, --work-dir <dir>          작업 디렉토리 (기본값: 파일명)
  -m, --model <model>           사용할 Ollama 모델 (기본값: gpt-oss:20b)
  -g, --genre <genre>           소설 장르 (기본값: fantasy)
  --max-chunk-size <size>       최대 청크 크기 (기본값: 3000)
  --temperature <temp>          번역 온도 (기본값: 0.1)
  -v, --verbose                 상세한 출력 표시
```

### Python CLI 직접 사용

기존 Python CLI도 여전히 사용 가능합니다:

```bash
# EPUB 텍스트 추출
python3 -m epub_extractor.cli extract "novel.epub" --max-chunk-size 2000

# 번역 실행
python3 -m epub_extractor.cli translate "novel/" "translated/" --model gpt-oss:20b

# 한글 EPUB 생성
python3 -m epub_extractor.cli build "novel.epub" "translated/" --output "novel-ko.epub"
```

### 설정 파일 (config/config.py)

```python
# 기본 모델 설정
DEFAULT_MODEL = "gpt-oss:20b"

# 번역 설정
DEFAULT_TEMPERATURE = 0.1      # 번역 창의성 (낮을수록 일관성 향상)
DEFAULT_MAX_RETRIES = 3         # 오류 시 재시도 횟수
DEFAULT_GENRE = "fantasy"       # 기본 장르

# 청크 크기 설정
DEFAULT_MAX_CHUNK_SIZE = 2000   # 최대 청크 크기
DEFAULT_MIN_CHUNK_SIZE = 1000   # 최소 청크 크기

# 캐싱 설정
DEFAULT_ENABLE_CACHE = True     # 번역 캐싱 활성화
```

### 환경 변수

`.env` 파일을 생성하여 설정 가능:
```bash
OLLAMA_MODEL=gpt-oss:20b
DEBUG=True
```

## 📊 번역 워크플로우

### 작업 디렉토리 구조
```
sample_translation_work/
├── chunks/                    # 원본 텍스트 청크
│   ├── chapter_01_part_01.txt
│   └── ...
├── translated_chunks/         # 번역된 텍스트
│   ├── ko_chapter_01_part_01.txt
│   └── ...
├── html_files/               # 원본 HTML 파일
├── index.json               # EPUB 구조 정보
└── translation_index.json   # 번역 진행 상태
```

### 번역 진행 상태 확인
```bash
# 진행 상태 보기
cat sample_translation_work/translation_index.json | python3 -m json.tool

# 번역된 파일 수 확인
ls sample_translation_work/translated_chunks/ | wc -l
```

## 🎯 사용 예제

### 기본 번역 (완전 자동화)
```bash
# 가장 간단한 사용법 - 한 번의 명령으로 모든 과정 수행
./translation.sh full -f "Harry Potter.epub"
```

### 고급 설정으로 번역
```bash
# SF 소설을 다른 모델로 번역
./translation.sh full -f "Dune.epub" \
  -m llama3:8b \
  -g sci-fi \
  --temperature 0.2
```

### 단계별 수동 실행
```bash
# 1단계: 추출
./translation.sh extract -f "LargeNovel.epub" --max-chunk-size 1000

# 2단계: 번역 (재개 기능 활용)
./translation.sh translate -i "LargeNovel/" \
  -m gpt-oss:20b \
  --max-retries 5 \
  --resume

# 3단계: 통합
./translation.sh combine -f "LargeNovel.epub" -i "LargeNovel/translated/"
```

### 배치 처리
```bash
# 여러 EPUB 파일 일괄 번역
for epub in *.epub; do
  ./translation.sh full -f "$epub" -m gpt-oss:20b -v
done
```

## 🐛 문제 해결

### Ollama 연결 실패
```bash
# Ollama 서비스 상태 확인
ollama list

# 서비스 재시작
ollama serve

# 모델 재다운로드
ollama pull gpt-oss:20b
```

### 메모리 부족
```bash
# 청크 크기 줄이기
./translation.sh extract -f "book.epub" --max-chunk-size 1000

# GPU 메모리 조절 (NVIDIA)
export OLLAMA_NUM_GPU_LAYERS=20
```

### 번역 품질 개선
- Temperature 낮추기: `./translation.sh translate -i novel/ --temperature 0.0`
- 장르 정확히 지정: `./translation.sh translate -i novel/ --genre fantasy`
- 더 큰 모델 사용: `./translation.sh translate -i novel/ --model gpt-oss:20b`

## 🧪 개발 및 테스트

### 테스트 실행
```bash
# 단위 테스트
make test

# 커버리지 리포트
make coverage

# 코드 린트
make lint

# 코드 포맷팅
make format
```

### 개발 환경 설정
```bash
# 개발 의존성 설치
pip install -r requirements-dev.txt

# pre-commit 훅 설치
pre-commit install
```

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

기여를 환영합니다! 다음 단계를 따라주세요:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 💡 팁과 트릭

### 성능 최적화
- **병렬 처리**: 여러 EPUB 파일 동시 번역 가능
- **재개 기능 활용**: `--resume` 옵션으로 중단된 번역 이어서 진행
- **청크 크기 조절**: 파일 크기에 맞게 청크 크기 최적화

### 번역 품질
- **장르 설정**: 정확한 장르 지정으로 번역 품질 향상 (`-g fantasy`)
- **Temperature 조절**: 0.0-0.3 범위 권장 (`--temperature 0.1`)
- **모델 선택**: 대용량 모델일수록 품질 향상 (`-m gpt-oss:20b`)

### 디버깅
- **Verbose 모드**: `-v` 또는 `--verbose`로 상세 로그 확인
- **임시 파일 보존**: 디버깅 시 작업 디렉토리 확인
- **단계별 실행**: 문제 구간 파악을 위한 extract/translate/combine 개별 실행
- **통합 스크립트**: 컬러 로그와 진행 상황 실시간 확인

## 📚 지원 형식

- **EPUB 2.0/3.0**: ZIP 기반 EPUB 파일
- **언어**: 영어 → 한국어 번역
- **장르**: 판타지, SF, 로맨스, 미스터리, 호러, 일반

## 🔗 관련 링크

- [Ollama 공식 사이트](https://ollama.com)
- [Python 패키징 가이드](https://packaging.python.org)
- [EPUB 3 스펙](https://www.w3.org/publishing/epub3/)

---

**문제가 있으시면 이슈를 등록해주세요!**