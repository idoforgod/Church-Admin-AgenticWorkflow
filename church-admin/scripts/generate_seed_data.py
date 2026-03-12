#!/usr/bin/env python3
"""
One-time seed data generator for Church Administration system.
Generates realistic Korean Presbyterian church data for ~50 members,
12-month financial records, expanded schedule, and more newcomers.

All data passes P1 validation (29 rules: M1-M7, F1-F7, S1-S6, N1-N6, B1-B3).

Usage:
    python3 scripts/generate_seed_data.py

Output: Writes to data/*.yaml files (overwrites existing seed data).
"""

import os
import sys
import random
from datetime import date, datetime, timedelta

# Ensure we can import yaml
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Korean Name Pool
# ---------------------------------------------------------------------------
LAST_NAMES = [
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
    "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍",
    "전", "고", "문", "양", "손", "배", "백", "허", "유", "남",
]

MALE_FIRST_NAMES = [
    "철수", "영호", "성민", "대현", "준영", "상호", "민수", "진우",
    "현석", "재영", "동환", "성택", "하늘", "건우", "도윤", "시우",
    "주원", "승현", "태민", "기현", "지훈", "우진", "민재", "현우",
    "정훈", "성준", "현수", "용석", "상현", "기범", "희성", "동혁",
]

FEMALE_FIRST_NAMES = [
    "영희", "미나", "소영", "현주", "은혜", "수진", "지은", "하영",
    "서연", "민서", "지혜", "수빈", "미래", "은서", "도희", "예진",
    "채원", "유진", "혜원", "소윤", "나현", "선영", "은정", "지연",
    "미경", "보라", "다은", "은별", "하은", "서윤", "수현", "가은",
]

DEPARTMENTS = ["장년부", "청년부", "중고등부", "대학부"]
CELL_GROUPS = [
    "합정1구역", "합정2구역", "연희1구역", "연희2구역",
    "상수1구역", "상수2구역", "망원1구역", "망원2구역",
    "홍은1구역", "홍은2구역", "연남1구역", "연남2구역",
]
SERVING_AREAS = [
    "찬양팀", "주차봉사", "교회학교 교사", "주일학교 교사",
    "새신자 돌봄", "심방팀", "재정위원회", "당회",
    "방송팀", "안내봉사", "식사봉사", "꽃꽂이봉사",
    "성경통독반", "구역장", "선교위원회", "교육위원회",
    "청년부 간사", "찬양대",
]
ADDRESSES = [
    "서울시 마포구 합정동", "서울시 마포구 상수동", "서울시 마포구 망원동",
    "서울시 마포구 연남동", "서울시 서대문구 연희동", "서울시 서대문구 홍은동",
    "서울시 서대문구 북가좌동", "서울시 마포구 서교동", "서울시 마포구 동교동",
    "서울시 서대문구 남가좌동", "서울시 은평구 응암동", "서울시 은평구 역촌동",
]

