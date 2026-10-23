# NaraTalk `db.py` 함수별 반환값 완전 가이드

> **대상:** `src_db/db.py`와 `sql_schema_sql/*.sql`을 연동하는 UI·STT·TTS·AI 팀원  
> **작성 기준:** 제공된 `db.py` 코드 및 NaraTalk의 해당 SQL 파일 중 `SELECT`·`RETURNING` 구문  
> **주의:** 아래 출력은 반환 **형식을 설명하기 위한 예시**이며, 실제 PostgreSQL에서 실행·검증한 결과는 아닙니다. UUID와 날짜는 예시 값입니다.

## 1. `return`이 무엇인지부터 이해하기

함수는 어떤 작업을 하고 나서 결과를 호출한 곳으로 돌려줄 수 있습니다. 그때 사용하는 문법이 `return`입니다.

```python
def add_numbers(first_number, second_number):
    return first_number + second_number

result = add_numbers(10, 20)
print(result)  # 30
```

1. `add_numbers(10, 20)`을 호출합니다.
2. `first_number=10`, `second_number=20`이 됩니다.
3. `return 30`이 실행되어 호출한 쪽에 `30`이 전달됩니다.
4. `result`에 `30`이 저장됩니다.

**`print()`와 `return`의 차이:** `print()`는 화면에 보여주고, `return`은 다른 코드가 사용할 수 있는 값을 돌려줍니다. `return`이 없는 함수는 정상 종료 시 `None`을 돌려줍니다.

### 이 문서에서 사용하는 자료형

| 자료형 | 뜻 | 예시 |
|---|---|---|
| `dict` | 이름(키)으로 값을 찾아 쓰는 자료형, 딕셔너리 | `{'id': ..., 'nickname': '나비'}` |
| `list[dict]` | 딕셔너리가 여러 개 들어 있는 목록 | `[{'ko': '안녕하세요!'}, ...]` |
| `str` | 문자열(글자) | `'물 주세요.'` |
| `bool` | 참 또는 거짓 | `True`, `False` |
| `None` | 결과가 없음을 나타내는 값 | `None` |
| `uuid.UUID` | 겹치지 않게 식별하려는 고유번호 객체 | `UUID('11111111-1111-4111-8111-111111111111')` |
| `datetime` | 날짜 및 시간 객체 | `datetime` 값 (`created_at`) |
| `psycopg.Connection` | PostgreSQL과 통신하는 연결 객체 | `conn` |

**매우 중요한 규칙:** 이 프로젝트는 `psycopg.connect(..., row_factory=dict_row)`로 연결하므로 SQL 조회 한 행은 보통 **딕셔너리**, 여러 행은 **딕셔너리 리스트**로 반환됩니다.

- `cursor.fetchone()` → `dict` 또는 `None`
- `cursor.fetchall()` → `list[dict]` (결과가 없으면 `[]`)
- `cursor.fetchone()['id']` → 딕셔너리에서 `id`만 꺼냄. 이 프로젝트에서는 `uuid.UUID`
- `return cursor.fetchone() is not None` → `True` 또는 `False`

---

## 2. 함수 21개 반환값 한눈에 보기

