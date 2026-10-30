# export_whisper_validation.py

import pandas as pd
import re
from src.db import get_connection


# 전처리 함수
def clean_for_evaluation(text: str) -> str:
    if not text:
        return ""
    cleaned = text.lower()
    cleaned = re.sub(r'[^가-힣a-z0-9\s]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


# 두 문자열 간의 문자 오류율(CER)을 계산하는 함수
def calculate_cer(reference: str, hypothesis: str) -> float:
    ref = clean_for_evaluation(reference)
    hyp = clean_for_evaluation(hypothesis)

    if not ref:
        return 0.0 if not hyp else 1.0

    d = [[0] * (len(hyp) + 1) for _ in range(len(ref) + 1)]
    for i in range(len(ref) + 1):
        d[i][0] = i
    for j in range(len(hyp) + 1):
        d[0][j] = j

    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            if ref[i - 1] == hyp[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(
                    d[i - 1][j] + 1,  # Deletion
                    d[i][j - 1] + 1,  # Insertion
                    d[i - 1][j - 1] + 1  # Substitution
                )
    return round(d[len(ref)][len(hyp)] / len(ref), 4)

# 실제 DB의 연습 기록을 조회
def export_whisper_validation_to_csv(output_filename="whisper_cer_comparison_results.csv"):

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        r.id,
                        u.nickname,
                        s.ko AS reference,
                        r.transcript,
                        r.cer AS db_saved_cer,
                        r.score,
                        r.created_at
                    FROM practice_runs r
                    JOIN users u ON r.user_id = u.id
                    JOIN sentences s ON r.sentence_id = s.id
                    WHERE r.transcript IS NOT NULL AND r.transcript != ''
                    ORDER BY r.created_at DESC
                """)
                rows = cursor.fetchall()

        if not rows:
            print("DB에 연동할 연습 기록 데이터가 없습니다.")
            return None

        df = pd.DataFrame(rows)

        # 1. 정답 문장과 모델 인식 텍스트 양쪽에 모두 전처리 적용
        df["정답문장_Cleaned"] = df["reference"].apply(clean_for_evaluation)
        df["전처리후_Cleaned"] = df["transcript"].apply(clean_for_evaluation)

        # 2. 전처리 전 CER (%) (DB에 저장된 원본 기준 또는 원본 간 계산값)
        df["전처리전_CER (%)"] = (df["db_saved_cer"].astype(float) * 100).round(1)

        # 3. 전처리 후 CER 계산 (전처리된 정답 vs 전처리된 인식 텍스트 비교)
        df["전처리후_CER_계산값"] = df.apply(
            lambda row: calculate_cer(row["정답문장_Cleaned"], row["전처리후_Cleaned"]), axis=1
        )
        df["전처리후_CER (%)"] = (df["전처리후_CER_계산값"] * 100).round(1)

        # 4. CER 개선율(감소폭) 산출
        df["CER_개선율(p)"] = (df["전처리전_CER (%)"] - df["전처리후_CER (%)"]).round(1)

        # 5. 발표 및 검증용 표준 컬럼 구조로 매핑
        df_export = pd.DataFrame({
            "고유ID(run_id)": df["id"],
            "사용자": df["nickname"],
            "연습일시": df["created_at"],
            "정답문장(Reference_Raw)": df["reference"],
            "정답문장전처리(Reference_Cleaned)": df["정답문장_Cleaned"],
            "전처리전텍스트(Raw)": df["transcript"],
            "전처리후텍스트(Cleaned)": df["전처리후_Cleaned"],
            "전처리 전 CER (%)": df["전처리전_CER (%)"].astype(str) + "%",
            "전처리 후 CER (%)": df["전처리후_CER (%)"].astype(str) + "%",
            "개선 효과 (CER 감소폭)": df["CER_개선율(p)"].astype(str) + "%p 감소",
            "발음평가점수": df["score"]
        })

        # CSV 파일 저장
        df_export.to_csv(output_filename, index=False, encoding="utf-8-sig")
        print(f"정답 문장 전처리가 반영된 CER 비교 CSV 산출 완료: {output_filename}")
        return output_filename

    except Exception as e:
        print(f"CSV 산출 중 오류가 발생했습니다: {e}")
        return None


if __name__ == "__main__":
    export_whisper_validation_to_csv()