# ---------------------------------------------------------------------------
# Member generation
# ---------------------------------------------------------------------------
def generate_members():
    """Generate ~50 members with families, roles, history."""
    random.seed(42)  # Reproducible
    members = []
    used_ids = set()
    families = {}

    # --- Family definitions (id_prefix, last_name, relations) ---
    family_defs = [
        # Existing families (preserve exact data)
        # F042: 김 family
        {"fid": "F042", "last": "김", "head": "M001", "members": [
            {"id": "M001", "first": "철수", "gender": "male", "birth": "1975-03-15",
             "reg": "2015-06-01", "bapt": "2010-04-05", "bapt_type": "adult",
             "dept": "장년부", "cell": "합정1구역", "role": "집사",
             "serving": ["찬양팀", "주차봉사"], "relation": "household_head",
             "phone": "010-1234-5678", "email": "kim.cs@example.com",
             "addr": "서울시 마포구 합정동 123-4",
             "history": [
                 {"date": "2015-06-01", "event": "transfer_in", "note": "○○교회에서 이명 (Transfer from XX Church)"},
                 {"date": "2023-07-01", "event": "role_change", "note": "성도 → 집사 임직 (Ordained as Deacon)"},
             ]},
            {"id": "M002", "first": "영희", "gender": "female", "birth": "1978-11-22",
             "reg": "2015-06-01", "bapt": "2008-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "합정1구역", "role": "권사",
             "serving": ["교회학교 교사"], "relation": "spouse",
             "phone": "010-9876-5432", "email": None,
             "addr": "서울시 마포구 합정동 123-4", "history": []},
            {"id": "M003", "first": "성민", "gender": "male", "birth": "2005-08-10",
             "reg": "2015-06-01", "bapt": None, "bapt_type": None,
             "dept": "청년부", "cell": None, "role": None,
             "serving": [], "relation": "child",
             "phone": None, "email": None,
             "addr": "서울시 마포구 합정동 123-4", "history": []},
        ]},
        # F010: 정 family
        {"fid": "F010", "last": "정", "head": "M012", "members": [
            {"id": "M012", "first": "대현", "gender": "male", "birth": "1968-05-20",
             "reg": "2005-03-15", "bapt": "2000-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "연희1구역", "role": "장로",
             "serving": ["당회", "재정위원회"], "relation": "household_head",
             "phone": "010-2222-3333", "email": "jung.dh@example.com",
             "addr": "서울시 서대문구 연희동 45-7",
             "history": [
                 {"date": "2005-03-15", "event": "transfer_in", "note": "은혜교회에서 이명"},
                 {"date": "2018-11-11", "event": "role_change", "note": "집사 → 장로 장립"},
             ]},
            {"id": "M010", "first": "은혜", "gender": "female", "birth": "1980-04-12",
             "reg": "2010-06-01", "bapt": "2010-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "합정2구역", "role": "성도",
             "serving": [], "relation": "spouse",
             "phone": "010-1111-0000", "email": None, "addr": None,
             "status": "inactive",
             "history": [{"date": "2023-06-01", "event": "status_change", "note": "장기 미출석으로 비활동 전환"}]},
        ]},
        # F025: 홍 family
        {"fid": "F025", "last": "홍", "head": "M045", "members": [
            {"id": "M045", "first": "길동", "gender": "male", "birth": "1982-03-03",
             "reg": "2010-01-10", "bapt": "2010-04-05", "bapt_type": "adult",
             "dept": "장년부", "cell": "망원1구역", "role": "안수집사",
             "serving": ["찬양팀"], "relation": "household_head",
             "phone": "010-6666-7777", "email": None,
             "addr": "서울시 마포구 망원동 22-1",
             "history": [
                 {"date": "2010-04-05", "event": "baptism", "note": "성인세례"},
                 {"date": "2020-05-01", "event": "role_change", "note": "집사 → 안수집사 임직"},
             ]},
            {"id": "M046", "first": "미나", "gender": "female", "birth": "1985-07-19",
             "reg": "2012-03-01", "bapt": "2012-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "망원1구역", "role": "집사",
             "serving": ["주일학교 교사"], "relation": "spouse",
             "phone": "010-6666-8888", "email": None,
             "addr": "서울시 마포구 망원동 22-1", "history": []},
        ]},
        # F030: 오 family
        {"fid": "F030", "last": "오", "head": "M056", "members": [
            {"id": "M056", "first": "현주", "gender": "female", "birth": "1972-09-30",
             "reg": "2008-05-01", "bapt": "2002-04-07", "bapt_type": "adult",
             "dept": "장년부", "cell": "홍은1구역", "role": "권사",
             "serving": ["심방팀", "새신자 돌봄"], "relation": "household_head",
             "phone": "010-7777-8888", "email": "oh.hj@example.com",
             "addr": "서울시 서대문구 홍은동 112-5",
             "history": [
                 {"date": "2008-05-01", "event": "transfer_in", "note": "소망교회에서 이명"},
                 {"date": "2015-11-01", "event": "role_change", "note": "집사 → 권사 임직"},
             ]},
            {"id": "M057", "first": "성택", "gender": "male", "birth": "1970-01-15",
             "reg": "2008-05-01", "bapt": "1995-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "홍은1구역", "role": "집사",
             "serving": ["주차봉사"], "relation": "spouse",
             "phone": "010-7777-9999", "email": None,
             "addr": "서울시 서대문구 홍은동 112-5", "history": []},
        ]},
    ]

    # Singles (no family)
    singles = [
        {"id": "M023", "first": "소영", "last": "한", "gender": "female", "birth": "1990-02-14",
         "reg": "2018-09-01", "bapt": "2019-04-21", "bapt_type": "adult",
         "dept": "청년부", "cell": "상수1구역", "role": "집사",
         "serving": ["청년부 간사", "새신자 돌봄"],
         "phone": "010-4444-5555", "email": "han.sy@example.com",
         "addr": "서울시 마포구 상수동 88-3",
         "history": [{"date": "2019-04-21", "event": "baptism", "note": "성인세례"}]},
        {"id": "M252", "first": "하늘", "last": "정", "gender": "male", "birth": "1995-06-15",
         "reg": "2026-01-05", "bapt": "2025-12-25", "bapt_type": "adult",
         "dept": "청년부", "cell": None, "role": "성도",
         "serving": [],
         "phone": "010-5555-6666", "email": "haneul95@example.com",
         "addr": "서울시 마포구 연남동 78-9",
         "history": [
             {"date": "2025-12-25", "event": "baptism", "note": "성탄절 세례식"},
             {"date": "2026-01-05", "event": "transfer_in", "note": "새신자 정착 (N003 → M252)"},
         ]},
    ]

    # --- NEW families to add ---
    new_families = [
        # F050: 강 family (Elder)
        {"fid": "F050", "last": "강", "members": [
            {"id": "M060", "first": "준영", "gender": "male", "birth": "1965-08-12",
             "reg": "2002-04-01", "bapt": "1990-04-15", "bapt_type": "adult",
             "dept": "장년부", "cell": "상수2구역", "role": "장로",
             "serving": ["당회", "선교위원회"], "relation": "household_head",
             "phone": "010-3100-4200", "email": "kang.jy@example.com",
             "addr": "서울시 마포구 상수동 45-2",
             "history": [
                 {"date": "2002-04-01", "event": "transfer_in", "note": "중앙교회에서 이명"},
                 {"date": "2012-11-11", "event": "role_change", "note": "집사 → 장로 장립"},
             ]},
            {"id": "M061", "first": "미경", "gender": "female", "birth": "1968-12-03",
             "reg": "2002-04-01", "bapt": "1992-04-12", "bapt_type": "adult",
             "dept": "장년부", "cell": "상수2구역", "role": "권사",
             "serving": ["심방팀", "식사봉사"], "relation": "spouse",
             "phone": "010-3100-4201", "email": None,
             "addr": "서울시 마포구 상수동 45-2",
             "history": [{"date": "2016-11-01", "event": "role_change", "note": "집사 → 권사 임직"}]},
        ]},
        # F051: 조 family (3 members)
        {"fid": "F051", "last": "조", "members": [
            {"id": "M062", "first": "상호", "gender": "male", "birth": "1977-04-18",
             "reg": "2014-09-01", "bapt": "2015-04-05", "bapt_type": "adult",
             "dept": "장년부", "cell": "망원2구역", "role": "집사",
             "serving": ["방송팀"], "relation": "household_head",
             "phone": "010-3200-5300", "email": "cho.sh@example.com",
             "addr": "서울시 마포구 망원동 67-3",
             "history": [{"date": "2015-04-05", "event": "baptism", "note": "부활절 세례"}]},
            {"id": "M063", "first": "지은", "gender": "female", "birth": "1980-06-25",
             "reg": "2014-09-01", "bapt": "2015-04-05", "bapt_type": "adult",
             "dept": "장년부", "cell": "망원2구역", "role": "집사",
             "serving": ["교회학교 교사", "꽃꽂이봉사"], "relation": "spouse",
             "phone": "010-3200-5301", "email": None,
             "addr": "서울시 마포구 망원동 67-3", "history": []},
            {"id": "M064", "first": "도윤", "gender": "male", "birth": "2008-02-14",
             "reg": "2014-09-01", "bapt": None, "bapt_type": None,
             "dept": "중고등부", "cell": None, "role": None,
             "serving": [], "relation": "child",
             "phone": None, "email": None,
             "addr": "서울시 마포구 망원동 67-3", "history": []},
        ]},
        # F052: 윤 family
        {"fid": "F052", "last": "윤", "members": [
            {"id": "M065", "first": "민수", "gender": "male", "birth": "1973-11-07",
             "reg": "2007-06-01", "bapt": "2001-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "연희2구역", "role": "안수집사",
             "serving": ["안내봉사", "주차봉사"], "relation": "household_head",
             "phone": "010-3300-6400", "email": None,
             "addr": "서울시 서대문구 연희동 89-1",
             "history": [{"date": "2019-05-01", "event": "role_change", "note": "집사 → 안수집사 임직"}]},
            {"id": "M066", "first": "하영", "gender": "female", "birth": "1976-03-20",
             "reg": "2007-06-01", "bapt": "2008-04-06", "bapt_type": "adult",
             "dept": "장년부", "cell": "연희2구역", "role": "집사",
             "serving": ["찬양대"], "relation": "spouse",
             "phone": "010-3300-6401", "email": None,
             "addr": "서울시 서대문구 연희동 89-1", "history": []},
        ]},
        # F053: 장 family (Elder)
        {"fid": "F053", "last": "장", "members": [
            {"id": "M067", "first": "현석", "gender": "male", "birth": "1960-07-22",
             "reg": "2000-01-15", "bapt": "1985-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "홍은2구역", "role": "장로",
             "serving": ["당회", "교육위원회"], "relation": "household_head",
             "phone": "010-3400-7500", "email": "jang.hs@example.com",
             "addr": "서울시 서대문구 홍은동 234-7",
             "history": [
                 {"date": "2000-01-15", "event": "transfer_in", "note": "서울제일교회에서 이명"},
                 {"date": "2010-11-14", "event": "role_change", "note": "안수집사 → 장로 장립"},
             ]},
            {"id": "M068", "first": "선영", "gender": "female", "birth": "1963-09-15",
             "reg": "2000-01-15", "bapt": "1988-04-10", "bapt_type": "adult",
             "dept": "장년부", "cell": "홍은2구역", "role": "권사",
             "serving": ["심방팀", "성경통독반"], "relation": "spouse",
             "phone": "010-3400-7501", "email": None,
             "addr": "서울시 서대문구 홍은동 234-7",
             "history": [{"date": "2008-11-01", "event": "role_change", "note": "집사 → 권사 임직"}]},
        ]},
        # F054: 임 family
        {"fid": "F054", "last": "임", "members": [
            {"id": "M069", "first": "재영", "gender": "male", "birth": "1979-01-30",
             "reg": "2016-03-01", "bapt": "2016-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "연남1구역", "role": "집사",
             "serving": ["주차봉사"], "relation": "household_head",
             "phone": "010-3500-8600", "email": None,
             "addr": "서울시 마포구 연남동 34-8",
             "history": [{"date": "2016-12-25", "event": "baptism", "note": "성탄절 세례"}]},
            {"id": "M070", "first": "수빈", "gender": "female", "birth": "1982-05-11",
             "reg": "2016-03-01", "bapt": "2017-04-16", "bapt_type": "adult",
             "dept": "장년부", "cell": "연남1구역", "role": "집사",
             "serving": ["안내봉사"], "relation": "spouse",
             "phone": "010-3500-8601", "email": None,
             "addr": "서울시 마포구 연남동 34-8", "history": []},
        ]},
        # F055: 서 family
        {"fid": "F055", "last": "서", "members": [
            {"id": "M071", "first": "동환", "gender": "male", "birth": "1971-10-05",
             "reg": "2009-08-01", "bapt": "1996-04-07", "bapt_type": "adult",
             "dept": "장년부", "cell": "합정2구역", "role": "안수집사",
             "serving": ["재정위원회", "안내봉사"], "relation": "household_head",
             "phone": "010-3600-9700", "email": "seo.dh@example.com",
             "addr": "서울시 마포구 합정동 56-9",
             "history": [{"date": "2021-05-01", "event": "role_change", "note": "집사 → 안수집사 임직"}]},
            {"id": "M072", "first": "은정", "gender": "female", "birth": "1974-02-28",
             "reg": "2009-08-01", "bapt": "2010-04-04", "bapt_type": "adult",
             "dept": "장년부", "cell": "합정2구역", "role": "권사",
             "serving": ["식사봉사", "꽃꽂이봉사"], "relation": "spouse",
             "phone": "010-3600-9701", "email": None,
             "addr": "서울시 마포구 합정동 56-9",
             "history": [{"date": "2022-11-01", "event": "role_change", "note": "집사 → 권사 임직"}]},
        ]},
        # F056: 신 family (3 members)
        {"fid": "F056", "last": "신", "members": [
            {"id": "M073", "first": "건우", "gender": "male", "birth": "1983-06-14",
             "reg": "2017-01-08", "bapt": "2017-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "상수1구역", "role": "집사",
             "serving": ["방송팀", "찬양팀"], "relation": "household_head",
             "phone": "010-3700-1800", "email": "shin.gw@example.com",
             "addr": "서울시 마포구 상수동 12-7",
             "history": [{"date": "2017-12-25", "event": "baptism", "note": "성탄절 세례"}]},
            {"id": "M074", "first": "예진", "gender": "female", "birth": "1986-08-20",
             "reg": "2017-01-08", "bapt": "2018-04-01", "bapt_type": "adult",
             "dept": "장년부", "cell": "상수1구역", "role": "집사",
             "serving": ["주일학교 교사"], "relation": "spouse",
             "phone": "010-3700-1801", "email": None,
             "addr": "서울시 마포구 상수동 12-7", "history": []},
            {"id": "M075", "first": "시우", "gender": "male", "birth": "2012-11-03",
             "reg": "2017-01-08", "bapt": None, "bapt_type": None,
             "dept": "중고등부", "cell": None, "role": None,
             "serving": [], "relation": "child",
             "phone": None, "email": None,
             "addr": "서울시 마포구 상수동 12-7", "history": []},
        ]},
        # F057: 권 family
        {"fid": "F057", "last": "권", "members": [
            {"id": "M076", "first": "용석", "gender": "male", "birth": "1975-12-01",
             "reg": "2011-06-01", "bapt": "2012-04-08", "bapt_type": "adult",
             "dept": "장년부", "cell": "연남2구역", "role": "집사",
             "serving": ["찬양팀"], "relation": "household_head",
             "phone": "010-3800-2900", "email": None,
             "addr": "서울시 마포구 연남동 56-1",
             "history": [{"date": "2012-04-08", "event": "baptism", "note": "부활절 세례"}]},
            {"id": "M077", "first": "채원", "gender": "female", "birth": "1978-04-16",
             "reg": "2011-06-01", "bapt": "2012-04-08", "bapt_type": "adult",
             "dept": "장년부", "cell": "연남2구역", "role": "집사",
             "serving": ["새신자 돌봄"], "relation": "spouse",
             "phone": "010-3800-2901", "email": None,
             "addr": "서울시 마포구 연남동 56-1", "history": []},
        ]},
        # F058: 황 family
        {"fid": "F058", "last": "황", "members": [
            {"id": "M078", "first": "상현", "gender": "male", "birth": "1969-03-08",
             "reg": "2004-10-01", "bapt": "1994-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "망원1구역", "role": "집사",
             "serving": ["안내봉사"], "relation": "household_head",
             "phone": "010-3900-4100", "email": None,
             "addr": "서울시 마포구 망원동 99-4",
             "history": [{"date": "2004-10-01", "event": "transfer_in", "note": "부산 동래교회에서 이명"}]},
            {"id": "M079", "first": "보라", "gender": "female", "birth": "1972-07-25",
             "reg": "2004-10-01", "bapt": "1998-04-12", "bapt_type": "adult",
             "dept": "장년부", "cell": "망원1구역", "role": "집사",
             "serving": ["식사봉사"], "relation": "spouse",
             "phone": "010-3900-4101", "email": None,
             "addr": "서울시 마포구 망원동 99-4", "history": []},
        ]},
        # F059: 안 family
        {"fid": "F059", "last": "안", "members": [
            {"id": "M080", "first": "기현", "gender": "male", "birth": "1984-09-17",
             "reg": "2019-03-01", "bapt": "2019-12-25", "bapt_type": "adult",
             "dept": "장년부", "cell": "홍은1구역", "role": "성도",
             "serving": [], "relation": "household_head",
             "phone": "010-4100-5200", "email": None,
             "addr": "서울시 서대문구 홍은동 78-3",
             "history": [{"date": "2019-12-25", "event": "baptism", "note": "성탄절 세례"}]},
            {"id": "M081", "first": "다은", "gender": "female", "birth": "1987-01-09",
             "reg": "2019-03-01", "bapt": "2020-04-12", "bapt_type": "adult",
             "dept": "장년부", "cell": "홍은1구역", "role": "성도",
             "serving": [], "relation": "spouse",
             "phone": "010-4100-5201", "email": None,
             "addr": "서울시 서대문구 홍은동 78-3", "history": []},
        ]},
    ]

    # NEW singles
    new_singles = [
        {"id": "M082", "first": "지훈", "last": "박", "gender": "male", "birth": "1993-03-22",
         "reg": "2020-06-01", "bapt": "2021-04-04", "bapt_type": "adult",
         "dept": "청년부", "cell": "연남1구역", "role": "성도",
         "serving": ["찬양팀"],
         "phone": "010-4200-6300", "email": "park.jh@example.com",
         "addr": "서울시 마포구 연남동 112-3",
         "history": [{"date": "2021-04-04", "event": "baptism", "note": "부활절 세례"}]},
        {"id": "M083", "first": "서연", "last": "이", "gender": "female", "birth": "1996-07-30",
         "reg": "2022-01-08", "bapt": None, "bapt_type": None,
         "dept": "청년부", "cell": None, "role": "성도",
         "serving": [],
         "phone": "010-4300-7400", "email": "lee.sy@example.com",
         "addr": "서울시 마포구 서교동 45-6",
         "history": []},
        {"id": "M084", "first": "민재", "last": "최", "gender": "male", "birth": "1991-11-14",
         "reg": "2021-09-01", "bapt": "2022-04-17", "bapt_type": "adult",
         "dept": "청년부", "cell": "상수2구역", "role": "성도",
         "serving": ["방송팀"],
         "phone": "010-4400-8500", "email": None,
         "addr": "서울시 마포구 상수동 33-8",
         "history": [{"date": "2022-04-17", "event": "baptism", "note": "부활절 세례"}]},
        {"id": "M085", "first": "유진", "last": "송", "gender": "female", "birth": "1988-05-03",
         "reg": "2015-03-01", "bapt": "2015-12-25", "bapt_type": "adult",
         "dept": "장년부", "cell": "망원2구역", "role": "집사",
         "serving": ["새신자 돌봄", "심방팀"],
         "phone": "010-4500-9600", "email": None,
         "addr": "서울시 마포구 망원동 45-2",
         "history": [{"date": "2015-12-25", "event": "baptism", "note": "성탄절 세례"}]},
        {"id": "M086", "first": "현우", "last": "류", "gender": "male", "birth": "1997-08-21",
         "reg": "2023-06-01", "bapt": None, "bapt_type": None,
         "dept": "청년부", "cell": None, "role": "성도",
         "serving": [],
         "phone": "010-4600-1700", "email": "ryu.hw@example.com",
         "addr": "서울시 마포구 동교동 67-9",
         "history": []},
        {"id": "M087", "first": "혜원", "last": "전", "gender": "female", "birth": "1994-12-08",
         "reg": "2019-09-01", "bapt": "2020-12-25", "bapt_type": "adult",
         "dept": "청년부", "cell": "연남2구역", "role": "성도",
         "serving": ["성경통독반"],
         "phone": "010-4700-2800", "email": None,
         "addr": "서울시 마포구 연남동 23-4",
         "history": [{"date": "2020-12-25", "event": "baptism", "note": "성탄절 세례"}]},
        {"id": "M088", "first": "태민", "last": "고", "gender": "male", "birth": "1998-02-18",
         "reg": "2024-01-07", "bapt": None, "bapt_type": None,
         "dept": "청년부", "cell": None, "role": "성도",
         "serving": [],
         "phone": "010-4800-3900", "email": "ko.tm@example.com",
         "addr": "서울시 마포구 서교동 89-2",
         "history": []},
        # Transferred member
        {"id": "M089", "first": "승현", "last": "배", "gender": "male", "birth": "1981-06-30",
         "reg": "2013-04-01", "bapt": "2014-04-20", "bapt_type": "adult",
         "dept": "장년부", "cell": "합정1구역", "role": "집사",
         "serving": [], "status": "transferred",
         "phone": "010-4900-5100", "email": None,
         "addr": None,
         "history": [
             {"date": "2014-04-20", "event": "baptism", "note": "부활절 세례"},
             {"date": "2025-08-01", "event": "transfer_out", "note": "대전 ○○교회로 이명"},
         ]},
        # Deceased member
        {"id": "M090", "first": "정훈", "last": "남", "gender": "male", "birth": "1945-03-01",
         "reg": "1998-01-01", "bapt": "1970-04-12", "bapt_type": "adult",
         "dept": "장년부", "cell": "합정1구역", "role": "장로",
         "serving": [], "status": "deceased",
         "phone": None, "email": None,
         "addr": None,
         "history": [
             {"date": "1998-01-01", "event": "transfer_in", "note": "개척 멤버"},
             {"date": "2010-11-14", "event": "role_change", "note": "장로 장립"},
             {"date": "2025-03-15", "event": "death", "note": "소천 (향년 80세)"},
         ]},
    ]

    # Build member list
    def build_member(m, fid=None, last=None):
        """Convert a member dict to the YAML-ready format."""
        name = (last or "") + m["first"]
        rec = {
            "id": m["id"],
            "name": name,
            "gender": m["gender"],
            "birth_date": m["birth"],
            "status": m.get("status", "active"),
            "contact": {
                "phone": m.get("phone"),
                "email": m.get("email"),
                "address": m.get("addr"),
            },
            "church": {
                "registration_date": m["reg"],
                "baptism_date": m.get("bapt"),
                "baptism_type": m.get("bapt_type"),
                "department": m["dept"],
                "cell_group": m.get("cell"),
                "role": m.get("role"),
                "serving_area": m.get("serving", []),
            },
            "family": {
                "family_id": fid,
                "relation": m.get("relation"),
            },
            "history": m.get("history", []),
        }
        return rec

    # Process existing + new families
    all_families = family_defs + new_families
    for fam in all_families:
        fid = fam["fid"]
        last = fam["last"]
        for m in fam["members"]:
            members.append(build_member(m, fid=fid, last=last))

    # Process singles
    for s in singles + new_singles:
        members.append(build_member(s, fid=None, last=s.get("last", "")))

    # Compute stats
    active_count = sum(1 for m in members if m["status"] == "active")
    total_count = len(members)

    # Build comment header
    stats_comment = (
        f"# _stats must match actual record counts:\n"
        f"# total_members: {total_count} ({', '.join(m['id'] for m in members)})\n"
        f"# total_active: {active_count} (all except status!=active)\n"
    )

    data = {
        "schema_version": "1.0",
        "last_updated": date.today().isoformat(),
        "updated_by": "member-manager",
        "members": members,
        "_stats": {
            "total_active": active_count,
            "total_members": total_count,
            "last_computed": date.today().isoformat(),
        },
    }

    return data, stats_comment