| 번호 | 함수 | 정상 반환값 | 데이터가 없을 때 / 특징 |
|---:|---|---|---|
| 1 | `get_connection()` | `psycopg.Connection` | 설정·접속 오류 시 예외 |
| 2 | `load_sql(filename)` | SQL 내용 `str` | 파일 없음·경로 잘못됨 시 예외 |
| 3 | `initialize_database()` | `None` | 테이블 생성·문장 등록만 수행 |
| 4 | `register_user(nickname)` | 회원 `dict` | 닉네임 공백·중복 시 `ValueError` |
| 5 | `login_user(nickname)` | 회원 `dict` 또는 `None` | 미등록/빈 닉네임이면 `None` |
| 6 | `get_user_by_id(user_id)` | 회원 `dict` 또는 `None` | 회원이 없으면 `None` |
| 7 | `get_sentences(category=None, level=None)` | `list[dict]` | 일치 문장 없으면 `[]` |
| 8 | `get_sentence(sentence_no)` | 문장 `dict` 또는 `None` | 문장 번호 없으면 `None` |
| 9 | `get_sentences_grouped()` | 카테고리별 `dict` | 문장 없으면 `{}` |
| 10 | `save_practice_run(...)` | `run_id` (`uuid.UUID`) | 정상 저장 시 한 개의 ID 반환 |
| 11 | `save_error_item(...)` | `error_id` (`uuid.UUID`) | 정상 저장 시 한 개의 ID 반환 |
| 12 | `get_practice_history(user_id)` | `list[dict]` | 기록 없으면 `[]` |
| 13 | `get_error_items(run_id)` | `list[dict]` | 오류 없으면 `[]` |
| 14 | `update_user_nickname(user_id, nickname)` | 변경된 회원 `dict` 또는 `None` | 대상 회원 없으면 `None` |
| 15 | `update_sentence(sentence_no, category, level, ko, en)` | 변경된 문장 `dict` 또는 `None` | 대상 문장 없으면 `None` |
| 16 | `update_practice_status(run_id, status)` | 수정된 상태 `dict` 또는 `None` | 대상 연습 없으면 `None` |
| 17 | `update_error_item(error_id, error_type, ...)` | 수정된 오류 `dict` 또는 `None` | 대상 오류 없으면 `None` |
| 18 | `delete_user(user_id)` | `bool` | 삭제 성공 `True`, 회원 없음 `False` |
| 19 | `delete_sentence(sentence_no)` | `bool` | 대상 없음 `False`; 연습 기록 연결 시 `ValueError` |
| 20 | `delete_practice_run(run_id)` | `bool` | 삭제 성공 `True`, 대상 없음 `False` |
| 21 | `delete_error_item(error_id)` | `bool` | 삭제 성공 `True`, 대상 없음 `False` |

**참고:** 오류가 발생할 때는 `None`을 반환하는 것이 아니라 **예외(Exception)** 가 발생할 수 있습니다. 정상적인 빈 결과와 오류를 구분해야 합니다.

---

## 3. 공통 함수 (DB 내부에서 사용하는 함수)

### 3-1. `get_connection()`

**역할:** `.env`에서 읽은 `DATABASE_URL`을 사용해 PostgreSQL에 연결합니다.

**반환형:** `psycopg.Connection` (데이터가 담긴 딕셔너리가 아님)

```python
from src_db.db import get_connection

conn = get_connection()
print(type(conn))  # psycopg.Connection 계열의 타입
conn.close()       # 사용을 마친 연결 종료
```

- `conn`은 SQL을 실행할 수 있게 해 주는 연결 객체입니다.
- `DATABASE_URL`이 비어 있으면 `ValueError`가 발생합니다.
- 주소·비밀번호·서버 상태에 문제가 있으면 PostgreSQL 연결 예외가 발생할 수 있습니다.
- 평소 UI 팀원이 이 함수를 직접 호출할 필요는 거의 없습니다. 아래 CRUD 함수가 내부에서 연결합니다.

### 3-2. `load_sql(filename)`

**역할:** `sql_schema_sql` 폴더의 `.sql` 파일을 읽어 문자열로 반환합니다.

**반환형:** `str`

```python
sql_text = load_sql('get_sentence.sql')
print(sql_text)
```

예시 반환 내용:

```sql
SELECT id, sentence_no, category, level, ko, en
FROM sentences
WHERE sentence_no = %s;
```

- SQL을 **실행하지 않고 읽기만** 합니다.
- 폴더 밖의 파일이나 `.sql`이 아닌 파일을 요청하면 `ValueError`가 발생합니다.
- 존재하지 않는 파일은 `FileNotFoundError`가 발생합니다.

### 3-3. `initialize_database()`

**역할:** 확장 기능 준비 → 4개 테이블 생성 → 기본 문장 34개 등록을 순서대로 실행합니다.

**반환형:** `None`

```python
result = initialize_database()
print(result)  # None
```

함수 안의 `print('실행 완료: ...')`는 진행 메시지를 화면에 표시하는 것입니다. `return` 값이 아닙니다.

