# wer/cer 계산 결과를 수작업 검증 예제 10건 이상관 비교
from pathlib import Path
from faster_whisper import WhisperModel
import jiwer
import pandas as pd
import librosa
import re

# 1. Faster-Whisper 모델 로드
model_size = "small"
model = WhisperModel(model_size, device="cpu", compute_type="int8")

# 2. test_audio 디렉토리 설정
audio_dir = Path("test_audio")


# 3. 텍스트 정규화 함수 정의
def normalize_text(text: str) -> str:
    text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ==========================================
# 📐 [수동 방식] Levenshtein 거리 기반 직접 구현 함수
# ==========================================
def compute_edit_distance(seq1, seq2):
    if len(seq1) == 0:
        return len(seq2)
    if len(seq2) == 0:
        return len(seq1)

    matrix = [[0 for _ in range(len(seq2) + 1)] for _ in range(len(seq1) + 1)]

    for i in range(len(seq1) + 1):
        matrix[i][0] = i
    for j in range(len(seq2) + 1):
        matrix[0][j] = j

    for i in range(1, len(seq1) + 1):
        for j in range(1, len(seq2) + 1):
            if seq1[i - 1] == seq2[j - 1]:
                cost = 0
            else:
                cost = 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,  # Deletion
                matrix[i][j - 1] + 1,  # Insertion
                matrix[i - 1][j - 1] + cost  # Substitution
            )
    return matrix[len(seq1)][len(seq2)]


def manual_wer(ref: str, hyp: str) -> float:
    ref_words = ref.split()
    hyp_words = hyp.split()
    if len(ref_words) == 0:
        return 0.0 if len(hyp_words) == 0 else 1.0
    dist = compute_edit_distance(ref_words, hyp_words)
    return dist / len(ref_words)


def manual_cer(ref: str, hyp: str) -> float:
    ref_chars = list(ref.replace(" ", ""))
    hyp_chars = list(hyp.replace(" ", ""))
    if len(ref_chars) == 0:
        return 0.0 if len(hyp_chars) == 0 else 1.0
    dist = compute_edit_distance(ref_chars, hyp_chars)
    return dist / len(ref_chars)


# ==========================================

references = []
hypotheses = []
results_data = []

# 4. 디렉토리 내 모든 wav 오디오 파일 순회
for audio_path in sorted(audio_dir.glob("*.wav")):
    file_name = audio_path.name

    # 📌 파일 하나씩 평가할 때마다 진행 중 표시
    print(f"[평가 중...] {file_name}")

    # 1) 확장자 제거
    stem_text = audio_path.name
    while Path(stem_text).suffix:
        stem_text = Path(stem_text).stem

    # 2) 첫 번째 공백 기준 국가명 분리 후 뒤 문장만 정답(ref)으로 지정
    parts = stem_text.split(" ", 1)
    ref_raw = parts[1] if len(parts) > 1 else stem_text
    ref_text = normalize_text(ref_raw)

    # Faster-Whisper STT 수행
    try:
        audio_array, sr = librosa.load(str(audio_path), sr=16000, mono=True)
        segments, info = model.transcribe(
            audio_array,
            language="ko",
            beam_size=5,
            without_timestamps=True
        )
        hyp_raw = " ".join([segment.text for segment in segments]).strip()
        hyp_text = normalize_text(hyp_raw)
    except Exception:
        continue

    # [비교 평가]
    try:
        auto_w = jiwer.wer(ref_text, hyp_text)
        auto_c = jiwer.cer(ref_text, hyp_text)
    except Exception:
        auto_w, auto_c = 0.0, 0.0

    man_w = manual_wer(ref_text, hyp_text)
    man_c = manual_cer(ref_text, hyp_text)

    wer_diff = abs(auto_w - man_w)
    cer_diff = abs(auto_c - man_c)

    references.append(ref_text)
    hypotheses.append(hyp_text)

    results_data.append({
        "filename": file_name,
        "ref": ref_text,
        "hyp": hyp_text,
        "auto_wer": f"{auto_w:.2f}",
        "manual_wer": f"{man_w:.2f}",
        "wer_diff": f"{wer_diff:.2f}",
        "auto_cer": f"{auto_c:.2f}",
        "manual_cer": f"{man_c:.2f}",
        "cer_diff": f"{cer_diff:.2f}"
    })

# 5. Pandas DataFrame 변환 및 파일명을 인덱스로 지정하여 CSV 저장
if results_data:
    df = pd.DataFrame(results_data)
    df = df.set_index("filename")

    csv_path = "result.csv"
    df.to_csv(csv_path, encoding="utf-8-sig")

# 6. 전체 데이터셋 평균 WER 및 CER 계산 및 출력
if references and hypotheses:
    overall_auto_wer = jiwer.wer(references, hypotheses)
    overall_auto_cer = jiwer.cer(references, hypotheses)

    print(f"\n[최종 평가 완료 (총 {len(references)}개 파일)]")
    print(f"Overall Auto WER: {overall_auto_wer:.2f}")
    print(f"Overall Auto CER: {overall_auto_cer:.2f}")
else:
    print("\n[최종 평가 완료] 평가할 수 있는 유효한 오디오 파일이 없습니다.")