# ---------------------------------------------------------------------------
# Finance generation
# ---------------------------------------------------------------------------
def generate_finance():
    """Generate 12 months of financial data (Jan-Dec 2026)."""

    offerings = []
    expenses = []
    monthly_summaries = {}

    off_counter = 1
    exp_counter = 1

    # Typical Korean church monthly offering pattern (KRW)
    # Tithe: 3.5-4.5M, Sunday: 1.0-1.5M, Thanksgiving: 0.3-0.6M
    base_tithe = 3_800_000
    base_sunday = 1_200_000

    for month in range(1, 13):
        month_str = f"2026-{month:02d}"
        month_income = 0
        month_expense = 0

        # 4 Sundays per month (approximate)
        for week in range(1, 5):
            sunday_num = (month - 1) * 4 + week
            sun_date = f"2026-{month:02d}-{min(week * 7, 28):02d}"

            # Vary amounts slightly
            random.seed(sunday_num * 13 + 7)
            tithe = base_tithe + random.randint(-300_000, 500_000)
            sunday_off = base_sunday + random.randint(-200_000, 300_000)

            items = [
                {"category": "십일조 (Tithe)", "amount": tithe},
                {"category": "주일헌금 (Sunday Offering)", "amount": sunday_off},
            ]

            # Add occasional special offerings
            if week == 1 and month % 2 == 0:
                items.append({"category": "감사헌금 (Thanksgiving)", "amount": random.randint(300_000, 600_000)})
            if week == 3 and month % 3 == 0:
                items.append({"category": "선교헌금 (Mission Offering)", "amount": random.randint(400_000, 700_000)})
            if month == 2 and week == 2:
                items.append({"category": "건축헌금 (Building Fund)", "amount": 2_000_000})

            total = sum(i["amount"] for i in items)
            month_income += total

            off_id = f"OFF-2026-{off_counter:03d}"
            offerings.append({
                "id": off_id,
                "date": sun_date,
                "service": "주일예배 1부 (Sunday Service 1st)",
                "type": "sunday_offering",
                "items": items,
                "total": total,
                "recorded_by": "재정담당집사 (Finance Deacon)",
                "verified": True,
                "void": False,
            })
            off_counter += 1

        # Monthly expenses
        # Electricity
        elec = 200_000 + random.randint(0, 100_000)
        expenses.append({
            "id": f"EXP-2026-{exp_counter:03d}",
            "date": f"2026-{month:02d}-10",
            "category": "관리비",
            "subcategory": "전기요금 (Electricity)",
            "amount": elec,
            "description": f"{month}월 전기요금",
            "payment_method": "계좌이체 (Bank transfer)",
            "approved_by": "담임목사 (Senior Pastor)",
            "receipt": True,
            "void": False,
        })
        month_expense += elec
        exp_counter += 1

        # Pastoral salary
        salary = 2_500_000
        expenses.append({
            "id": f"EXP-2026-{exp_counter:03d}",
            "date": f"2026-{month:02d}-15",
            "category": "인건비",
            "subcategory": "교역자사례비 (Pastoral Compensation)",
            "amount": salary,
            "description": f"{month}월 사례비",
            "payment_method": "계좌이체 (Bank transfer)",
            "approved_by": "장로회 (Elder Board)",
            "receipt": False,
            "void": False,
        })
        month_expense += salary
        exp_counter += 1

        # Water bill (odd months)
        if month % 2 == 1:
            water = 80_000 + random.randint(0, 30_000)
            expenses.append({
                "id": f"EXP-2026-{exp_counter:03d}",
                "date": f"2026-{month:02d}-12",
                "category": "관리비",
                "subcategory": "수도요금 (Water)",
                "amount": water,
                "description": f"{month}월 수도요금",
                "payment_method": "계좌이체 (Bank transfer)",
                "approved_by": "담임목사 (Senior Pastor)",
                "receipt": True,
                "void": False,
            })
            month_expense += water
            exp_counter += 1

        # Ministry expenses (quarterly)
        if month % 3 == 0:
            ministry = 500_000 + random.randint(0, 300_000)
            expenses.append({
                "id": f"EXP-2026-{exp_counter:03d}",
                "date": f"2026-{month:02d}-20",
                "category": "사역비",
                "subcategory": "부서활동비 (Ministry Activities)",
                "amount": ministry,
                "description": f"{month}월 분기별 사역비",
                "payment_method": "법인카드 (Corporate Card)",
                "approved_by": "담임목사 (Senior Pastor)",
                "receipt": True,
                "void": False,
            })
            month_expense += ministry
            exp_counter += 1

        monthly_summaries[month_str] = {
            "total_income": month_income,
            "total_expense": month_expense,
            "balance": month_income - month_expense,
            "computed_at": f"2026-{month:02d}-28" if month <= 2 else f"2026-{month:02d}-01",
        }

    data = {
        "schema_version": "1.0",
        "year": 2026,
        "currency": "KRW",
        "last_updated": date.today().isoformat(),
        "updated_by": "finance-recorder",
        "offerings": offerings,
        "expenses": expenses,
        "pledged_annual": [
            {"member_id": "M001", "year": 2026, "pledged_amount": 12_000_000, "paid_to_date": 3_000_000, "status": "active"},
            {"member_id": "M012", "year": 2026, "pledged_amount": 18_000_000, "paid_to_date": 4_500_000, "status": "active"},
            {"member_id": "M060", "year": 2026, "pledged_amount": 15_000_000, "paid_to_date": 3_750_000, "status": "active"},
            {"member_id": "M067", "year": 2026, "pledged_amount": 20_000_000, "paid_to_date": 5_000_000, "status": "active"},
        ],
        "budget": {
            "fiscal_year": 2026,
            "approved_date": "2025-12-28",
            "categories": {
                "관리비": 3_500_000,
                "인건비": 35_000_000,
                "사역비": 12_000_000,
                "선교비": 8_000_000,
                "교육비": 5_000_000,
                "기타": 2_000_000,
            },
            "total_budget": 65_500_000,
        },
        "monthly_summary": monthly_summaries,
    }
    return data