**주의:** 문장 등록 SQL을 반복 실행하면 기존 문장 데이터가 갱신될 수 있으니 앱 실행 때마다 호출하지 말고 초기 구축 때 사용합니다.

---

## 4. 회원(`users`) 함수

회원 한 명을 반환하는 함수들의 공통 딕셔너리 구조는 SQL에서 다음 3개 컬럼을 선택하므로 확정됩니다.

```python
{
    'id': UUID('11111111-1111-4111-8111-111111111111'),
    'nickname': '나비',
    'created_at': datetime_객체
}
```

> 위 `datetime_객체`는 자료형을 설명하기 위한 표기이며 그대로 실행하는 코드가 아닙니다.

### 4-1. `register_user(nickname)`

**입력:** 닉네임 `str`  
**역할:** 닉네임으로 새 회원을 등록합니다.  
**반환형:** 회원 정보 `dict`

```python
user = register_user('나비')
user_id = user['id']
print(user['nickname'])  # 나비
```

**반환 키:** `id` (`UUID`), `nickname` (`str`), `created_at` (`datetime`)

**오류:** 빈 닉네임이나 기존 닉네임과 중복(대소문자 구분 없이 중복 포함)이면 `ValueError`가 발생합니다. 실패 시 `None`을 반환하는 방식이 아닙니다.

### 4-2. `login_user(nickname)`

**입력:** 닉네임 `str`  
**역할:** 같은 닉네임을 가진 회원을 찾습니다.  
**반환형:** 회원 `dict` 또는 `None`

```python
user = login_user('나비')
if user is None:
    print('등록되지 않은 사용자입니다.')
else:
    print(user['id'])
```

**반환 키:** `id`, `nickname`, `created_at`

**없을 때:** `None`  
**중요:** 비밀번호를 확인하는 로그인 기능이 아니라 **닉네임 조회 기능**입니다.

### 4-3. `get_user_by_id(user_id)`

**입력:** 회원 UUID  
**역할:** 고유번호로 회원을 찾습니다.  
**반환형:** 회원 `dict` 또는 `None`

```python
user = get_user_by_id(user_id)
if user is not None:
    print(user['nickname'])
```

**반환 키:** `id`, `nickname`, `created_at`  
**없을 때:** `None`

### 4-4. `update_user_nickname(user_id, nickname)`

**입력:** 회원 UUID, 새 닉네임 `str`  
**역할:** 기존 회원의 닉네임을 변경합니다.  
**반환형:** **수정 후** 회원 `dict` 또는 `None`

```python
updated_user = update_user_nickname(user_id, '새나비')
if updated_user is not None:
    print(updated_user['nickname'])  # 새나비
```

**반환 키:** `id`, `nickname`, `created_at`  
**없을 때:** `None`  
**오류:** 빈 닉네임 또는 중복 닉네임이면 `ValueError`

### 4-5. `delete_user(user_id)`

**입력:** 회원 UUID  
**역할:** 먼저 해당 회원의 연습 기록을 삭제하고, 이후 회원을 삭제합니다. 연습에 연결된 오류 상세도 함께 삭제됩니다.  
**반환형:** `bool`

```python
deleted = delete_user(user_id)
print(deleted)  # True 또는 False
```

- `True`: 해당 회원 행이 실제로 삭제됨
- `False`: 해당 회원이 없어 삭제한 회원 행이 없음
- `True`/`False`만 반환하며 회원 딕셔너리는 반환하지 않습니다.
- **주의:** 회원 연습 기록까지 없어질 수 있는 실제 삭제 작업입니다.

---

## 5. 학습 문장(`sentences`) 함수

문장 한 건의 반환 키는 다음과 같습니다.

```python
{
    'id': UUID('22222222-2222-4222-8222-222222222222'),
    'sentence_no': 27,
    'category': '식당 및 주문',
    'level': '쉬움',
    'ko': '물 주세요.',
    'en': 'Water, please.'
}
```

`id`는 연습 저장에 필요한 **UUID**, `sentence_no`는 화면에 표시하는 **정수 문장 번호**입니다. 둘을 바꿔 사용하면 안 됩니다.

### 5-1. `get_sentences(category=None, level=None)`

