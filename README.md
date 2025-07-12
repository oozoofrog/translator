# EPUB 파일 추출기

EPUB 파일의 내용을 챕터별로 개별 텍스트 파일로 분리하는 Python 스크립트입니다.

## 기능

- EPUB 파일의 목차 구조 분석
- 챕터별로 내용을 개별 `.txt` 파일로 분리
- HTML 태그 제거 및 순수 텍스트 추출
- 자동 챕터명 생성

## 설치

### 1. 가상환경 활성화
```bash
./activate.sh
```

### 2. 의존성 확인 (선택사항)
```bash
pip install -r requirements.txt
```
*이 프로젝트는 표준 라이브러리만 사용하므로 추가 설치가 필요하지 않습니다.*

## 사용법

### EPUB 파일 추출
```bash
./extract.sh "파일명.epub"
```

예시:
```bash
./extract.sh "내가_좋아하는_소설.epub"
```

## 출력

- 입력 파일명과 동일한 이름의 디렉토리 생성
- 각 챕터는 `챕터명.txt` 형태로 저장
- 목차 순서대로 파일 생성

## 파일 구조

```
novels/
├── epub_extractor.py    # 메인 추출 스크립트
├── extract.sh          # 실행 스크립트
├── activate.sh         # 가상환경 활성화 스크립트
├── venv/               # Python 가상환경
└── README.md           # 사용 설명서
```

## 요구사항

- Python 3.6 이상
- 표준 라이브러리만 사용 (추가 설치 불필요)

## 지원 형식

- 표준 EPUB 2.0/3.0 파일
- ZIP 기반 EPUB 구조