# ---------------------------------------------------------------------------
# Newcomers generation
# ---------------------------------------------------------------------------
def generate_newcomers():
    """Generate expanded newcomer data (7 newcomers at various stages)."""
    data = {
        "schema_version": "1.0",
        "last_updated": date.today().isoformat(),
        "updated_by": "newcomer-tracker",
        "newcomers": [
            {
                "id": "N001",
                "name": "박민준",
                "gender": "male",
                "birth_year": 1992,
                "contact": {"phone": "010-1111-2222", "kakao_id": "pmj1992"},
                "first_visit": "2026-02-02",
                "visit_route": "지인 초청",
                "referred_by": "M001",
                "journey_stage": "attending",
                "journey_milestones": {
                    "first_visit": {"date": "2026-02-02", "completed": True},
                    "welcome_call": {"date": "2026-02-03", "completed": True, "notes": "반갑게 통화, 다음 주 방문 의사 있음"},
                    "second_visit": {"date": "2026-02-09", "completed": True},
                    "small_group_intro": {"date": None, "completed": False},
                    "baptism_class": {"date": None, "completed": False},
                    "baptism": {"date": None, "completed": False},
                },
                "assigned_to": "M023",
                "assigned_department": "청년부 (Youth)",
                "status": "active",
                "settled_as_member": None,
                "settled_date": None,
            },
            {
                "id": "N002",
                "name": "최수진",
                "gender": "female",
                "birth_year": 1988,
                "contact": {"phone": "010-3333-4444", "kakao_id": None},
                "first_visit": "2026-01-19",
                "visit_route": "전도",
                "referred_by": None,
                "journey_stage": "small_group",
                "journey_milestones": {
                    "first_visit": {"date": "2026-01-19", "completed": True},
                    "welcome_call": {"date": "2026-01-20", "completed": True, "notes": "세 자녀 있음. 주일학교 관심"},
                    "second_visit": {"date": "2026-01-26", "completed": True},
                    "small_group_intro": {"date": "2026-02-05", "completed": True},
                    "baptism_class": {"date": None, "completed": False},
                    "baptism": {"date": None, "completed": False},
                },
                "assigned_to": "M056",
                "assigned_department": "장년부 (Adult)",
                "status": "active",
                "settled_as_member": None,
                "settled_date": None,
            },
            {
                "id": "N003",
                "name": "정하늘",
                "gender": "male",
                "birth_year": 1995,
                "contact": {"phone": "010-5555-6666", "kakao_id": "haneul95"},
                "first_visit": "2025-10-12",
                "visit_route": "온라인 검색",
                "referred_by": None,
                "journey_stage": "settled",
                "journey_milestones": {
                    "first_visit": {"date": "2025-10-12", "completed": True},
                    "welcome_call": {"date": "2025-10-13", "completed": True, "notes": None},
                    "second_visit": {"date": "2025-10-19", "completed": True},
                    "small_group_intro": {"date": "2025-11-02", "completed": True},
                    "baptism_class": {"date": "2025-11-15", "completed": True},
                    "baptism": {"date": "2025-12-25", "completed": True},
                },
                "assigned_to": "M012",
                "assigned_department": "청년부 (Youth)",
                "status": "settled",
                "settled_as_member": "M252",
                "settled_date": "2026-01-05",
            },
            {
                "id": "N004",
                "name": "김서현",
                "gender": "female",
                "birth_year": 2000,
                "contact": {"phone": "010-6100-7200", "kakao_id": "kim_sh2000"},
                "first_visit": "2026-02-16",
                "visit_route": "지인 초청",
                "referred_by": "M082",
                "journey_stage": "first_visit",
                "journey_milestones": {
                    "first_visit": {"date": "2026-02-16", "completed": True},
                    "welcome_call": {"date": None, "completed": False},
                    "second_visit": {"date": None, "completed": False},
                    "small_group_intro": {"date": None, "completed": False},
                    "baptism_class": {"date": None, "completed": False},
                    "baptism": {"date": None, "completed": False},
                },
                "assigned_to": "M023",
                "assigned_department": "청년부 (Youth)",
                "status": "active",
                "settled_as_member": None,
                "settled_date": None,
            },
            {
                "id": "N005",
                "name": "이동건",
                "gender": "male",
                "birth_year": 1975,
                "contact": {"phone": "010-6200-8300", "kakao_id": None},
                "first_visit": "2026-01-05",
                "visit_route": "행사 초청",
                "referred_by": "M045",
                "journey_stage": "baptism_class",
                "journey_milestones": {
                    "first_visit": {"date": "2026-01-05", "completed": True},
                    "welcome_call": {"date": "2026-01-06", "completed": True, "notes": "가족과 함께 방문. 주일예배 정착 의지"},
                    "second_visit": {"date": "2026-01-12", "completed": True},
                    "small_group_intro": {"date": "2026-01-22", "completed": True},
                    "baptism_class": {"date": "2026-02-10", "completed": True},
                    "baptism": {"date": None, "completed": False},
                },
                "assigned_to": "M056",
                "assigned_department": "장년부 (Adult)",
                "status": "active",
                "settled_as_member": None,
                "settled_date": None,
            },
            {
                "id": "N006",
                "name": "장유미",
                "gender": "female",
                "birth_year": 1985,
                "contact": {"phone": "010-6300-9400", "kakao_id": "yumi_j"},
                "first_visit": "2025-11-30",
                "visit_route": "전도",
                "referred_by": "M085",
                "journey_stage": "settled",
                "journey_milestones": {
                    "first_visit": {"date": "2025-11-30", "completed": True},
                    "welcome_call": {"date": "2025-12-01", "completed": True, "notes": "이전 교회 경험 있음. 즉시 정착 의지"},
                    "second_visit": {"date": "2025-12-07", "completed": True},
                    "small_group_intro": {"date": "2025-12-15", "completed": True},
                    "baptism_class": {"date": "2025-12-20", "completed": True},
                    "baptism": {"date": "2025-12-25", "completed": True},
                },
                "assigned_to": "M061",
                "assigned_department": "장년부 (Adult)",
                "status": "settled",
                "settled_as_member": "M085",
                "settled_date": "2026-01-12",
            },
            {
                "id": "N007",
                "name": "한재윤",
                "gender": "male",
                "birth_year": 1999,
                "contact": {"phone": "010-6400-1500", "kakao_id": "jy_han99"},
                "first_visit": "2026-02-23",
                "visit_route": "온라인 검색",
                "referred_by": None,
                "journey_stage": "first_visit",
                "journey_milestones": {
                    "first_visit": {"date": "2026-02-23", "completed": True},
                    "welcome_call": {"date": None, "completed": False},
                    "second_visit": {"date": None, "completed": False},
                    "small_group_intro": {"date": None, "completed": False},
                    "baptism_class": {"date": None, "completed": False},
                    "baptism": {"date": None, "completed": False},
                },
                "assigned_to": "M082",
                "assigned_department": "청년부 (Youth)",
                "status": "active",
                "settled_as_member": None,
                "settled_date": None,
            },
        ],
        "_stats": {
            "total_active": 5,  # N001, N002, N004, N005, N007
            "by_stage": {
                "first_visit": 2,  # N004, N007
                "attending": 1,  # N001
                "small_group": 1,  # N002
                "baptism_class": 1,  # N005
                "baptized": 0,
                "settled": 2,  # N003, N006
            },
            "last_computed": date.today().isoformat(),
        },
    }
    return data