**입력:** 선택적으로 카테고리와 난이도  
**역할:** 조건에 맞는 문장 **여러 개**를 조회합니다.  
**반환형:** `list[dict]`

```python
all_sentences = get_sentences()                     # 전체 문장
restaurant_sentences = get_sentences(category='식당 및 주문')
easy_sentences = get_sentences(level='쉬움')
filtered = get_sentences(category='식당 및 주문', level='쉬움')

print(len(all_sentences))  # 기본 문장만 등록되어 있다면 34
```

각 문장 딕셔너리의 키: `id`, `sentence_no`, `category`, `level`, `ko`, `en`

**없을 때:** `[]`  
**오류:** `level`에 `'쉬움'`, `'보통'`, `'어려움'` 이외의 값을 넣으면 `ValueError`

### 5-2. `get_sentence(sentence_no)`

**입력:** 정수 문장 번호, 예를 들어 `27`  
**역할:** 문장 **한 개**를 조회합니다.  
**반환형:** 문장 `dict` 또는 `None`

```python
sentence = get_sentence(27)
if sentence is not None:
    print(sentence['ko'])  # 물 주세요.
    sentence_id = sentence['id']
```

**반환 키:** `id`, `sentence_no`, `category`, `level`, `ko`, `en`  
**없을 때:** `None`

### 5-3. `get_sentences_grouped()`

**입력:** 없음  
**역할:** 문장 목록을 카테고리별로 묶어 UI 프로토타입 형식으로 변환합니다.  
**반환형:** `dict[str, list[dict]]`, 즉 **카테고리 이름 → 문장 목록** 형태의 딕셔너리

```python
grouped = get_sentences_grouped()

# 반환 구조 예시
{
    '식당 및 주문': [
        {'ko': '물 주세요.', 'en': 'Water, please.', 'difficulty': '쉬움'},
        # ... 다른 문장
    ],
    # ... 다른 카테고리
}
```

**반환 키:** 최상위 딕셔너리의 키는 카테고리명, 각 문장 딕셔너리의 키는 `ko`, `en`, `difficulty`  
**없을 때:** `{}`

**매우 중요:** 여기에는 `id`(문장 UUID)가 **없습니다**. 연습 결과를 DB에 저장하려면 `get_sentence()`나 `get_sentences()`가 반환하는 `id`를 사용하세요.

### 5-4. `update_sentence(sentence_no, category, level, ko, en)`

**입력:** 문장 번호와 변경할 카테고리, 난이도, 한국어 원문, 영어 번역  
**역할:** 기존 학습 문장 수정  
**반환형:** **수정 후** 문장 `dict` 또는 `None`

```python
updated_sentence = update_sentence(
    27, '식당 및 주문', '쉬움', '물 좀 주세요.', 'Some water, please.'
)
if updated_sentence is not None:
    print(updated_sentence['ko'])  # 물 좀 주세요.
```

**반환 키:** `id`, `sentence_no`, `category`, `level`, `ko`, `en`  
**없을 때:** `None`  
**오류:** 잘못된 난이도 또는 필수 문자열이 비어 있으면 `ValueError`

### 5-5. `delete_sentence(sentence_no)`

**입력:** 정수 문장 번호  
**역할:** 해당 학습 문장 삭제  
**반환형:** `bool`

```python
deleted = delete_sentence(27)
print(deleted)  # True 또는 False
```

- `True`: 문장 삭제 성공
- `False`: 해당 번호의 문장이 없어 삭제하지 않음
- **오류:** 연습 기록에서 참조 중인 문장이면 FK 제약 때문에 삭제할 수 없어 `ValueError` 발생

> 삭제·수정 예제는 실제 DB의 문장을 바꿉니다. 팀 공용 DB에서는 테스트용 데이터나 별도의 테스트 DB를 사용하세요.

---

## 6. STT 연습 결과(`practice_runs`) 함수

### 6-1. `save_practice_run(user_id, sentence_id, transcript, wer, cer, latency_ms, status)`

**역할:** 사용자 1회의 STT 평가 결과 저장  
**입력:** 회원 UUID, **문장 UUID**, 인식 문자열, WER/CER(소수), 처리시간(ms), 합격 여부(`bool`)  
**반환형:** `uuid.UUID` **하나** (= `run_id`)

