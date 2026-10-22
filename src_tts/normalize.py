import csv
import re
import pprint


def normalize_korean(text):
    """한국어 텍스트 전처리: 공백 통일 및 끝 문장부호(? ! .) 유지"""
    if not text:
        return ""

    # 연속된 공백(탭, 여러 칸 띄어쓰기 등)을 하나의 공백으로 통일
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def preprocess_sentences(file_path = "text.csv"):
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