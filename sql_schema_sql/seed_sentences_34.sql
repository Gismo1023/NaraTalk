-- 프로토타입 SENTENCES_DB의 34개 문장을 원문 그대로 등록합니다.
-- 문장 번호는 카테고리 순서대로 1부터 34까지 부여합니다.
-- 이미 같은 sentence_no가 있으면 문장 내용을 갱신합니다.
INSERT INTO sentences (sentence_no, category, level, ko, en)
VALUES
    (1, '필수 기초 회화', '쉬움', '안녕하세요!', 'Hello!'),
    (2, '필수 기초 회화', '쉬움', '감사합니다!', 'Thank you!'),
    (3, '필수 기초 회화', '쉬움', '죄송합니다!', 'I''m sorry!'),
    (4, '필수 기초 회화', '쉬움', '도와주세요!', 'Help me, please!'),
    (5, '이동 및 길찾기', '쉬움', '여기 어디에요?', 'Where am I?'),
    (6, '이동 및 길찾기', '쉬움', '화장실 어디에 있어요?', 'Where is the restroom?'),
    (7, '이동 및 길찾기', '보통', '서울역으로 가는 지하철은 어디서 타요?', 'Where do I take the subway to Seoul Station?'),
    (8, '이동 및 길찾기', '보통', '공항에 어떻게 가요?', 'How do I get to the airport?'),
    (9, '이동 및 길찾기', '어려움', '이 버스가 명동역으로 가나요?', 'Does this bus go to Myeongdong Station?'),
    (10, '이동 및 길찾기', '어려움', '교통카드 보증금은 어디서 환급받을 수 있나요?', 'Where can I get a refund for the transit card deposit?'),
    (11, '이동 및 길찾기', '어려움', '환승 할인 적용받으려면 몇 분 이내에 갈아타야 하죠?', 'Within how many minutes do I need to transfer for the transfer discount?'),
    (12, '숙박 및 기타', '쉬움', '짐을 맡기고 싶어요.', 'Can I store my bags here?'),
    (13, '숙박 및 기타', '쉬움', '체크인 하고 싶어요.', 'I''d like to check in.'),
    (14, '숙박 및 기타', '쉬움', '와이파이 비밀번호가 뭐예요?', 'What is the Wi-Fi password?'),
    (15, '숙박 및 기타', '보통', '방에 열쇠를 두고 나왔어요.', 'I left my key inside the room.'),
    (16, '숙박 및 기타', '보통', '부대 시설이 어디에 있나요?', 'Where are the facilities?'),
    (17, '숙박 및 기타', '어려움', '영어를 할 수 있는 직원이 있나요?', 'Is there anyone who speaks English?'),
    (18, '숙박 및 기타', '어려움', '근처에 약국이 어디에 있나요?', 'Where is the nearest pharmacy?'),
    (19, '숙박 및 기타', '어려움', '배터리가 다 돼서 그러는데 충전 좀 할 수 있을까요?', 'My battery is dead. Could I charge my phone here?'),
    (20, '가격 및 쇼핑', '쉬움', '얼마예요?', 'How much is this?'),
    (21, '가격 및 쇼핑', '쉬움', '이것 주세요.', 'I''ll take this, please.'),
    (22, '가격 및 쇼핑', '보통', '깎아주세요.', 'Please give me a discount.'),
    (23, '가격 및 쇼핑', '보통', '카드 결제 돼요?', 'Can I pay by card?'),
    (24, '가격 및 쇼핑', '어려움', '영수증은 안 주셔도 괜찮습니다.', 'You don''t need to give me the receipt.'),
    (25, '가격 및 쇼핑', '어려움', '혹시 다른 사이즈나 색상도 있나요?', 'Do you have this in any other size or color?'),
    (26, '가격 및 쇼핑', '어려움', '면세 받을 수 있나요?', 'Can I get a tax refund?'),
    (27, '식당 및 주문', '쉬움', '물 주세요.', 'Water, please.'),
    (28, '식당 및 주문', '쉬움', '메뉴판 좀 주세요.', 'Menu, please.'),
    (29, '식당 및 주문', '보통', '이거 하나 주세요.', 'One of this, please.'),
    (30, '식당 및 주문', '보통', '맵지 않게 해주세요.', 'Please make it not spicy.'),
    (31, '식당 및 주문', '어려움', '추천해주실 만한 대표 메뉴가 있나요?', 'Do you have any signature dishes you can recommend?'),
    (32, '식당 및 주문', '어려움', '고기는 빼고 만들어 주실 수 있나요?', 'Can you make this without meat?'),
    (33, '식당 및 주문', '어려움', '포장 되나요?', 'Can I get this to go?'),
    (34, '식당 및 주문', '어려움', '계산서 먼저 주세요.', 'Could I have the check, please?')
ON CONFLICT (sentence_no) DO UPDATE SET
    category = EXCLUDED.category,
    level = EXCLUDED.level,
    ko = EXCLUDED.ko,
    en = EXCLUDED.en;
