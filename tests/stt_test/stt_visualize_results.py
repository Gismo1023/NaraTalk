# stt_evaluation_result.csv로 그래프 추출
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 한글 폰트 깨짐 방지 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


def main():
    # 1. CSV 파일 경로 설정 (현재 스크립트가 위치한 stt/stt_test/ 폴더 기준)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "stt_evaluation_result.csv")

    if not os.path.exists(csv_path):
        print(f"⚠️ '{csv_path}' 파일을 찾을 수 없습니다. 먼저 stt_test_evaluation.py를 실행하여 CSV를 생성해주세요.")
        return

    print(f"CSV 데이터 로드 중: {csv_path}")
    df = pd.read_csv(csv_path)

    # 점수가 비어있는 경우 0점으로 채우기
    df['score'] = pd.to_numeric(df['score'], errors='coerce').fillna(0)

    # 2. 대시보드 레이아웃 설정 (1행 3열)
    fig = plt.figure(figsize=(16, 6))

    # 상단 타이틀 추가 (y 위치 조절)
    fig.suptitle("STT 발음 평가 결과 대시보드", fontsize=16, fontweight='bold', y=0.95)

    # -------------------------------------------------------------------------
    # [그래프 1] 파일별 발음 평가 점수 (전체 10건 출력)
    # -------------------------------------------------------------------------
    ax1 = fig.add_subplot(1, 3, 1)

    all_files = [
        "test_audio_04.wav", "test_audio_08.wav", "test_audio_09.wav",
        "test_audio_13.wav", "test_audio_16.wav", "test_audio_18.wav",
        "test_audio_21.wav", "test_audio_23.wav", "test_audio_30.wav", "test_audio_31.wav"
    ]

    df_full = pd.DataFrame({"file_name": all_files})
    df_merged = pd.merge(df_full, df, on="file_name", how="left").fillna({"score": 0})

    sns.barplot(
        data=df_merged,
        x="file_name",
        y="score",
        palette="Blues_r",
        ax=ax1
    )
    ax1.set_title("파일별 발음 평가 점수 (전체 10건)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("오디오 파일명", fontsize=10)
    ax1.set_ylabel("점수 (Score)", fontsize=10)
    ax1.set_ylim(0, 105)
    ax1.tick_params(axis='x', rotation=45)

    for p in ax1.patches:
        height = p.get_height()
        ax1.annotate(f"{height:.1f}점",
                     (p.get_x() + p.get_width() / 2., height),
                     ha='center', va='bottom', fontsize=8, xytext=(0, 3),
                     textcoords='offset points')

    # -------------------------------------------------------------------------
    # [그래프 2] 난이도별 평균 점수 ('미정' 제외)
    # -------------------------------------------------------------------------
    ax2 = fig.add_subplot(1, 3, 2)

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
    ax2.set_title("난이도별 평균 점수", fontsize=12, fontweight='bold')
    ax2.set_xlabel("난이도", fontsize=10)
    ax2.set_ylabel("평균 점수", fontsize=10)
    ax2.set_ylim(0, 105)

    for p in ax2.patches:
        height = p.get_height()
        if height > 0:
            ax2.annotate(f"{height:.1f}점",
                         (p.get_x() + p.get_width() / 2., height),
                         ha='center', va='bottom', fontsize=9, xytext=(0, 3),
                         textcoords='offset points')

    # -------------------------------------------------------------------------
    # [그래프 3] 전체 평균 오류율 (CER / WER 도넛 차트)
    # -------------------------------------------------------------------------
    ax3 = fig.add_subplot(1, 3, 3)

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
    ax3.set_title("전체 평균 오류율 (CER / WER)", fontsize=12, fontweight='bold')

    # 3. 레이아웃 조정 (상단에 타이틀 공간 확보를 위해 rect=[left, bottom, right, top] 지정)
    plt.tight_layout(rect=[0, 0, 1, 0.90])

    # 현재 폴더(stt/stt_test/) 내부에 이미지 저장
    output_img = os.path.join(current_dir, "stt_evaluation_dashboard.png")
    plt.savefig(output_img, dpi=300)
    print(f"시각화 완료! 이미지 저장 경로: {os.path.abspath(output_img)}")

    plt.show()


if __name__ == "__main__":
    main()