```python
run_id = save_practice_run(
    user_id=user_id,
    sentence_id=sentence_id,
    transcript='물 주세요.',
    wer=0.0,
    cer=0.0,
    latency_ms=850,
    status=True
)
print(run_id)  # 저장된 연습의 UUID
```

이 함수의 마지막 줄은:

```python
return cursor.fetchone()['id']
```

입니다. SQL의 `RETURNING id` 결과는 처음에는 `{'id': UUID(...)}` 딕셔너리이지만, `['id']`로 값만 꺼내서 **UUID 한 개**를 반환합니다.

- `status=True`: 합격, `False`: 불합격
- `wer=0.2`: 20% 오류율 (20이라는 정수가 아님)
- `latency_ms=850`: 850밀리초
- **오류:** `status`가 실제 `bool`이 아니면 `ValueError`. 존재하지 않는 사용자·문장 UUID 등은 DB 오류가 될 수 있습니다.

### 6-2. `get_practice_history(user_id)`

**역할:** 회원의 연습 기록을 최근 순서로 여러 건 조회  
**반환형:** `list[dict]`  
**없을 때:** `[]`

한 기록 딕셔너리의 **전체 키 14개**는 다음과 같습니다.

| 키 | 뜻 | 자료형 |
|---|---|---|
| `id` | 연습 기록 ID (`run_id`) | UUID |
| `nickname` | 회원 닉네임 | str |
| `sentence_no` | 학습 문장 번호 | int |
| `category` | 학습 카테고리 | str |
| `level` | 난이도 | str |
| `ko` | 한국어 정답 | str |
| `en` | 영어 번역 | str |
| `transcript` | STT 인식 문장 | str 또는 None |
| `wer` | 단어 오류율 | float 또는 None |
| `cer` | 문자 오류율 | float 또는 None |
| `latency_ms` | STT 처리시간 | int 또는 None |
| `status` | 합격 여부 | bool |
| `status_label` | 화면에 표시할 `합격` / `불합격` | str |
| `created_at` | 연습 시각 | datetime |

```python
history = get_practice_history(user_id)

for record in history:
    print(record['ko'])
    print(record['transcript'])
    print(record['status_label'])
    if record['wer'] is not None:
        print(f"WER: {record['wer']:.1%}")
```

여기서 `for`는 리스트 안의 기록을 **한 개씩** 꺼내는 반복문입니다. `.1%`는 `0.2`를 `20.0%` 형태로 표시합니다.

**주의:** `wer`, `cer`, `transcript`, `latency_ms`는 테이블 정의상 `NULL`을 허용합니다. 문자열이나 숫자라고 가정하기 전에 `None` 여부를 확인하세요.

### 6-3. `update_practice_status(run_id, status)`

**역할:** 연습 기록의 합격 여부 수정  
**반환형:** `dict` 또는 `None`

```python
updated_run = update_practice_status(run_id, False)
if updated_run is not None:
    print(updated_run['status'])  # False
```

**반환 키 5개:** `id`, `user_id`, `sentence_id`, `status`, `created_at`

- 없는 `run_id`면 `None`
- `status`가 `True`나 `False`가 아니면 `ValueError`
- **이 함수는 전체 연습 기록을 반환하지 않습니다.** `transcript`, `wer`, `cer`는 반환 키에 없습니다.

### 6-4. `delete_practice_run(run_id)`

**역할:** 연습 기록 1개 삭제. 관련 `error_items`도 `ON DELETE CASCADE`로 삭제  
**반환형:** `bool`

```python
deleted = delete_practice_run(run_id)
print(deleted)  # True 또는 False
```

- `True`: 삭제된 연습 기록이 있음
- `False`: 해당 ID의 연습 기록이 없음

---

## 7. 인식 오류 상세(`error_items`) 함수

### 7-1. `save_error_item(run_id, error_type, reference_token=None, hypothesis_token=None, position=None)`

**역할:** 연습 1회에서 발생한 대체·삭제·삽입 오류 한 건 저장  
**반환형:** `uuid.UUID` 한 개 (= `error_id`)

