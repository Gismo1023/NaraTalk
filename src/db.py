# db.py
# SQL은 sql_schema_sql 폴더의 개별 .sql 파일에서 관리합니다.
import os
from pathlib import Path
import psycopg
from psycopg.rows import dict_row
from psycopg.errors import UniqueViolation, ForeignKeyViolation
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent  # src 폴더
PROJECT_DIR = BASE_DIR.parent  # NaraTalk 프로젝트 루트
SQL_DIR = PROJECT_DIR / 'sql_schema_sql'  # 팀장이 만든 SQL 폴더
load_dotenv(BASE_DIR / '.env')  # src 폴더의 .env 읽기
DATABASE_URL = os.getenv('DATABASE_URL')


# PostgreSQL 연결
def get_connection():
    if not DATABASE_URL:
        raise ValueError('NaraTalk/src/.env 파일에 DATABASE_URL을 설정하세요.')
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


# SQL 파일의 내용을 문자열로 읽기
def load_sql(filename):
    file_path = (SQL_DIR / filename).resolve()

    if not file_path.is_relative_to(SQL_DIR.resolve()) or file_path.suffix.lower() != '.sql':
        raise ValueError('sql_schema_sql 폴더의 .sql 파일만 사용할 수 있습니다.')
    if not file_path.is_file():
        raise FileNotFoundError(f'SQL 파일을 찾을 수 없습니다: {file_path}')

    return file_path.read_text(encoding='utf-8-sig')


# 처음 한 번: 테이블 4개 생성 및 프로토타입 문장 34개 등록
def initialize_database():
    sql_files = [
        'extension_pgcrypto.sql',
        'create_users.sql',
        'create_sentences.sql',
        'create_practice_runs.sql',
        'create_error_items.sql',
        'seed_sentences_34.sql'
    ]

    with get_connection() as conn:
        with conn.cursor() as cursor:
            for filename in sql_files:
                cursor.execute(load_sql(filename))
                print(f'실행 완료: {filename}')


# 닉네임만으로 회원 등록. 내부 고유번호는 UUID 사용
def register_user(nickname):
    nickname = nickname.strip()
    if not nickname:
        raise ValueError('닉네임을 입력하세요.')

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(load_sql('register_user.sql'), (nickname,))
                return cursor.fetchone()
    except UniqueViolation as error:
        raise ValueError('이미 사용 중인 닉네임입니다.') from error


# 닉네임으로 회원 조회 (비밀번호 인증 기능은 없음)
def login_user(nickname):
    nickname = nickname.strip()
    if not nickname:
        return None

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('login_user.sql'), (nickname,))
            return cursor.fetchone()


# UUID로 등록된 회원 정보 조회
def get_user_by_id(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('get_user_by_id.sql'), (user_id,))
            return cursor.fetchone()


# 문장 목록 조회: 카테고리/난이도 선택 가능
# level은 1, 2, 3이 아니라 '쉬움', '보통', '어려움' 문자열
def get_sentences(category=None, level=None):
    if level is not None and level not in ('쉬움', '보통', '어려움'):
        raise ValueError("level은 '쉬움', '보통', '어려움' 중 하나여야 합니다.")

    if category is not None and level is not None:
        filename = 'get_sentences_by_category_level.sql'
        params = (category, level)
    elif category is not None:
        filename = 'get_sentences_by_category.sql'
        params = (category,)
    elif level is not None:
        filename = 'get_sentences_by_level.sql'
        params = (level,)
    else:
        filename = 'get_sentences_all.sql'
        params = ()

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql(filename), params)
            return cursor.fetchall()


# 문장 번호(1~34)로 문장 1개 조회
def get_sentence(sentence_no):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('get_sentence.sql'), (sentence_no,))
            return cursor.fetchone()


# 프로토타입 SENTENCES_DB와 같은 카테고리별 딕셔너리 형태로 변환
def get_sentences_grouped():
    grouped = {}
    for sentence in get_sentences():
        category = sentence['category']
        if category not in grouped:
            grouped[category] = []
        grouped[category].append({
            'ko': sentence['ko'],
            'en': sentence['en'],
            'difficulty': sentence['level']
        })
    return grouped


# STT 연습 결과 저장
def save_practice_run(user_id, sentence_id, transcript,
                      wer, cer, latency_ms, score, grade,
                      feedback, substitutions, deletions, insertions):

    if grade not in ('매우 우수', '양호한 수준', '기초에 집중'):
        raise ValueError('grade는 매우 우수, 양호한 수준, 기초에 집중 중 하나여야 합니다.')

    params = (
        user_id, sentence_id, transcript,
        wer, cer, latency_ms, score, grade,
        feedback, substitutions, deletions, insertions
    )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('save_practice_run.sql'), params)
            return cursor.fetchone()['id']


# 하나의 연습에서 발생한 단어 오류 저장
def save_error_item(run_id, error_type, reference_token=None,
                    hypothesis_token=None, position=None):
    if error_type not in ('substitution', 'deletion', 'insertion'):
        raise ValueError('error_type은 substitution, deletion, insertion 중 하나여야 합니다.')

    params = (run_id, error_type, reference_token, hypothesis_token, position)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('save_error_item.sql'), params)
            return cursor.fetchone()['id']


