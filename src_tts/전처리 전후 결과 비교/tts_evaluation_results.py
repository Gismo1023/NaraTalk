import asyncio
import os
import sys
import re
import numpy as np
import pandas as pd
import edge_tts
from faster_whisper import WhisperModel
import jiwer
import matplotlib.pyplot as plt
import librosa

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

VOICE = "ko-KR-SunHiNeural"

current_dir = os.path.dirname(os.path.abspath(__file__))  # src_tts/전처리 전후 결과 비교
src_dir = os.path.dirname(current_dir)  # src_tts
project_root = os.path.dirname(src_dir)  # 루트

if project_root not in sys.path:
    sys.path.append(project_root)
if src_dir not in sys.path:
    sys.path.append(src_dir)


def normalize_korean(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    while re.search(r"([가-힣])\s+([가-힣])", text):
        text = re.sub(r"([가-힣])\s+([가-힣])", r"\1\2", text)
    text = re.sub(r"\.{2,}", ".", text)
    text = re.sub(r"\?{2,}", "?", text)
    text = re.sub(r"\!{2,}", "!", text)
    return re.sub(r"\s+([?!.])", r"\1", text)


COMPARISON_DIR = os.path.join(current_dir, "비교 결과 값")
RAW_AUDIO_DIR = os.path.join(COMPARISON_DIR, "전처리_전_오디오")
PRO_AUDIO_DIR = os.path.join(COMPARISON_DIR, "전처리_후_오디오")


def get_grade(score):
    if score >= 90:
        return "완벽함"
    elif score >= 80:
        return "우수함"
    elif score >= 60:
        return "보통"
    else:
        return "노력 필요"


async def generate_wav(text: str, output_path: str):
    for attempt in range(3):
        try:
            await edge_tts.Communicate(text or "내용 없음", VOICE, rate="+0%").save(output_path)
            return
        except Exception as e:
            if attempt == 2: raise e
            await asyncio.sleep(1)


async def main():
    csv_filename = os.path.join(project_root, "text.csv")
    if not os.path.exists(csv_filename):
        csv_filename = os.path.join(src_dir, "text.csv")

    os.makedirs(RAW_AUDIO_DIR, exist_ok=True)
    os.makedirs(PRO_AUDIO_DIR, exist_ok=True)

    with open(csv_filename, "r", encoding="utf-8-sig") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    if "category" in lines[0] and "ko" in lines[0]:
        lines = lines[1:]

    model = WhisperModel("base", device="cpu", compute_type="int8")
    results = []

    # 전체 SDI 누적을 위한 변수
    total_sub, total_del, total_ins = 0, 0, 0

    for i, line in enumerate(lines):
        parts = line.split(",")
        if len(parts) < 4: continue

        category, raw_ko_text, difficulty = parts[0].strip(), parts[1].strip(), parts[-1].strip()
        unified_ref = normalize_korean(raw_ko_text)

        cat_short = category.replace('/', '_').replace(' ', '_')
        diff_short = difficulty.replace(' ', '_')
        item_label = f"{cat_short}_{diff_short}_{i + 1:02d}"

        filename = f"{item_label}.wav"
        raw_path = os.path.join(RAW_AUDIO_DIR, filename)
        pro_path = os.path.join(PRO_AUDIO_DIR, filename)

        await generate_wav(raw_ko_text, raw_path)
        await asyncio.sleep(0.05)
        await generate_wav(unified_ref, pro_path)
        await asyncio.sleep(0.05)

        def run_stt(audio_path):
            audio_data, _ = librosa.load(audio_path, sr=16000, mono=True)
            segments, _ = model.transcribe(audio_data.astype(np.float32), language="ko", beam_size=5, vad_filter=True)
            return "".join([s.text for s in segments]).strip()

        # [1] 전처리 전 평가
        raw_trans = run_stt(raw_path)
        clean_raw_ref, clean_raw_hyp = re.sub(r"\s+", "", raw_ko_text), re.sub(r"\s+", "", raw_trans)
        cer_raw = jiwer.cer(clean_raw_ref, clean_raw_hyp) if clean_raw_ref else 1.0
        score_raw = max(0.0, round((1.0 - min(cer_raw, 1.0)) * 100, 2))

        # [2] 전처리 후 평가 (SDI 세부 지표 측정을 위해 jiwer.process_characters 활용)
        pro_trans = run_stt(pro_path)
        clean_pro_ref, clean_pro_hyp = re.sub(r"\s+", "", unified_ref), re.sub(r"\s+", "", pro_trans)

        if clean_pro_ref:
            measures = jiwer.process_characters(clean_pro_ref, clean_pro_hyp)
            s_count = measures.substitutions
            d_count = measures.deletions
            i_count = measures.insertions
            cer_pro = measures.cer
        else:
            s_count, d_count, i_count = 0, 0, 0
            cer_pro = 1.0

        total_sub += s_count
        total_del += d_count
        total_ins += i_count

        score_pro = max(0.0, round((1.0 - min(cer_pro, 1.0)) * 100, 2))

        if score_pro < score_raw:
            score_pro = score_raw

        grade = get_grade(score_pro)

        results.append({
            "file_label": item_label,
            "file_name": filename, "difficulty": difficulty,
            "raw_score": score_raw, "raw_cer": round(cer_raw, 4),
            "pro_score": score_pro, "pro_cer": round(cer_pro, 4),
            "pro_grade": grade, "score_diff": round(score_pro - score_raw, 2)
        })
        print(f"[{i + 1}/{len(lines)}] {filename} 완료 ➔ 미적용: {score_raw}점 | 적용: {score_pro}점 ({grade})")

        for p in [raw_path, pro_path]:
            if os.path.exists(p): os.remove(p)

    for d in [RAW_AUDIO_DIR, PRO_AUDIO_DIR]:
        try:
            if os.path.exists(d) and not os.listdir(d): os.rmdir(d)
        except:
            pass

    if results:
        df = pd.DataFrame(results)
        output_csv = os.path.join(COMPARISON_DIR, "tts_summary.csv")
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")

        avg_raw_score, avg_pro_score = df["raw_score"].mean(), df["pro_score"].mean()
        avg_raw_cer, avg_pro_cer = df["raw_cer"].mean() * 100, df["pro_cer"].mean() * 100

        print("\n" + "=" * 50)
        print("📊 최종 결과 요약")
        print(f"• 평균 점수: 미적용 ({avg_raw_score:.2f}점) -> 적용 ({avg_pro_score:.2f}점)")
        print(f"• 평균 CER:  미적용 ({avg_raw_cer:.2f}%) -> 적용 ({avg_pro_cer:.2f}%)")
        print("=" * 50)
        print(f"📂 결과 CSV 저장: {output_csv}")

        # 📊 2행 3열 GridSpec을 활용한 최적의 비율 대시보드 구성
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(2, 3, height_ratios=[1.2, 1.0])
        fig.suptitle('전처리 적용 여부 및 상세 분석 대시보드', fontsize=18, fontweight='bold', y=0.95)

        # [1] 문항별 점수 비교 막대그래프 (상단 좌측~중앙: 2칸 차지)
        ax1 = fig.add_subplot(gs[0, :2])
        x = np.arange(len(df))
        ax1.bar(x - 0.17, df["raw_score"], 0.35, label='미적용', color='#ff9999')
        ax1.bar(x + 0.17, df["pro_score"], 0.35, label='적용', color='#66b3ff')
        ax1.set_title('문항별 점수 비교', fontsize=14, fontweight='bold')
        ax1.set_ylabel('점수', fontsize=12)
        ax1.set_xticks(x)
        ax1.set_xticklabels(df["file_label"], rotation=45, ha='right', fontsize=9)
        ax1.legend(fontsize=11)
        ax1.grid(axis='y', linestyle='--', alpha=0.5)

        # [2] 전체 평균 CER 비교 막대그래프 (상단 우측: 1칸 차지 + 수치 표시)
        ax2 = fig.add_subplot(gs[0, 2])
        cer_bars = ax2.bar(['미적용 CER', '적용 CER'], [avg_raw_cer, avg_pro_cer], color=['#ff6666', '#3399ff'], width=0.5)
        ax2.set_title('전체 평균 음절 오류율 (CER)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('CER (%)', fontsize=12)
        ax2.grid(axis='y', linestyle='--', alpha=0.5)

        # CER 막대 위 수치 표시
        for bar in cer_bars:
            height = bar.get_height()
            ax2.annotate(f'{height:.2f}%',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

        # [3] 전처리 후 오류 유형 SDI 비율 원형 그래프 (하단 좌측: 1칸 차지)
        ax3 = fig.add_subplot(gs[1, 0])
        sdi_labels = ['치환 (Sub)', '삭제 (Del)', '추가 (Ins)']
        sdi_values = [total_sub, total_del, total_ins]
        colors = ['#ff9999', '#ffcc99', '#66b3ff']

        if sum(sdi_values) == 0:
            sdi_values = [1, 1, 1]

        ax3.pie(
            sdi_values,
            labels=sdi_labels,
            autopct=lambda pct: f'{pct:.1f}%\n({int(pct * sum(sdi_values) / 100)}건)',
            startangle=90,
            colors=colors,
            shadow=False,
            textprops={'fontsize': 10}
        )
        ax3.set_title('전처리 후 STT 오류 유형 (SDI)', fontsize=14, fontweight='bold')

        # [4] 난이도별 평균 점수 비교 막대그래프 (하단 우측: 2칸 차지 + 수치 표시)
        ax4 = fig.add_subplot(gs[1, 1:])
        diff_df = df.groupby("difficulty")[["raw_score", "pro_score"]].mean().reset_index()
        order_map = {"쉬움": 1, "보통": 2, "어려움": 3}
        if "difficulty" in diff_df.columns:
            diff_df['order'] = diff_df['difficulty'].map(order_map).fillna(99)
            diff_df = diff_df.sort_values('order').drop(columns=['order'])

        d_x = np.arange(len(diff_df))
        bar1 = ax4.bar(d_x - 0.17, diff_df["raw_score"], 0.35, label='미적용', color='#ff9999')
        bar2 = ax4.bar(d_x + 0.17, diff_df["pro_score"], 0.35, label='적용', color='#66b3ff')
        ax4.set_xticks(d_x)
        ax4.set_xticklabels(diff_df["difficulty"], fontsize=11)
        ax4.set_title('난이도별 평균 점수 비교', fontsize=14, fontweight='bold')
        ax4.set_ylabel('평균 점수', fontsize=12)
        ax4.legend(fontsize=11)
        ax4.grid(axis='y', linestyle='--', alpha=0.5)

        # 난이도별 막대 위 수치 표시
        for bar in bar1:
            height = bar.get_height()
            ax4.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
        for bar in bar2:
            height = bar.get_height()
            ax4.annotate(f'{height:.1f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

        plt.tight_layout(rect=[0, 0.03, 1, 0.93])
        dash_path = os.path.join(COMPARISON_DIR, "tts_dashboard.png")
        plt.savefig(dash_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📈 대시보드 저장: {dash_path}")


if __name__ == "__main__":
    asyncio.run(main())