```python
error_id = save_error_item(
    run_id=run_id,
    error_type='deletion',
    reference_token='물',
    hypothesis_token=None,
    position=0
)
print(error_id)  # 오류 기록 UUID
```

**오류 유형:**

- `substitution`: 원래 단어를 다른 단어로 인식한 대체 오류
- `deletion`: 원래 단어를 빠뜨린 삭제 오류
- `insertion`: 정답에 없는 단어가 추가된 삽입 오류

**오류:** 이 세 문자열 이외의 `error_type`은 `ValueError`. 잘못된 `run_id`는 FK 오류가 발생할 수 있습니다.

### 7-2. `get_error_items(run_id)`

**역할:** 특정 연습에서 기록된 오류 여러 개 조회  
**반환형:** `list[dict]`  
**없을 때:** `[]`

오류 한 건의 반환 키 5개:

```python
{
    'id': UUID('33333333-3333-4333-8333-333333333333'),
    'error_type': 'deletion',
    'reference_token': '물',
    'hypothesis_token': None,
    'position': 0
}
```

```python
errors = get_error_items(run_id)
for error in errors:
    print(error['error_type'])
    print(error['reference_token'], error['hypothesis_token'])
```

**주의:** 이 조회 결과에는 `run_id`가 포함되지 않습니다. 조회에 사용한 `run_id`는 호출한 코드에서 따로 보관해야 합니다.

### 7-3. `update_error_item(error_id, error_type, reference_token=None, hypothesis_token=None, position=None)`

**역할:** 기존 오류 항목 수정  
**반환형:** 수정 후 오류 `dict` 또는 `None`

```python
updated_error = update_error_item(
    error_id, 'substitution', '물', '불', 0
)
if updated_error is not None:
    print(updated_error['reference_token'])
    print(updated_error['hypothesis_token'])
```

**반환 키 6개:** `id`, `run_id`, `error_type`, `reference_token`, `hypothesis_token`, `position`

- `get_error_items()`의 항목과 달리 수정 함수의 결과에는 `run_id`도 포함됩니다.
- 대상이 없으면 `None`
- 잘못된 오류 유형은 `ValueError`

### 7-4. `delete_error_item(error_id)`

**역할:** 오류 상세 항목 한 개 삭제  
**반환형:** `bool`

```python
deleted = delete_error_item(error_id)
print(deleted)  # True 또는 False
```

- `True`: 해당 오류가 실제로 삭제됨
- `False`: 해당 오류가 없음

---

## 8. 팀원별로 어떤 반환값을 사용할까?

| 담당 | 주로 호출할 함수 | 반환값에서 사용할 정보 |
|---|---|---|
| UI | `register_user`, `login_user` | `user['id']`, `user['nickname']` |
| UI | `get_sentences`, `get_sentence` | `sentence['id']`, `sentence['ko']`, `sentence['en']` |
| TTS | `get_sentence` | `sentence['ko']`를 음성 합성 입력으로 사용 |
| STT | DB 직접 조회보다 UI·서비스에서 문장 정보 전달받기 | 전사 결과 `transcript`와 `latency_ms` 생산 |
| AI 평가 | `get_sentence` 결과 활용 | 정답 `ko`와 STT 결과 비교 후 WER/CER/합격 여부 생산 |
| 서비스·DB | `save_practice_run` | `run_id` UUID를 받아 저장·조회 연결 |
| 서비스·DB | `save_error_item` | `error_id` UUID를 받아 오류 기록 추적 |
| UI 결과 화면 | `get_practice_history` | `status_label`, `transcript`, `wer`, `cer` 등 |
| UI 오류 화면 | `get_error_items` | 오류의 유형·원문·인식 단어·위치 |

### 한 번의 학습 흐름 예시