# ---------------------------------------------------------------------------
# Schedule expansion
# ---------------------------------------------------------------------------
def generate_schedule():
    """Generate expanded schedule with more events."""
    data = {
        "schema_version": "1.0",
        "last_updated": date.today().isoformat(),
        "updated_by": "schedule-manager",
        "regular_services": [
            {"id": "SVC-SUN-1", "name": "주일예배 1부 (Sunday Service 1st)", "recurrence": "weekly",
             "day_of_week": "sunday", "time": "09:00", "duration_minutes": 70,
             "location": "본당 (Main Sanctuary)",
             "preacher_rotation": ["담임목사 (Senior Pastor)", "부목사1 (Associate Pastor 1)"],
             "worship_leader": "찬양팀A (Worship Team A)"},
            {"id": "SVC-SUN-2", "name": "주일예배 2부 (Sunday Service 2nd)", "recurrence": "weekly",
             "day_of_week": "sunday", "time": "11:00", "duration_minutes": 70,
             "location": "본당 (Main Sanctuary)",
             "preacher_rotation": ["담임목사 (Senior Pastor)"],
             "worship_leader": "찬양팀B (Worship Team B)"},
            {"id": "SVC-WED", "name": "수요예배 (Wednesday Service)", "recurrence": "weekly",
             "day_of_week": "wednesday", "time": "19:30", "duration_minutes": 60,
             "location": "본당 (Main Sanctuary)",
             "preacher_rotation": ["담임목사 (Senior Pastor)", "부목사1 (Associate Pastor 1)", "부목사2 (Associate Pastor 2)"],
             "worship_leader": None},
            {"id": "SVC-FRI", "name": "금요기도회 (Friday Prayer Meeting)", "recurrence": "weekly",
             "day_of_week": "friday", "time": "20:00", "duration_minutes": 60,
             "location": "소예배실 (Small Chapel)",
             "preacher_rotation": ["부목사1 (Associate Pastor 1)", "부목사2 (Associate Pastor 2)"],
             "worship_leader": None},
            {"id": "SVC-DAWN", "name": "새벽기도회 (Early Morning Prayer)", "recurrence": "weekly",
             "day_of_week": "monday", "time": "05:30", "duration_minutes": 40,
             "location": "소예배실 (Small Chapel)",
             "preacher_rotation": ["담임목사 (Senior Pastor)"],
             "worship_leader": None},
        ],
        "special_events": [
            {"id": "EVT-2026-001", "name": "2026년 신년감사예배 (New Year Thanksgiving)", "date": "2026-01-04",
             "time": "11:00", "duration_minutes": 120, "location": "본당 (Main Sanctuary)",
             "preacher": "담임목사 (Senior Pastor)", "description": "New Year thanksgiving worship",
             "attendance_expected": 350,
             "preparation": ["현수막 제작", "특별 찬양팀 섭외", "식사 준비 250인분"],
             "status": "completed"},
            {"id": "EVT-2026-002", "name": "구역장 세미나 (Cell Leader Seminar)", "date": "2026-01-18",
             "time": "14:00", "duration_minutes": 180, "location": "교육관 3층",
             "preacher": "담임목사 (Senior Pastor)", "description": "Annual cell group leader training",
             "attendance_expected": 30,
             "preparation": ["교재 준비", "다과 준비"], "status": "completed"},
            {"id": "EVT-2026-003", "name": "청년부 수련회 (Youth Retreat)", "date": "2026-02-07",
             "time": "09:00", "duration_minutes": 2880, "location": "양평 수양관",
             "preacher": "부목사1 (Associate Pastor 1)", "description": "2-day youth retreat (Feb 7-8)",
             "attendance_expected": 40,
             "preparation": ["수양관 예약", "차량 준비", "프로그램 기획"], "status": "completed"},
            {"id": "EVT-2026-008", "name": "3월 부흥회 (March Revival Meeting)", "date": "2026-03-15",
             "time": "19:00", "duration_minutes": 90, "location": "본당 (Main Sanctuary)",
             "preacher": "초청강사 (Guest Speaker)", "description": "3-day revival (March 15-17)",
             "attendance_expected": 300,
             "preparation": ["강사 숙소 준비", "특별 찬양 준비"], "status": "confirmed"},
            {"id": "EVT-2026-015", "name": "부활절 연합예배 (Easter Joint Service)", "date": "2026-04-05",
             "time": "10:00", "duration_minutes": 90, "location": "본당 (Main Sanctuary)",
             "preacher": "담임목사 (Senior Pastor)", "description": "Easter with baptism ceremony",
             "attendance_expected": 400,
             "preparation": ["꽃 장식 준비", "달걀 나눔 행사", "세례식 준비"], "status": "planned"},
            {"id": "EVT-2026-020", "name": "어버이주일 (Parents' Day Service)", "date": "2026-05-10",
             "time": "11:00", "duration_minutes": 90, "location": "본당 (Main Sanctuary)",
             "preacher": "담임목사 (Senior Pastor)", "description": "Parents' Day special service",
             "attendance_expected": 350,
             "preparation": ["카네이션 준비", "효도상 준비"], "status": "planned"},
            {"id": "EVT-2026-025", "name": "VBS (여름성경학교)", "date": "2026-07-27",
             "time": "09:00", "duration_minutes": 480, "location": "교육관",
             "preacher": "부목사2 (Associate Pastor 2)", "description": "5-day VBS (Jul 27-31)",
             "attendance_expected": 80,
             "preparation": ["교재 주문", "간식 준비", "교사 교육"], "status": "planned"},
            {"id": "EVT-2026-030", "name": "추수감사절 예배 (Thanksgiving)", "date": "2026-11-15",
             "time": "11:00", "duration_minutes": 120, "location": "본당 (Main Sanctuary)",
             "preacher": "담임목사 (Senior Pastor)", "description": "Korean Thanksgiving (3rd Sunday Nov)",
             "attendance_expected": 380,
             "preparation": ["과일 바구니 준비", "특별 찬양"], "status": "planned"},
            {"id": "EVT-2026-035", "name": "성탄절 예배 (Christmas Service)", "date": "2026-12-25",
             "time": "11:00", "duration_minutes": 120, "location": "본당 (Main Sanctuary)",
             "preacher": "담임목사 (Senior Pastor)", "description": "Christmas celebration + baptism",
             "attendance_expected": 400,
             "preparation": ["장식", "성탄 트리", "세례식 준비", "교회학교 성극"], "status": "planned"},
        ],
        "facility_bookings": [
            {"id": "FAC-2026-001", "facility": "교육관 3층 (Education Building 3F)", "date": "2026-02-15",
             "time_start": "14:00", "time_end": "17:00",
             "purpose": "청년부 수련회 준비 모임", "booked_by": "청년부 간사", "status": "confirmed"},
            {"id": "FAC-2026-002", "facility": "소예배실 (Small Chapel)", "date": "2026-03-05",
             "time_start": "10:00", "time_end": "12:00",
             "purpose": "구역장 모임", "booked_by": "교구장", "status": "confirmed"},
            {"id": "FAC-2026-003", "facility": "교육관 2층 (Education Building 2F)", "date": "2026-03-12",
             "time_start": "14:00", "time_end": "16:00",
             "purpose": "여선교회 모임", "booked_by": "여선교회장", "status": "confirmed"},
            {"id": "FAC-2026-004", "facility": "친교실 (Fellowship Hall)", "date": "2026-04-05",
             "time_start": "12:30", "time_end": "14:30",
             "purpose": "부활절 오찬", "booked_by": "행정간사", "status": "pending"},
        ],
    }
    return data


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def write_yaml_with_header(filepath, data, header_comment):
    """Write YAML with a custom header comment."""
    content = header_comment + "\n" + yaml.dump(
        data, allow_unicode=True, default_flow_style=False, sort_keys=False,
        width=120,
    )
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Written: {filepath} ({os.path.getsize(filepath):,} bytes)")