# 하나의 연습에서 발생한 오류 여러 건을 한 번의 연결로 저장
#   items: [{"error_type", "reference_token", "hypothesis_token", "position"}, ...]
#   반환값: 저장한 건수
def save_error_items(run_id, items):
    rows = []
    for item in items or []:
        error_type = item.get("error_type")
        if error_type not in ('substitution', 'deletion', 'insertion'):
            raise ValueError('error_type은 substitution, deletion, insertion 중 하나여야 합니다.')
        rows.append((run_id, error_type, item.get("reference_token"),
                     item.get("hypothesis_token"), item.get("position")))

    if not rows:
        return 0

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(load_sql('save_error_item.sql'), rows)
    return len(rows)


# 회원별 STT 연습 내역 조회
def get_practice_history(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('get_practice_history.sql'), (user_id,))
            return cursor.fetchall()


# 특정 연습에서 발생한 오류 조회
def get_error_items(run_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('get_error_items.sql'), (run_id,))
            return cursor.fetchall()


# 회원 닉네임 수정 (사용자 식별에는 UUID 사용)
def update_user_nickname(user_id, nickname):
    nickname = nickname.strip()
    if not nickname:
        raise ValueError('닉네임을 입력하세요.')

    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(load_sql('update_user_nickname.sql'), (nickname, user_id))
                return cursor.fetchone()
    except UniqueViolation as error:
        raise ValueError('이미 사용 중인 닉네임입니다.') from error


# 문장 번호로 학습 문장 수정
def update_sentence(sentence_no, category, level, ko, en):
    if level not in ('쉬움', '보통', '어려움'):
        raise ValueError("level은 '쉬움', '보통', '어려움' 중 하나여야 합니다.")

    category = category.strip()
    ko = ko.strip()
    en = en.strip()
    if not category or not ko or not en:
        raise ValueError('카테고리, 한국어 문장, 영어 번역을 모두 입력하세요.')

    params = (category, level, ko, en, sentence_no)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('update_sentence.sql'), params)
            return cursor.fetchone()


# 개별 STT 오류 기록 수정
def update_error_item(error_id, error_type, reference_token=None,
                      hypothesis_token=None, position=None):
    if error_type not in ('substitution', 'deletion', 'insertion'):
        raise ValueError('error_type은 substitution, deletion, insertion 중 하나여야 합니다.')

    params = (error_type, reference_token, hypothesis_token, position, error_id)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('update_error_item.sql'), params)
            return cursor.fetchone()


# 회원 탈퇴: 연습 기록을 먼저 삭제한 뒤 회원 삭제 (한 트랜잭션)
def delete_user(user_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('delete_user_practice_runs.sql'), (user_id,))
            cursor.execute(load_sql('delete_user.sql'), (user_id,))
            return cursor.fetchone() is not None


# 학습 문장 삭제 (연습 기록이 남아 있으면 삭제 거부)
def delete_sentence(sentence_no):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(load_sql('delete_sentence.sql'), (sentence_no,))
                return cursor.fetchone() is not None
    except ForeignKeyViolation as error:
        raise ValueError('이 문장을 사용한 연습 기록이 있어 삭제할 수 없습니다.') from error


# 연습 기록 삭제 (해당 오류 상세 기록은 자동으로 함께 삭제)
def delete_practice_run(run_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('delete_practice_run.sql'), (run_id,))
            return cursor.fetchone() is not None


# STT 오류 상세 기록 한 건 삭제
def delete_error_item(error_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('delete_error_item.sql'), (error_id,))
            return cursor.fetchone() is not None

# 관리자 로그인
def login_manager(password):
    if not password:
        return None

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('login_manager.sql'), (password,))
            return cursor.fetchone()


# 추가 5개
#users에 등록된 전체 사용자 수를 정수로 반환한다.
def get_count_users():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('get_count_users.sql'))
            return cursor.fetchone()['total_users']


#전체 사용자의 닉네임·등록일·연습 횟수를 최근 등록순으로 조회해 딕셔너리 리스트로 반환한다.
def get_nickname_cteated_at():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('get_nickname_cteated_at.sql'))
            return cursor.fetchall()


#전체 사용자의 카테고리별 연습 횟수 상위 5개를 딕셔너리 리스트로 반환한다.
def get_category_top5():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('get_category_top5.sql'))
            return cursor.fetchall()


#전체 사용자의 난이도별 연습 횟수 상위 3개를 딕셔너리 리스트로 반환한다.
def get_level_top5():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('get_level_top5.sql'))
            return cursor.fetchall()


#전체 사용자의 문장 ID별 연습 횟수 상위 5개를 딕셔너리 리스트로 반환한다.
def get_sentence_top5():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(load_sql('get_sentence_top5.sql'))
            return cursor.fetchall()





if __name__ == '__main__':
    initialize_database()
    print(f'문장 등록 확인: {len(get_sentences())}개')
