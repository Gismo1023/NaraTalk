# 📝 `normalize.py` 모듈 구조 및 기능 정의서

본 문서는 **나랏말싸미(AI 한국어 발음 교정 서비스)** 프로젝트에서 문장 데이터를 안전하게 로드하고 정규화하는 `normalize.py` 모듈의 구조와 주요 기능을 정의합니다.

---

## 1. 모듈 개요
- **주요 역할**: `text.csv` 파일로부터 데이터를 안전하게 읽어와 쉼표 깨짐 현상을 방지하고, 지정된 카테고리 순서대로 데이터를 재구성한 뒤 한국어 텍스트 정규화를 자동으로 적용합니다.
- **연동 파일**: `text.csv`

---

## 2. 주요 함수 설명

### ① `normalize_korean(text: str) -> str`
- **목적**: 한국어 텍스트 전처리 수행
- **세부 규칙**:
  - 탭, 줄바꿈, 연속된 띄어쓰기 등 불필요한 공백을 단일 공백(`" "`)으로 통일합니다.
  - 문자열 양 끝의 공백을 제거합니다(`strip()`).
  - 음성 톤과 문장 형태 보존을 위해 마침표(`.`), 물음표(`?`), 느낌표(`!`) 등의 문장 부호는 유지합니다.

### ② `load_and_preprocess_sentences(file_path: str) -> dict`
- **목적**: CSV 파일 로드 및 정렬·전처리 일괄 처리
- **세부 동작**:
  1. **카테고리 순서 고정**: 아래 5가지 카테고리 순서(`desired_order`)를 뼈대로 삼아 딕셔너리를 초기화합니다.
     - `필수 기초 회화`
     - `이동 및 길찾기`
     - `숙박 및 기타`
     - `가격 및 쇼핑`
     - `식당 및 주문`
  2. **안전한 CSV 파싱**: 큰따옴표(`" "`)로 감싸진 쉼표 포함 문장들을 오류 없이 안전하게 읽어옵니다.
  3. **자동 정규화 적용**: 각 항목의 한국어(`ko`) 텍스트에 `normalize_korean`을 즉시 적용하여 최종 `SENTENCES_DB`를 빌드합니다.

---

## 3. 소스코드 구현

```python
import csv
import re
import pprint


def normalize_korean(text: str) -> str:
    """한국어 텍스트 전처리: 공백 통일 및 끝 문장부호(? ! .) 유지"""
    if not text:
        return ""

    # 연속된 공백(탭, 여러 칸 띄어쓰기 등)을 하나의 공백으로 통일
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def preprocess_sentences(file_path: str = "text.csv") -> dict:
    """
    1. 지정한 순서대로 카테고리를 고정하고 CSV를 안전하게 읽어옴
    2. 한국어(ko) 텍스트에 normalize_korean 전처리 적용
    """
    desired_order = [
        "필수 기초 회화",
        "이동 및 길찾기",
        "숙박 및 기타",
        "가격 및 쇼핑",
        "식당 및 주문"
    ]

    ordered_db = {cat: [] for cat in desired_order}

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row["category"]
            item = {
                "ko": normalize_korean(row["ko"]),  # 한국어 정규화 적용
                "en": row["en"],                      # 영어 원본 유지
                "difficulty": row["difficulty"]       # 난이도 유지
            }
            if category in ordered_db:
                ordered_db[category].append(item)

    return ordered_db


# 전역에서 바로 가져다 쓸 수 있는 SENTENCES_DB 정의
SENTENCES_DB = preprocess_sentences("text.csv")


# 단독 테스트용 실행부
if __name__ == "__main__":
    print("=== 정규화 및 순서 고정이 완료된 SENTENCES_DB ===")
    pprint.pprint(SENTENCES_DB)