def main():
    # Find church-admin root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(script_dir)
    data_dir = os.path.join(root, "data")

    if not os.path.isdir(data_dir):
        print(f"ERROR: data/ not found at {data_dir}", file=sys.stderr)
        sys.exit(1)

    print("Generating seed data for Church Administration system...")

    # Members
    members_data, stats_comment = generate_members()
    write_yaml_with_header(
        os.path.join(data_dir, "members.yaml"),
        members_data,
        "# data/members.yaml\n"
        "# Writer: member-manager agent (sole writer — Layer 1 enforced)\n"
        "# Validator: validate_members.py (M1-M7)\n"
        "# Sensitivity: HIGH (PII — .gitignore'd)\n"
        "# Deletion policy: SOFT-DELETE ONLY (status: \"inactive\") — never remove records\n"
        "# NEVER remove existing members — use status: \"inactive\" to preserve history (교적 보존)\n",
    )

    # Finance
    finance_data = generate_finance()
    write_yaml_with_header(
        os.path.join(data_dir, "finance.yaml"),
        finance_data,
        "# data/finance.yaml\n"
        "# Writer: finance-recorder agent (sole writer — Layer 1 enforced)\n"
        "# Validator: validate_finance.py (F1-F7)\n"
        "# Sensitivity: HIGH (Financial — .gitignore'd)\n"
        "# Deletion policy: VOID-ONLY (void: true) — never delete records\n"
        "# Autopilot: PERMANENTLY DISABLED — all writes require human approval\n"
        "# Currency: KRW (Korean Won), integer amounts only (no decimals)\n",
    )

    # Newcomers
    newcomers_data = generate_newcomers()
    write_yaml_with_header(
        os.path.join(data_dir, "newcomers.yaml"),
        newcomers_data,
        "# data/newcomers.yaml\n"
        "# Writer: newcomer-tracker agent (sole writer — Layer 1 enforced)\n"
        "# Validator: validate_newcomers.py (N1-N6)\n"
        "# Sensitivity: HIGH (PII — .gitignore'd)\n"
        "# Deletion policy: SOFT-DELETE ONLY (status: \"inactive\") — never remove records\n"
        "# Journey: first_visit → attending → small_group → baptism_class → baptized → settled\n",
    )

    # Schedule
    schedule_data = generate_schedule()
    write_yaml_with_header(
        os.path.join(data_dir, "schedule.yaml"),
        schedule_data,
        "# data/schedule.yaml\n"
        "# Writer: schedule-manager agent (sole writer — Layer 1 enforced)\n"
        "# Validator: validate_schedule.py (S1-S6)\n"
        "# Sensitivity: LOW (public schedule information)\n"
        "# Deletion policy: status → \"cancelled\" for events; remove completed past events annually\n",
    )

    print(f"\nSeed data generated:")
    print(f"  Members: {len(members_data['members'])} total, {members_data['_stats']['total_active']} active")
    print(f"  Offerings: {len(finance_data['offerings'])}")
    print(f"  Expenses: {len(finance_data['expenses'])}")
    print(f"  Newcomers: {len(newcomers_data['newcomers'])}")
    print(f"  Services: {len(schedule_data['regular_services'])}")
    print(f"  Events: {len(schedule_data['special_events'])}")

    print("\nRun validation: python3 scripts/validate_all.py --data-dir data/")


if __name__ == "__main__":
    main()