```python
from src_db.db import login_user, get_sentence, save_practice_run, get_practice_history

# 1. UI: 등록된 회원 찾기
user = login_user('나비')
if user is None:
    raise ValueError('회원이 없습니다.')
user_id = user['id']

# 2. UI/TTS: 학습 문장 하나 가져오기
sentence = get_sentence(27)
if sentence is None:
    raise ValueError('문장이 없습니다.')
sentence_id = sentence['id']
reference_text = sentence['ko']  # TTS 음성 합성과 AI 평가의 정답

# 3. 아래 값들은 STT·AI 기능에서 전달됐다고 가정한 예시
transcript = '물 주세요.'
wer = 0.0
cer = 0.0
latency_ms = 850
status = True

# 4. DB: 연습 결과 저장 → UUID 하나를 반환
run_id = save_practice_run(user_id, sentence_id, transcript, wer, cer, latency_ms, status)

# 5. UI: 다시 조회 → 기록 딕셔너리들의 리스트 반환
history = get_practice_history(user_id)
for record in history:
    print(record['ko'], record['status_label'])
```

**실행 흐름 정리:** `login_user()` → 회원 딕셔너리 → `get_sentence()` → 문장 딕셔너리 → `save_practice_run()` → UUID → `get_practice_history()` → 딕셔너리 리스트.

---

## 9. 초보자가 자주 하는 실수

### 실수 1. `None`을 딕셔너리로 사용

```python
user = login_user('존재하지 않는 닉네임')
print(user['id'])  # user가 None이면 TypeError 발생
```

**올바른 사용:**

```python
if user is not None:
    print(user['id'])
else:
    print('회원이 없습니다.')
```

### 실수 2. `list[dict]`를 `dict`처럼 사용

```python
sentences = get_sentences()
# print(sentences['ko'])  # 리스트는 문자열 키로 접근할 수 없음
```

**올바른 사용:**

```python
for sentence in sentences:
    print(sentence['ko'])
```

### 실수 3. `run_id`를 딕셔너리라고 생각

```python
run_id = save_practice_run(...)
# print(run_id['id'])  # 이미 UUID 자체를 반환하므로 잘못된 접근
```

**올바른 사용:** 반환받은 `run_id`를 그대로 `save_error_item(run_id, ...)` 또는 `get_error_items(run_id)`에 전달합니다.

### 실수 4. `sentence_no`와 `sentence_id` 혼동

```python
sentence = get_sentence(27)
sentence_id = sentence['id']  # UUID
# save_practice_run(..., sentence_id=27, ...)  # 잘못된 값
```

### 실수 5. `status`를 문자열로 전달

```python
# status='합격'  # 잘못됨
status=True       # 올바름
```

### 실수 6. 화면 출력과 반환값을 혼동

`initialize_database()`에서 파일별 완료 메시지가 출력되더라도 반환값은 `None`입니다.

### 실수 7. 예외를 빈 결과로 착각

- 조회 조건에 맞는 데이터가 없을 때: `None`, `[]`, `{}` 중 함수에 정의된 값
- DB 연결 실패·SQL 오류·입력값 검증 실패: 대개 **예외** 발생. 빈 결과가 자동 반환되는 것은 아님

---

## 10. 마지막 요약: 반환형만 외운다면

```text
DB 연결 객체             → get_connection()
SQL 문자열              → load_sql()
반환값 없음(None)       → initialize_database()

회원 dict                → register_user()
회원 dict 또는 None      → login_user(), get_user_by_id(), update_user_nickname()

문장 dict 또는 None      → get_sentence(), update_sentence()
문장 dict 리스트         → get_sentences()
카테고리별 dict          → get_sentences_grouped()

연습 run_id (UUID)       → save_practice_run()
연습 dict 리스트         → get_practice_history()
연습 상태 dict 또는 None → update_practice_status()

오류 error_id (UUID)     → save_error_item()
오류 dict 리스트         → get_error_items()
오류 dict 또는 None      → update_error_item()

True / False             → delete_user(), delete_sentence(),
                          delete_practice_run(), delete_error_item()
```

> **협업 시 유의:** 지금 문서의 딕셔너리 키는 함께 제공된 SQL 파일의 `SELECT`/`RETURNING`을 근거로 작성했습니다. SQL 파일의 선택 컬럼이 바뀌면 실제 Python 반환 딕셔너리도 바뀌므로, 팀원용 문서도 같이 수정해야 합니다. 실제 DB 동작은 별도 통합 테스트가 필요합니다.
