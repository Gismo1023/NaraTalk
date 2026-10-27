import csv
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def normalize_korean(text):
    """
    한국어 텍스트 전처리 고도화:
    - 글자 사이에 들어간 비정상적인 불필요한 공백 제거 (예: '안  녕' -> '안녕')
    - 반복되는 지저분한 문장부호(?, !, .)를 단일 부호로 정제
    """
    if not text:
        return ""

    # 1. 2칸 이상의 연속된 공백을 단일 공백으로 치환
    text = re.sub(r"\s+", " ", text).strip()

    # 2. 글자 사이에 찢어진 공백을 자연스러운 단어 형태로 복원
    while re.search(r"([가-힣])\s+([가-힣])", text):
        text = re.sub(r"([가-힣])\s+([가-힣])", r"\1\2", text)

    # 3. 반복되는 문장부호 압축 및 정리 (예: '! ! !' -> '!')
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\?{2,}", "?", text)
    text = re.sub(r"\!{2,}", "!", text)

    # 4. 문장부호 앞에 불필요하게 붙은 공백 제거 (예: "안녕하세요 !" -> "안녕하세요!")
    text = re.sub(r"\s+([?!.])", r"\1", text)

    return text


def preprocess_sentences(file_path="text.csv"):

    desired_order = [
        "필수 기초 회화",
        "이동 및 길찾기",
        "숙박 및 기타",
        "가격 및 쇼핑",
        "식당 및 주문",
    ]

    ordered_db = {cat: [] for cat in desired_order}

    # 파일 경로가 상대 경로일 때 상위 디렉토리(루트)의 text.csv도 탐색할 수 있도록 보완
    path_obj = Path(file_path)
    if not path_obj.exists():
        parent_path = Path(__file__).resolve().parent.parent / "text.csv"
        if parent_path.exists():
            file_path = parent_path

    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:  # utf-8-sig로 BOM 문제 예방
            reader = csv.DictReader(f)
            for row in reader:
                category = row.get("category", "").strip()
                ko_text = row.get("ko", "").strip()

                item = {
                    "ko": normalize_korean(ko_text),  # 한국어 정규화 적용
                    "en": row.get("en", "").strip(),  # 영어 원본 유지
                    "difficulty": row.get("difficulty", "").strip()  # 난이도 유지
                }
                if category in ordered_db:
                    ordered_db[category].append(item)
    except FileNotFoundError:
        print(f"⚠️ '{file_path}' 파일을 찾지 못했습니다.")

    return ordered_db


# 전역에서 바로 가져다 쓸 수 있는 SENTENCES_DB 정의
SENTENCES_DB = preprocess_sentences("text.csv")

# 단독 테스트용 실행부
if __name__ == "__main__":
    print("\n=== 정규화 및 순서 고정이 완료된 SENTENCES_DB 테스트 ===")
    for cat, items in SENTENCES_DB.items():
        print(f"\n[{cat}] (총 {len(items)}개 문장)")
        for item in items[:2]:  # 테스트로 카테고리당 앞 2개씩만 출력
            print(f"  - ko: {item['ko']} / en: {item['en']}")