# TTS CSV를 이용해 그래프 추출
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 폰트 깨짐 방지 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


def main():
    # 현재 폴더(tts/tts_test/) 내의 CSV 파일 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "tts_evaluation_results.csv")

    if not os.path.exists(csv_path):
        print(f"⚠️ '{csv_path}' 파일을 찾을 수 없습니다. 먼저 tts_evaluation_results.py를 실행해주세요.")
        return

    print(f"CSV 데이터 로드 중: {csv_path}")
    df = pd.read_csv(csv_path)

    df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)

    # 대시보드 레이아웃 설정 (GridSpec 2행 구조)
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.0])

    fig.suptitle("TTS 음성 평가 결과 대시보드", fontsize=18, fontweight='bold', y=0.98)

    # [상단] 파일별 발음 평가 점수
    ax1 = fig.add_subplot(gs[0, :])
    df_sorted = df.sort_values(by="file_name")

    sns.barplot(
        data=df_sorted,
        x="file_name",
        y="score",
        palette="Blues_r",
        ax=ax1
    )
    ax1.set_title("TTS 파일별 발음 평가 점수 (전체)", fontsize=13, fontweight='bold')
    ax1.set_xlabel("오디오 파일명", fontsize=11)
    ax1.set_ylabel("점수 (Score)", fontsize=11)
    ax1.set_ylim(0, 110)
    ax1.tick_params(axis='x', rotation=60, labelsize=8)

    for p in ax1.patches:
        height = p.get_height()
        if height > 0:
            ax1.annotate(f"{height:.1f}",
                         (p.get_x() + p.get_width() / 2., height),
                         ha='center', va='bottom', fontsize=7.5, xytext=(0, 2),
                         textcoords='offset points')

    # [하단 좌측] 난이도별 평균 점수
    ax2 = fig.add_subplot(gs[1, 0])
    df_level = df[df["assigned_level"] != "미정"]
    level_df = df_level.groupby("assigned_level")["score"].mean().reset_index()

    sns.barplot(
        data=level_df,
        x="assigned_level",
        y="score",
        order=["쉬움", "보통", "어려움"],
        palette="viridis",
        ax=ax2
    )
    ax2.set_title("난이도별 평균 점수", fontsize=13, fontweight='bold')
    ax2.set_xlabel("난이도", fontsize=11)
    ax2.set_ylabel("평균 점수", fontsize=11)
    ax2.set_ylim(0, 110)

    for p in ax2.patches:
        height = p.get_height()
        if height > 0:
            ax2.annotate(f"{height:.1f}점",
                         (p.get_x() + p.get_width() / 2., height),
                         ha='center', va='bottom', fontsize=10, xytext=(0, 3),
                         textcoords='offset points')

    # [하단 우측] 전체 평균 오류율 도넛 차트
    ax3 = fig.add_subplot(gs[1, 1])
    mean_cer = df["cer_raw"].mean() * 100
    mean_wer = df["wer_raw"].mean() * 100

    sizes = [mean_cer, mean_wer]
    labels = [f'CER (음절 오류율: {mean_cer:.1f}%)', f'WER (어절 오류율: {mean_wer:.1f}%)']
    colors = ['#ff9999', '#ffcc99']

    ax3.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        wedgeprops=dict(width=0.4, edgecolor='w')
    )
    ax3.set_title("전체 평균 오류율 (CER / WER)", fontsize=13, fontweight='bold')

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # 이미지 파일 저장 (현재 폴더인 tts/tts_test/ 내부에 저장)
    output_img = os.path.join(current_dir, "tts_evaluation_dashboard.png")
    plt.savefig(output_img, dpi=300)
    print(f"TTS 시각화 완료! 이미지 저장 경로: {os.path.abspath(output_img)}")

    plt.show()


if __name__ == "__main__":
    main()