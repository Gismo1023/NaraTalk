# 한국어 읽기 연습 — D1 공통 실행 파일

## 1. 목적과 현재 범위
한국어를 배우는 외국인이 제시 문장을 읽고 STT 전사와 정답을 비교하며 반복 연습하는 프로젝트입니다.
핵심 지표는 전사 일치도입니다. WER/CER를 실제 발음 정확도로 단정하지 않습니다.

이 묶음은 PM·통합 담당의 파일 4개만 포함합니다.
- config.py: 공통 경로·제목·난이도·정규화 버전
- run_app.py: PyCharm 실행기
- requirements.txt: D1 설치 패키지
- README.md: 실행·통합 안내

**이 네 파일만으로 UI가 실행되지는 않습니다.** 기존 프로젝트의 app.py, data_loader.py, data/sentences.csv가 필요합니다.
새 파일 네 개를 기존 프로젝트 최상위에 배치하고 같은 이름의 파일은 변경 내용을 확인한 뒤 교체하세요.
app.py와 data_loader.py를 data 또는 sql 폴더로 옮기지 마세요.

## 2. 환경
- IDE: PyCharm 2026.2.1 (Python 인터프리터와 별개)
- Python: 3.11 권장
- 환경 관리: Miniconda
- UI: Streamlit
- 예정 DB: PostgreSQL, 관리 도구 DBeaver 26.2.2

D1 UI 실행에는 PostgreSQL·DBeaver 접속이 필요하지 않습니다.
현재 requirements.txt는 직접 의존성 범위를 지정한 목록이며 완전한 버전 잠금 파일이 아닙니다.
팀 통합 시 실제 설치 버전을 기록하고 같은 환경을 사용하세요.

## 3. 필요한 파일 배치
| 위치 | 파일 | 담당 |
|---|---|---|
| 최상위 | config.py, run_app.py, requirements.txt, README.md | PM·통합 |
| 최상위 | app.py | UI·배포, 기존 파일 필요 |
| 최상위 | data_loader.py | 데이터·음성, 기존 파일 필요 |
| data 폴더 | sentences.csv | 데이터·음성, 기존 파일 필요 |
| sql 폴더 | schema.sql | 서비스·DB, D1 UI에는 불필요 |

## 4. 설치
Miniconda Prompt에서 한 번만 환경을 만듭니다.
```bash
conda create -n reading-practice python=3.11 -y
conda activate reading-practice
```
이미 환경이 있으면 activate만 실행합니다. 프로젝트 폴더로 이동합니다. 아래 Windows 경로는 예시입니다.
```powershell
cd "C:\aihuman9\work_space\Python\reading_practice"
python -m pip install -r requirements.txt
python -c "import sys; print(sys.executable)"
```
마지막 명령에 표시된 Python 환경을 PyCharm 프로젝트 인터프리터로 선택하세요.
터미널 환경과 PyCharm 실행 인터프리터가 다를 수 있으므로 두 위치에서 확인합니다.

## 5. 실행
PyCharm에서 프로젝트 폴더를 열고 run_app.py를 Run하세요.
브라우저가 열리지 않으면 실행창에 표시되는 Local URL을 여세요.
종료는 PyCharm 실행 중지 버튼을 사용합니다.

터미널 실행도 가능합니다.
```bash
python -m streamlit run app.py
```
app.py를 일반 Python 스크립트로 직접 실행하지 마세요. Streamlit은 위 모듈 실행 방식으로 시작합니다.
run_app.py는 선택된 Python으로 Streamlit 자식 프로세스를 실행하며, 앱 코드 디버깅 구성은 별도 작업입니다.

## 6. 공통 변수와 함수
| 이름 | 의미 | 자료형 |
|---|---|---|
| BASE_DIR | 프로젝트 폴더 | pathlib.Path |
| DATA_DIR / SQL_DIR | 데이터/SQL 폴더 | pathlib.Path |
| SENTENCES_PATH / SCHEMA_PATH | 문장 CSV/스키마 경로 | pathlib.Path |
| APP_TITLE | 앱 제목 | str |
| LEVELS | 1=쉬움, 2=보통, 3=어려움 | dict[int, str] |
| NORMALIZATION_VERSION | 평가 정책 식별자 ko-v1 | str |

기존 app.py는 아래 이름으로 불러옵니다.
```python
from config import APP_TITLE, SENTENCES_PATH, LEVELS
from data_loader import load_sentences

sentences = load_sentences(SENTENCES_PATH)
```
문장 CSV 컬럼은 id, text, level, category입니다. 로더는 level을 Python int로 변환합니다.
CSV의 id는 문장 코드이며 DB UUID와 다릅니다. DB 도입 시 sentences.code에 매핑합니다.
정규화 버전 상수를 선언했다고 정규화 기능이 구현되는 것은 아닙니다.

## 7. D1 완료 확인
- [ ] 모든 팀원이 동일한 파일을 사용한다.
- [ ] 패키지 설치와 run_app.py 실행이 성공한다.
- [ ] 문장 30개와 난이도별 10개를 확인한다.
- [ ] 난이도·문장을 바꾸면 정답 표시가 바뀐다.
- [ ] 고정 시연 데이터와 실제 분석 결과를 구분한다.
- [ ] WER 어절·CER 공백 제외 문자·숫자 정책을 합의한다.
- [ ] 서비스 입력·출력 필드와 DB 관계를 합의한다.

DBeaver 연결·테이블 생성은 D1 선택 작업입니다. STT·TTS·실제 DB 저장은 이후 일정입니다.
이 README는 실제 팀 검증 완료를 주장하지 않습니다. 팀 PC의 실행 결과는 작업일지에 기록하세요.

## 8. 오류 확인
| 증상 | 확인할 내용 |
|---|---|
| app.py 없음 | run_app.py와 같은 폴더에 기존 app.py 배치 |
| No module named streamlit | 실행 인터프리터와 설치 인터프리터 일치 여부 |
| No module named data_loader | data_loader.py가 app.py와 같은 폴더에 있는지 |
| 문장 파일 오류 | data/sentences.csv의 위치·컬럼·난이도 확인 |
| missing ScriptRunContext | app.py 직접 Run 대신 run_app.py 사용 |
| 포트 사용 중 | 기존 앱 종료 또는 터미널 명령에 --server.port 8502 추가 |

비밀번호·API 키는 config.py에 넣지 않습니다. DB 연결 도입 시 환경변수로 관리하고 .env는 Git에 올리지 않습니다.
