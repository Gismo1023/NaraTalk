import csv
import re
from pathlib import Path
from dotenv import load_dotenv

# db.py에서 필요한 함수 임포트
from src_db.db import get_connection, load_sql, initialize_database, get_sentences_grouped

load_dotenv()

def normalize_korean(text):
    """한국어 텍스트 전처리: 공백 통일 및 끝 문장부호(? ! .) 유지"""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def init_database_table():
    """db.py에 정의된 전체 초기화 함수(테이블 생성 + 시드 데이터 적재)를 호출합니다."""
    try:
        initialize_database()
        print("✨ 데이터베이스 테이블 생성 및 초기화 성공!")
    except Exception as e:
        print(f"⚠️ 테이블 초기화 중 오류 발생: {e}")


def preprocess_sentences(file_path="text.csv"):
    """CSV 파일을 안전하게 읽어와 카테고리별로 분류하고 전처리 적용"""
    desired_order = [
        "필수 기초 회화",
        "이동 및 길찾기",
        "숙박 및 기타",
        "가격 및 쇼핑",
        "식당 및 주문",
    ]

    ordered_db = {cat: [] for cat in desired_order}

    # 만약 CSV 파일이 없다면 DB에서 직접 그룹화된 데이터를 가져오는 대안도 고려할 수 있습니다.
    try:
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
    except FileNotFoundError:
        print(f"⚠️ '{file_path}' 파일을 찾지 못해 DB에서 데이터를 불러옵니다.")
        ordered_db = get_sentences_grouped()

    return ordered_db


# 전역에서 바로 가져다 쓸 수 있는 SENTENCES_DB 정의
SENTENCES_DB = preprocess_sentences("text.csv")


# 단독 테스트용 실행부
if __name__ == "__main__":
    print("=== 데이터베이스 테이블 초기화 시도 ===")
    init_database_table()

    print("\n=== 정규화 및 순서 고정이 완료된 SENTENCES_DB ===")
    print(SENTENCES_DB)