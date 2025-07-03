from flask import Flask, request, jsonify, send_file, send_from_directory, session, Response
from flask.typing import ResponseReturnValue
from typing import Union, Tuple
import os
import requests
from dotenv import load_dotenv
from utils import use_ollama, get_hf_response, get_ollama_response, check_ollama_status
from language import detect_language, wants_language_reply, get_interest_question
import json
from extended_features import save_chat_history, generate_map_links, PDFGenerator, load_chat_history, format_schedule_places
import traceback
import warnings
import random
import threading
import hashlib
import re
from datetime import datetime, timedelta
from transport import extract_bus_info, get_bus_info, get_bus_route_info, extract_subway_info, get_subway_info, get_station_info, get_line_info, get_route_info, get_congestion_info, get_delay_info, transport_chat_handler, print_env_keys, get_ktx_info
# travel.py의 extract_city_from_message는 더 이상 사용하지 않음 (app.py에 통합됨)
from llm import get_ollama_response, get_hf_response


warnings.filterwarnings("ignore", message="missing glyph.*")

load_dotenv()
print_env_keys()  # 앱 시작 시 .env의 주요 API 키를 콘솔에 출력

def load_enhanced_prompt_with_real_data():
    """실제 레스토랑 데이터를 포함한 향상된 프롬프트 로드"""
    try:
        with open("../travel-bot/enhanced_prompt_with_real_data.json", "r", encoding="utf-8") as f:
            prompt_data = json.load(f)
            return prompt_data.get("system_prompt", "")
    except FileNotFoundError:
        print("⚠️ enhanced_prompt_with_real_data.json 파일을 찾을 수 없습니다. 기본 프롬프트를 사용합니다.")
        return ""
    except Exception as e:
        print(f"⚠️ 프롬프트 로드 중 오류 발생: {e}")
        return ""

# 실제 레스토랑 데이터 기반 프롬프트 로드
ENHANCED_SYSTEM_PROMPT = load_enhanced_prompt_with_real_data()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")  # 세션용 시크릿키

# 응답 캐시 (메모리 기반)
response_cache = {}

# 필수 정보 항목
REQUIRED_FIELDS = [
    ("departure", "출발하실 도시나 국가가 어디인가요?"),
    ("destination", "여행하실 도시나 국가는 어디인가요?"),
    ("duration", "몇 박 며칠 일정으로 계획하고 계신가요?"),
    ("interest", "여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)")
]

# 국가 목록 (도시를 묻기 위한 구분용)
COUNTRIES = [
    "한국", "대한민국", "korea", "south korea", "japan", "일본", "china", "중국", 
    "usa", "미국", "united states", "america", "uk", "영국", "united kingdom", 
    "france", "프랑스", "germany", "독일", "italy", "이탈리아", "spain", "스페인",
    "thailand", "태국", "vietnam", "베트남", "singapore", "싱가포르", "malaysia", "말레이시아",
    "australia", "호주", "canada", "캐나다", "new zealand", "뉴질랜드", "영국", "프랑스", "독일", "이탈리아", "스페인", "싱가포르", "호주"
]

# 국가별 인기 관광지 정보
COUNTRY_ATTRACTIONS = {
    "한국": {
        "name": "한국",
        "greeting": "한국이요? 좋군요!",
        "cities": ["서울", "부산", "제주도", "경주", "전주", "여수", "강릉", "춘천", "대구", "인천"],
        "cities_en": ["Seoul", "Busan", "Jeju Island", "Gyeongju", "Jeonju", "Yeosu", "Gangneung", "Chuncheon", "Daegu", "Incheon"],
        "cities_ja": ["ソウル", "釜山", "済州島", "慶州", "全州", "麗水", "江陵", "春川", "大邱", "仁川"],
        "cities_zh": ["首尔", "釜山", "济州岛", "庆州", "全州", "丽水", "江陵", "春川", "大邱", "仁川"],
        "popular": "현재 관광객들의 선호도는 1위 서울, 2위 제주도, 3위 부산 순입니다."
    },
    "일본": {
        "name": "일본",
        "greeting": "일본이요? 멋진 선택이네요!",
        "cities": ["도쿄", "오사카", "교토", "후쿠오카", "삿포로", "나고야", "요코하마", "고베", "히로시마", "나라"],
        "popular": "현재 관광객들의 선호도는 1위 도쿄, 2위 교토, 3위 오사카 순입니다."
    },
    "중국": {
        "name": "중국",
        "greeting": "중국이요? 광활한 대륙을 탐험하시는군요!",
        "cities": ["베이징", "상하이", "시안", "청두", "광저우", "항저우", "난징", "칭다오", "다롄", "선전"],
        "popular": "현재 관광객들의 선호도는 1위 베이징, 2위 상하이, 3위 시안 순입니다."
    },
    "미국": {
        "name": "미국",
        "greeting": "미국이요? 다양한 매력을 가진 나라네요!",
        "cities": ["뉴욕", "로스앤젤레스", "시카고", "라스베가스", "샌프란시스코", "마이애미", "보스턴", "워싱턴DC", "시애틀", "뉴올리언스"],
        "popular": "현재 관광객들의 선호도는 1위 뉴욕, 2위 로스앤젤레스, 3위 라스베가스 순입니다."
    },
    "태국": {
        "name": "태국",
        "greeting": "태국이요? 맛있는 음식과 아름다운 해변의 나라네요!",
        "cities": ["방콕", "푸켓", "치앙마이", "파타야", "크라비", "코사무이", "아유타야", "칸차나부리", "핫야이", "우돈타니"],
        "popular": "현재 관광객들의 선호도는 1위 방콕, 2위 푸켓, 3위 치앙마이 순입니다."
    },
    "베트남": {
        "name": "베트남",
        "greeting": "베트남이요? 아름다운 자연과 맛있는 음식의 나라네요!",
        "cities": ["하노이", "호치민", "다낭", "하롱베이", "후에", "호이안", "달랏", "나트랑", "사파"],
        "popular": "현재 관광객들의 선호도는 1위 하노이, 2위 호치민, 3위 하롱베이 순입니다."
    },
    "영국": {
        "name": "영국",
        "greeting": "영국이요? 고풍스러운 매력의 나라네요!",
        "cities": ["런던", "맨체스터", "리버풀", "에딘버러", "글래스고", "버밍엄", "브리스톨", "옥스포드", "케임브리지", "바스"],
        "popular": "현재 관광객들의 선호도는 1위 런던, 2위 에딘버러, 3위 맨체스터 순입니다."
    },
    "프랑스": {
        "name": "프랑스",
        "greeting": "프랑스요? 예술과 로맨스의 나라네요!",
        "cities": ["파리", "니스", "리옹", "마르세유", "보르도", "툴루즈", "스트라스부르", "아비뇽", "칸", "몽생미셸"],
        "popular": "현재 관광객들의 선호도는 1위 파리, 2위 니스, 3위 리옹 순입니다."
    },
    "독일": {
        "name": "독일",
        "greeting": "독일이요? 효율성과 문화가 조화로운 나라네요!",
        "cities": ["베를린", "뮌헨", "함부르크", "프랑크푸르트", "쾰른", "드레스덴", "뉘른베르크", "하이델베르크", "로텐부르크", "뷔르츠부르크"],
        "popular": "현재 관광객들의 선호도는 1위 베를린, 2위 뮌헨, 3위 함부르크 순입니다."
    },
    "이탈리아": {
        "name": "이탈리아",
        "greeting": "이탈리아요? 역사와 미식의 나라네요!",
        "cities": ["로마", "밀란", "베네치아", "피렌체", "나폴리", "토리노", "볼로냐", "시라쿠사", "팔레르모", "베로나"],
        "popular": "현재 관광객들의 선호도는 1위 로마, 2위 베네치아, 3위 피렌체 순입니다."
    },
    "스페인": {
        "name": "스페인",
        "greeting": "스페인이요? 열정과 축제의 나라네요!",
        "cities": ["마드리드", "바르셀로나", "발렌시아", "세비야", "그라나다", "말라가", "빌바오", "코르도바", "톨레도", "산티아고데콤포스텔라"],
        "popular": "현재 관광객들의 선호도는 1위 마드리드, 2위 바르셀로나, 3위 세비야 순입니다."
    },
    "싱가포르": {
        "name": "싱가포르",
        "greeting": "싱가포르요? 현대적이면서도 전통이 살아있는 도시네요!",
        "cities": ["싱가포르시티", "센토사", "마리나베이", "차이나타운", "리틀인디아", "아랍스트리트", "오차드", "클라키", "우드랜드", "주롱"],
        "popular": "현재 관광객들의 선호도는 1위 마리나베이, 2위 센토사, 3위 차이나타운 순입니다."
    },
    "호주": {
        "name": "호주",
        "greeting": "호주요? 광활한 자연과 독특한 동물들의 나라네요!",
        "cities": ["시드니", "멜버른", "브리즈번", "퍼스", "애들레이드", "골드코스트", "케언즈", "다윈", "호바트", "앨리스스프링스"],
        "popular": "현재 관광객들의 선호도는 1위 시드니, 2위 멜버른, 3위 골드코스트 순입니다."
    }
}

def is_country(text):
    """입력된 텍스트가 국가인지 확인"""
    # 영어 국가명 매핑 추가
    english_country_mapping = {
        "korea": "한국", "south korea": "한국", "japan": "일본", "china": "중국",
        "usa": "미국", "america": "미국", "united states": "미국",
        "uk": "영국", "united kingdom": "영국", "france": "프랑스",
        "germany": "독일", "italy": "이탈리아", "spain": "스페인",
        "thailand": "태국", "vietnam": "베트남", "singapore": "싱가포르",
        "malaysia": "말레이시아", "australia": "호주", "canada": "캐나다",
        "new zealand": "뉴질랜드"
    }
    
    # 일본어 국가명 매핑 추가
    japanese_country_mapping = {
        "韓国": "한국", "日本": "일본", "中国": "중국", "アメリカ": "미국",
        "イギリス": "영국", "フランス": "프랑스", "ドイツ": "독일",
        "イタリア": "이탈리아", "スペイン": "스페인", "タイ": "태국",
        "ベトナム": "베트남", "シンガポール": "싱가포르", "オーストラリア": "호주",
        "カナダ": "캐나다", "ニュージーランド": "뉴질랜드"
    }
    
    # 중국어 국가명 매핑 추가
    chinese_country_mapping = {
        "韩国": "한국", "日本": "일본", "中国": "중국", "美国": "미국",
        "英国": "영국", "法国": "프랑스", "德国": "독일",
        "意大利": "이탈리아", "西班牙": "스페인", "泰国": "태국",
        "越南": "베트남", "新加坡": "싱가포르", "澳大利亚": "호주",
        "加拿大": "캐나다", "新西兰": "뉴질랜드"
    }
    
    text_lower = text.lower()
    
    # 영어 국가명 매핑 확인
    for eng_name, kor_name in english_country_mapping.items():
        if eng_name in text_lower:
            return True
    
    # 일본어 국가명 매핑 확인
    for jp_name, kor_name in japanese_country_mapping.items():
        if jp_name in text:
            return True
    
    # 중국어 국가명 매핑 확인
    for cn_name, kor_name in chinese_country_mapping.items():
        if cn_name in text:
            return True
    
    # 기존 COUNTRIES 리스트 확인
    return any(country.lower() in text_lower for country in COUNTRIES)

def get_country_info(country_name, lang="ko"):
    """국가 정보를 반환하는 함수"""
    # 영어 국가명을 한국어로 변환
    english_country_mapping = {
        "korea": "한국", "south korea": "한국", "japan": "일본", "china": "중국",
        "usa": "미국", "america": "미국", "united states": "미국",
        "uk": "영국", "united kingdom": "영국", "france": "프랑스",
        "germany": "독일", "italy": "이탈리아", "spain": "스페인",
        "thailand": "태국", "vietnam": "베트남", "singapore": "싱가포르",
        "malaysia": "말레이시아", "australia": "호주", "canada": "캐나다",
        "new zealand": "뉴질랜드"
    }
    
    # 일본어 국가명을 한국어로 변환
    japanese_country_mapping = {
        "韓国": "한국", "日本": "일본", "中国": "중국", "アメリカ": "미국",
        "イギリス": "영국", "フランス": "프랑스", "ドイツ": "독일",
        "イタリア": "이탈리아", "スペイン": "스페인", "タイ": "태국",
        "ベトナム": "베트남", "シンガポール": "싱가포르", "オーストラリア": "호주",
        "カナダ": "캐나다", "ニュージーランド": "뉴질랜드"
    }
    
    # 중국어 국가명을 한국어로 변환
    chinese_country_mapping = {
        "韩国": "한국", "日本": "일본", "中国": "중국", "美国": "미국",
        "英国": "영국", "法国": "프랑스", "德国": "독일",
        "意大利": "이탈리아", "西班牙": "스페인", "泰国": "태국",
        "越南": "베트남", "新加坡": "싱가포르", "澳大利亚": "호주",
        "加拿大": "캐나다", "新西兰": "뉴질랜드"
    }
    
    country_name_lower = country_name.lower()
    
    # 영어 국가명을 한국어로 변환
    for eng_name, kor_name in english_country_mapping.items():
        if eng_name in country_name_lower:
            country_name = kor_name
            break
    
    # 일본어 국가명을 한국어로 변환
    for jp_name, kor_name in japanese_country_mapping.items():
        if jp_name in country_name:
            country_name = kor_name
            break
    
    # 중국어 국가명을 한국어로 변환
    for cn_name, kor_name in chinese_country_mapping.items():
        if cn_name in country_name:
            country_name = kor_name
            break
    
    # COUNTRY_ATTRACTIONS에서 정보 찾기
    for country_key, info in COUNTRY_ATTRACTIONS.items():
        if country_key.lower() in country_name.lower():
            # 언어에 맞는 도시 목록 반환
            if lang == "en" and "cities_en" in info:
                info_copy = info.copy()
                info_copy["cities"] = info["cities_en"]
                return info_copy
            elif lang == "ja" and "cities_ja" in info:
                info_copy = info.copy()
                info_copy["cities"] = info["cities_ja"]
                return info_copy
            elif lang == "zh" and "cities_zh" in info:
                info_copy = info.copy()
                info_copy["cities"] = info["cities_zh"]
                return info_copy
            else:
                return info
    return None

def get_next_question(user_state, lang="ko"):
    """다음 질문을 결정하는 함수"""
    if "destination" not in user_state:
        if lang == "en":
            return "Which city or country would you like to travel to?"
        elif lang == "ja":
            return "どの都市や国に行きたいですか？"
        elif lang == "zh":
            return "您想去哪个城市或国家？"
        else:
            return "여행하실 도시나 국가는 어디인가요?"
    
    # 목적지가 국가인 경우 구체적인 도시를 묻기
    if is_country(user_state["destination"]) and "destination_city" not in user_state:
        country_info = get_country_info(user_state["destination"])
        if country_info:
            if lang == "en":
                return f"Great choice! {country_info['name']} has many cities. Which city would you like to visit?"
            elif lang == "ja":
                return f"素晴らしい選択です！{country_info['name']}には多くの都市があります。どの都市に行きたいですか？"
            elif lang == "zh":
                return f"很好的选择！{country_info['name']}有很多城市。您想去哪个城市？"
            else:
                return f"{country_info['greeting']} {country_info['name']}의 어떤 도시를 여행하고 싶으신가요? {country_info['popular']}"
        else:
            if lang == "en":
                return f"Which city in {user_state['destination']} would you like to visit?"
            elif lang == "ja":
                return f"{user_state['destination']}のどの都市に行きたいですか？"
            elif lang == "zh":
                return f"您想去{user_state['destination']}的哪个城市？"
            else:
                return f"{user_state['destination']}의 어떤 도시를 여행하고 싶으신가요?"
    
    # 도시가 입력된 경우 재치있는 응답
    if "destination_city" in user_state and "duration" not in user_state:
        city = user_state["destination_city"]
        if lang == "en":
            city_responses = [
                f"{city}? Great choice! How many days would you like to plan for?",
                f"You selected {city}! Good choice. How many days would you like to plan for?",
                f"Traveling to {city}? Interesting city! How many days would you like to plan for?",
                f"You're traveling to {city}! It sounds like a great trip. How many days would you like to plan for?"
            ]
        elif lang == "ja":
            city_responses = [
                f"{city}？素晴らしい選択です！何日間の予定を立てたいですか？",
                f"{city}を選択されましたね！良い選択です。何日間の予定を立てたいですか？",
                f"{city}旅行ですか？興味深い都市ですね！何日間の予定を立てたいですか？",
                f"{city}に旅行されるのですね！素晴らしい旅行になりそうです。何日間の予定を立てたいですか？"
            ]
        elif lang == "zh":
            city_responses = [
                f"{city}？很好的选择！您想计划几天？",
                f"您选择了{city}！好选择。您想计划几天？",
                f"去{city}旅行？很有趣的城市！您想计划几天？",
                f"您要去{city}旅行！听起来很棒。您想计划几天？"
            ]
        else:
            city_responses = [
                f"{city}요? 멋진 선택이네요! 몇 박 며칠 일정으로 계획하고 계신가요?",
                f"{city}를 선택하셨군요! 좋은 선택입니다. 몇 박 며칠 일정으로 계획하고 계신가요?",
                f"{city}여행이요? 흥미로운 도시네요! 몇 박 며칠 일정으로 계획하고 계신가요?",
                f"{city}를 여행하시는군요! 멋진 여행이 될 것 같아요. 몇 박 며칠 일정으로 계획하고 계신가요?"
            ]
        return random.choice(city_responses)
    
    if "duration" not in user_state:
        if lang == "en":
            return "How many days would you like to plan for?"
        elif lang == "ja":
            return "何日間の予定を立てたいですか？"
        elif lang == "zh":
            return "您想计划几天？"
        else:
            return "몇 박 며칠 일정으로 계획하고 계신가요?"
    
    if "interest" not in user_state:
        if lang == "en":
            return "What are you most interested in for your trip? (e.g., food, nature, culture, shopping, etc.)"
        elif lang == "ja":
            return "旅行で最も興味があることは何ですか？（例：食べ物、自然、文化、ショッピングなど）"
        elif lang == "zh":
            return "您对旅行最感兴趣的是什么？（例如：美食、自然、文化、购物等）"
        else:
            return "여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)"
    
    # 모든 정보가 완성되었을 때 일정 생성 시작
    if lang == "en":
        return "Perfect! I have all the information I need. Let me create a detailed travel itinerary for you..."
    elif lang == "ja":
        return "完璧です！必要な情報が揃いました。詳細な旅行計画を作成いたします..."
    elif lang == "zh":
        return "完美！我已经收集到所有需要的信息。让我为您创建详细的旅行计划..."
    else:
        return "완벽합니다! 필요한 정보가 모두 모였습니다. 상세한 여행 일정을 만들어드리겠습니다..."

# 장난/비현실적 여행 키워드 목록
JOKE_KEYWORDS = [
    "시간여행", "타임머신", "하늘여행", "우주여행", "과거로", "미래로", "공상", "판타지", "외계인", "드래곤", "마법", "유니콘", "신세계", "평행우주", "4차원", "차원이동", "환상여행", "상상여행", "꿈속여행", "무한루프", "불로장생", "불가능", "초능력", "초월", "신비", "마법세계", "동화나라", "만화세계", "게임세계"
]

# ====== 실제 서울 맛집/장소 리스트 (확장 가능) ======
SEOUL_REAL_PLACES = [
    "삼청동 카페", "신사동 가로수길 맛집", "한남동 맛집", "북촌손만두",
    "광장시장 진주집", "홍대 닭갈비", "춘천닭갈비", "을지면옥",
    "이태원 바베큐", "우래옥", "성수동 베이커리", "백리향",
    "강남역 맛집", "명동교자", "압구정 스시", "경복궁", "남산타워", "광장시장",
    # 필요시 추가
]

REAL_PLACE_KEYWORDS = [
    "신세계", "카페", "시장", "공원", "해운대", "부산역", "동대문", "백화점", "한식점", "식당", "맛집", "해변", "해수욕장", "기장", "광안리", "남포동", "서면", "센텀시티", "국제시장", "자갈치", "감천", "마차", "역", "점", "공원"
]

def is_real_place(line):
    # 부산 등 목적지명이 포함된 장소명은 무조건 허용
    if "부산" in line:
        return True
    for keyword in REAL_PLACE_KEYWORDS:
        if keyword in line:
            return True
    return False

def replace_with_real_places(text):
    lines = text.split('\n')
    replaced = []
    for line in lines:
        if not is_real_place(line):
            replaced.append("다른 현지 음식점 또는 관광지")
        else:
            replaced.append(line)
    return '\n'.join(replaced)

# =====================
# 챗봇 질문/대화 흐름 커스터마이즈 안내
# =====================
#
# 질문 순서, 질문 문구, 필수 정보 항목(예: 인원, 예산 등)을 바꾸고 싶으시면 언제든 말씀해 주세요.
#
# 혹시 실제 사용 중 "질문이 하나씩 안 나온다"거나 "정보가 다 모이기 전에 추천이 나온다"면,
# 구체적인 입력/응답 예시(사용자 입력, 챗봇 응답)를 알려주시면 바로 점검해드릴 수 있습니다.
#
# 아래 REQUIRED_FIELDS 리스트를 수정하면 질문 순서/문구/항목을 쉽게 바꿀 수 있습니다.
# =====================

@app.route("/")
def serve_index():
    return send_file(os.path.abspath(os.path.join(os.path.dirname(__file__), '../travel-bot/frontend/index.html')))

@app.route('/frontend/<path:filename>')
def frontend_static(filename):
    return send_from_directory(os.path.abspath(os.path.join(os.path.dirname(__file__), '../travel-bot/frontend')), filename)

def get_destination_question(lang):
    if lang == 'en':
        return "Which city or country would you like to travel to?"
    elif lang == 'zh':
        return "您想去哪个城市或国家？"
    elif lang == 'ja':
        return "どの都市や国に行きたいですか？"
    else:
        return "여행하실 도시나 국가는 어디인가요?"

@app.route("/chat", methods=["POST"])
def chat():
    print("[DEBUG] chat 함수 진입")
    data = request.json or {}
    message = data.get("message", "")
    preferred_lang = session.get('preferred_language', 'ko')
    print("[DEBUG] JOKE CHECK:", repr(message), JOKE_KEYWORDS, any(kw in message for kw in JOKE_KEYWORDS))
    if any(kw in message for kw in JOKE_KEYWORDS):
        if preferred_lang == 'en':
            return jsonify({"response": f"'{message}'? I'd love to go there too, but let's stick to real destinations for now! 😅\n\nExamples: Seoul, Busan, Jeju Island etc."})
        elif preferred_lang == 'ja':
            return jsonify({"response": f"'{message}'ですか？私も行ってみたいですが、現実の旅行先だけご案内できます！😅\n\n例：ソウル、釜山、済州島など"})
        elif preferred_lang == 'zh':
            return jsonify({"response": f"'{message}'？我也很想去，但目前只能推荐现实中的目的地哦！😅\n\n例如：首尔、釜山、济州岛等"})
        else:
            return jsonify({"response": f"'{message}'라니! 저도 꼭 가보고 싶지만 아직은 현실적인 여행지만 안내할 수 있어요 😅\n\n예시: 서울, 부산, 제주도 등"})
    # --- 교통수단 키워드 감지 및 transport_chat_handler 직접 호출 (최상단 분기) ---
    transport_keywords = ["고속버스", "버스", "열차", "기차"]
    msg_clean = message.replace(" ", "").lower()
    if (
        any(keyword in msg_clean for keyword in transport_keywords)
        or '시간표' in message
        or '터미널' in message
    ):
        try:
            from transport import transport_chat_handler
        except ImportError:
            transport_chat_handler = None
        if transport_chat_handler:
            result = transport_chat_handler(message, session)
            if isinstance(result, dict) and "response" in result:
                return jsonify({"response": result["response"]})
            else:
                return jsonify({"response": str(result)})
        else:
            return jsonify({"response": "교통 정보 처리 모듈을 불러올 수 없습니다."})

    # --- [추가] 입력이 실제 도시/국가가 아닐 때 fallback 안내 및 user_state 초기화 (최상단, 단 1회만) ---
    user_state = session.get("user_state", {})
    # 관심사 키워드 목록 (fallback에서 제외)
    interest_keywords = [
        "음식", "맛집", "식사", "요리", "자연", "산", "바다", "공원", "문화", "박물관", "사찰", "궁전", "쇼핑", "상점", "시장",
        "food", "nature", "culture", "shopping", "FOOD", "NATURE", "CULTURE", "SHOPPING",
        "食べ物", "グルメ", "料理", "自然", "山", "海", "公園", "文化", "博物館", "寺", "宮殿", "ショッピング", "買い物",
        "美食", "料理", "自然", "山", "海", "公园", "文化", "博物馆", "寺庙", "宫殿", "购物", "买东西"
    ]
    # 도시/국가로 인식되지 않는 입력에 대해 안내 (단, 빈 입력/명령/교통/관심사/기간/언어변경 등은 제외)
    # [수정] 이미 도시가 선택된 상태(관심사 입력 단계)에서는 fallback 적용하지 않음
    # [수정] 기간 입력 단계에서도 fallback 적용하지 않음
    # [수정] 언어 변경 명령어도 제외
    lang_cmds = {
        '한글로 대답해줘': 'ko', '한국어로 대답해줘': 'ko',
        '영어로 대답해줘': 'en', '영어로 답변해줘': 'en',
        '일본어로 대답해줘': 'ja', '일본어로 답변해줘': 'ja',
        '중국어로 대답해줘': 'zh', '중국어로 답변해줘': 'zh',
        '한국어로 답변해줘': 'ko',
    }
    if (message.strip() and 
        not is_country(message) and 
        not is_valid_city(message) and
        not any(keyword in message for keyword in interest_keywords) and
        not extract_duration(message) and  # 기간 입력도 제외
        not (user_state.get('destination_city') and not user_state.get('interest')) and  # 관심사 입력 단계가 아니면
        not (user_state.get('destination') and user_state.get('interest') and not user_state.get('duration')) and  # 기간 입력 단계가 아니면
        not (message.strip() in lang_cmds)):  # 언어 변경 명령어도 제외
        
        # 현재 선택된 국가의 도시들을 예시로 보여주기 (user_state 초기화 전에)
        preferred_lang = session.get('preferred_language', 'ko')
        current_destination = user_state.get('destination')

    
        if current_destination and is_country(current_destination):
            country_info = get_country_info(current_destination, preferred_lang)
            if country_info and country_info.get('cities'):
                # 최대 3개 도시만 예시로 보여주기
                example_cities = ', '.join(country_info['cities'][:3])
                if preferred_lang == 'en':
                    return jsonify({"response": f"'{message}' is not a supported destination. Please try again.\n\nExamples: {example_cities} etc."})
                elif preferred_lang == 'ja':
                    return jsonify({"response": f"'{message}'はサポートされていない目的地です。もう一度入力してください。\n\n例：{example_cities}など"})
                elif preferred_lang == 'zh':
                    return jsonify({"response": f"'{message}'不是支持的目的地。请重新输入。\n\n例如：{example_cities}等"})
                else:
                    return jsonify({"response": f"'{message}'는(은) 여행지로 지원하지 않습니다. 다시 입력해 주세요.\n\n예시: {example_cities} 등"})
        
        # 국가가 선택되지 않은 경우 기본 예시 사용
        if preferred_lang == 'en':
            return jsonify({"response": f"'{message}' is not a supported destination. Please try again.\n\nExamples: Seoul, Busan, Jeju Island etc."})
        elif preferred_lang == 'ja':
            return jsonify({"response": f"'{message}'はサポートされていない目的地です。もう一度入力してください。\n\n例：ソウル、釜山、済州島など"})
        elif preferred_lang == 'zh':
            return jsonify({"response": f"'{message}'不是支持的目的地。请重新输入。\n\n例如：首尔、釜山、济州岛等"})
        else:
            return jsonify({"response": f"'{message}'는(은) 여행지로 지원하지 않습니다. 다시 입력해 주세요.\n\n예시: 서울, 부산, 제주도 등"})

    # 세션에서 대화 상태 불러오기
    user_state = session.get("user_state", {})

    # --- 메시지에서 도시/국가/관심사/기간 추출 및 user_state 업데이트 (preferred_language 분기보다 위) ---
    # 현재 선택된 국가가 있으면 해당 국가의 도시만 검색
    current_country = user_state.get("destination") if is_country(user_state.get("destination", "")) else None
    city = extract_city_from_message(message, current_country)
    if city:
        # 국가가 이미 선택된 상태에서는 destination_city만 업데이트
        if current_country:
            user_state["destination_city"] = city
        else:
            # 국가가 선택되지 않은 상태에서는 destination과 destination_city 모두 업데이트
            user_state["destination"] = city
            user_state["destination_city"] = city
    # 도시가 없고, 입력이 국가명일 경우 국가를 destination에 저장
    elif is_country(message.strip()):
        user_state["destination"] = message.strip()
    # 관심사 입력 단계가 아닐 때만 기간 추출
    if not (user_state.get('destination_city') and not user_state.get('interest')):
        duration = extract_duration(message)
        if duration:
            user_state["duration"] = duration
    interest_keywords = [
        "음식", "맛집", "식사", "요리", "자연", "산", "바다", "공원", "문화", "박물관", "사찰", "궁전", "쇼핑", "상점", "시장",
        "food", "nature", "culture", "shopping", "FOOD", "NATURE", "CULTURE", "SHOPPING",
        "食べ物", "グルメ", "料理", "自然", "山", "海", "公園", "文化", "博物館", "寺", "宮殿", "ショッピング", "買い物",
        "美食", "料理", "自然", "山", "海", "公园", "文化", "博物馆", "寺庙", "宫殿", "购物", "买东西"
    ]
    interest = extract_interest(message, interest_keywords, city)
    if interest:
        user_state["interest"] = interest
    # --- '한국여행', '일본여행' 등 패턴에서 국가 추출 ---
    import re
    country_travel_match = re.match(r"([가-힣]+)여행", message.replace(" ", ""))
    if country_travel_match:
        country_candidate = country_travel_match.group(1)
        if is_country(country_candidate):
            user_state["destination"] = country_candidate
            user_state.pop("destination_city", None)

    # slot-filling 추출 및 user_state 갱신
    # 현재 선택된 국가가 있으면 해당 국가의 도시만 검색
    current_country = user_state.get("destination") if is_country(user_state.get("destination", "")) else None
    city = extract_city_from_message(message, current_country)
    if city:
        user_state["destination_city"] = city
    # 관심사 입력 단계가 아닐 때만 기간 추출
    if not (user_state.get('destination_city') and not user_state.get('interest')):
        duration = extract_duration(message)
        if duration:
            user_state["duration"] = duration
    interest_keywords = [
        "음식", "맛집", "식사", "요리", "자연", "산", "바다", "공원", "문화", "박물관", "사찰", "궁전", "쇼핑", "상점", "시장",
        "food", "nature", "culture", "shopping", "FOOD", "NATURE", "CULTURE", "SHOPPING",
        "食べ物", "グルメ", "料理", "自然", "山", "海", "公園", "文化", "博物館", "寺", "宮殿", "ショッピング", "買い物",
        "美食", "料理", "自然", "山", "海", "公园", "文化", "博物馆", "寺庙", "宫殿", "购物", "买东西"
    ]
    interest = extract_interest(message, interest_keywords, city)
    if interest:
        user_state["interest"] = interest
    print(f"[DEBUG] user_state after extraction: {user_state}")
    session["user_state"] = user_state

    # 모든 slot이 채워졌으면 즉시 일정 생성
    if all(user_state.get(k) for k in ["destination", "destination_city", "duration", "interest"]):
        destination_info = user_state.get("destination", "")
        if user_state["destination"] != user_state["destination_city"]:
            destination_info = f"{user_state['destination']} {user_state['destination_city']}"
        else:
            destination_info = user_state["destination_city"]
        preferred_lang = session.get('preferred_language', 'ko')
        # 언어별 프롬프트 생성
        if preferred_lang == "en":
            prompt = f"""You are a travel expert. Please answer ONLY in English.\n\nTravel Information:\nDestination: {destination_info}\nInterest: {user_state.get('interest', '')}\nDuration: {user_state.get('duration', '')}\n\nPlease create a detailed travel itinerary for {destination_info} focusing on {user_state.get('interest', 'general tourism')} for {user_state.get('duration', 'a few days')}. Include specific places, restaurants, and activities for each day."""
        elif preferred_lang == "ja":
            prompt = f"""あなたは旅行の専門家です。必ず日本語で答えてください。\n\n旅行情報：\n目的地：{destination_info}\n興味：{user_state.get('interest', '')}\n期間：{user_state.get('duration', '')}\n\n{destination_info}の{user_state.get('interest', '一般的な観光')}に焦点を当てた{user_state.get('duration', '数日間')}の詳細な旅行計画を作成してください。各日の具体的な場所、レストラン、アクティビティを含めてください。"""
        elif preferred_lang == "zh":
            prompt = f"""你是旅游专家。请只用中文回答。\n\n旅游信息：\n目的地：{destination_info}\n兴趣：{user_state.get('interest', '')}\n行程：{user_state.get('duration', '')}\n\n请为{destination_info}创建一个详细的旅游行程，重点关注{user_state.get('interest', '一般旅游')}，行程{user_state.get('duration', '几天')}。请包含每天的具体地点、餐厅和活动。"""
        else:
            prompt = f"""당신은 여행 전문가입니다. 반드시 한국어로만 답변하세요.\n\n여행 정보:\n목적지: {destination_info}\n관심사: {user_state.get('interest', '')}\n일정: {user_state.get('duration', '')}\n\n{destination_info}의 {user_state.get('interest', '일반 관광')}에 초점을 맞춘 {user_state.get('duration', '며칠')} 상세한 여행 일정을 만들어주세요. 각 날짜별 구체적인 장소, 식당, 활동을 포함해주세요."""
        if use_ollama():
            result = get_ollama_response(prompt)
        else:
            result = get_hf_response(prompt)
        return jsonify({"response": result})

    # --- 언어 변경 명령이 들어오면 가장 먼저 처리 ---
    lang_cmds = {
        '한글로 대답해줘': 'ko', '한국어로 대답해줘': 'ko',
        '영어로 대답해줘': 'en', '영어로 답변해줘': 'en',
        '일본어로 대답해줘': 'ja', '일본어로 답변해줘': 'ja',
        '중국어로 대답해줘': 'zh', '중국어로 답변해줘': 'zh',
        '한국어로 답변해줘': 'ko',
    }
    if message.strip() in lang_cmds:
        session['preferred_language'] = lang_cmds[message.strip()]
        lang_name = message.strip().replace('로 대답해줘','').replace('로 답변해줘','')
        return jsonify({"response": f"앞으로 {lang_name}로 답변드릴게요!"})

    # --- duration slot-filling 로직을 preferred_language 분기보다 먼저 실행 ---
    # 기간 slot-filling - duration 추출을 먼저 수행 (관심사가 있을 때만)
    # [수정] 관심사 입력 단계에서는 기간 추출 로직을 건너뛰기
    if (user_state.get('destination') and user_state.get('interest') and not user_state.get('duration') and
        not (user_state.get('destination_city') and not user_state.get('interest'))):  # 관심사 입력 단계가 아니면
        # [수정] 관심사 키워드가 포함된 메시지는 기간 추출에서 제외
        if any(keyword in message for keyword in interest_keywords):
            # 관심사 키워드가 포함된 경우 기간 질문만 반복
            preferred_lang = session.get('preferred_language', 'ko')
            if preferred_lang == 'en':
                return jsonify({"response": "How many days would you like to plan for? (e.g., 3 days, 1 week, etc.)"})
            elif preferred_lang == 'ja':
                return jsonify({"response": "何日間の予定を立てたいですか？（例：3日間、1週間など）"})
            elif preferred_lang == 'zh':
                return jsonify({"response": "您想计划几天？（例如：3天、1周等）"})
            else:
                return jsonify({"response": "몇 박 며칠 일정으로 계획하고 계신가요? (예: 3일, 1주일 등)"})
        
        # duration 추출을 먼저 수행하여 city 추출과의 충돌 방지
        duration = extract_duration(message)
        if duration:
            user_state['duration'] = duration
            session['user_state'] = user_state
            # 모든 정보가 채워졌으니 LLM 호출
            destination_info = user_state.get("destination", "")
            if "destination_city" in user_state and user_state["destination_city"]:
                if user_state["destination"] != user_state["destination_city"]:
                    destination_info = f"{user_state['destination']} {user_state['destination_city']}"
                else:
                    destination_info = user_state["destination_city"]
            preferred_lang = session.get('preferred_language', 'ko')
            if preferred_lang == "en":
                prompt = f"""You are a travel expert. Please answer ONLY in English.\n\nTravel Information:\nDestination: {destination_info}\nInterest: {user_state.get('interest', '')}\nDuration: {user_state.get('duration', '')}\n\nPlease create a detailed travel itinerary for {destination_info} focusing on {user_state.get('interest', 'general tourism')} for {user_state.get('duration', 'a few days')}. Include specific places, restaurants, and activities for each day."""
            elif preferred_lang == "ja":
                prompt = f"""あなたは旅行の専門家です。必ず日本語で答えてください。\n\n旅行情報：\n目的地：{destination_info}\n興味：{user_state.get('interest', '')}\n期間：{user_state.get('duration', '')}\n\n{destination_info}の{user_state.get('interest', '一般的な観光')}に焦点を当てた{user_state.get('duration', '数日間')}の詳細な旅行計画を作成してください。各日の具体的な場所、レストラン、アクティビティを含めてください。"""
            elif preferred_lang == "zh":
                prompt = f"""你是旅游专家。请只用中文回答。\n\n旅游信息：\n目的地：{destination_info}\n兴趣：{user_state.get('interest', '')}\n行程：{user_state.get('duration', '')}\n\n请为{destination_info}创建一个详细的旅游行程，重点关注{user_state.get('interest', '一般旅游')}，行程{user_state.get('duration', '几天')}。请包含每天的具体地点、餐厅和活动。"""
            else:
                prompt = f"""당신은 여행 전문가입니다. 반드시 한국어로만 답변하세요.\n\n여행 정보:\n목적지: {destination_info}\n관심사: {user_state.get('interest', '')}\n일정: {user_state.get('duration', '')}\n\n{destination_info}의 {user_state.get('interest', '일반 관광')}에 초점을 맞춘 {user_state.get('duration', '며칠')} 상세한 여행 일정을 만들어주세요. 각 날짜별 구체적인 장소, 식당, 활동을 포함해주세요."""
            if use_ollama():
                result = get_ollama_response(prompt)
            else:
                result = get_hf_response(prompt)
            return jsonify({"response": result})
        # 기간 입력이 아니면 잘못된 입력 안내 후 기간 질문 반복
        duration_slot_filled = True  # duration slot-filling이 실행되었음을 표시
        preferred_lang = session.get('preferred_language', 'ko')
        if preferred_lang == 'en':
            return jsonify({"response": f"'{message}' is not a valid duration. How many days would you like to plan for? (e.g., 3 days, 1 week, etc.)"})
        elif preferred_lang == 'ja':
            return jsonify({"response": f"'{message}'は有効な期間ではありません。何日間の予定を立てたいですか？（例：3日間、1週間など）"})
        elif preferred_lang == 'zh':
            return jsonify({"response": f"'{message}'不是有效的行程。您想计划几天？（例如：3天、1周等）"})
        else:
            return jsonify({"response": f"'{message}'는(은) 올바른 기간이 아닙니다. 몇 박 며칠 일정으로 계획하고 계신가요? (예: 3일, 1주일 등)"})
    
    # --- preferred_language가 있으면 무조건 그 언어로 답변 ---
    if session.get('preferred_language'):
        preferred_lang = session['preferred_language']
        print(f"[DEBUG] preferred_lang: {preferred_lang}, user_state: {user_state}")



        # 국가만 입력된 경우, 도시 질문을 언어별로 반드시 안내
        if user_state.get('destination') and not user_state.get('destination_city') and is_country(user_state['destination']):
            # [추가] preferred_language가 'en'이고 destination이 '한국' 등 한글일 때 영어 안내로 매핑
            if preferred_lang == 'en':
                ko_to_en_country = {
                    '한국': 'Korea', '일본': 'Japan', '중국': 'China', '미국': 'USA', '프랑스': 'France', '독일': 'Germany',
                    '이탈리아': 'Italy', '스페인': 'Spain', '태국': 'Thailand', '베트남': 'Vietnam', '싱가포르': 'Singapore',
                    '호주': 'Australia', '캐나다': 'Canada', '뉴질랜드': 'New Zealand'
                }
                dest = user_state['destination']
                if dest in ko_to_en_country:
                    display_dest = ko_to_en_country[dest]
                else:
                    display_dest = dest
            else:
                display_dest = user_state['destination']
            country_info = get_country_info(user_state['destination'], preferred_lang)
            if country_info:
                city_list = "\n- ".join(country_info["cities"])
                if preferred_lang == 'en':
                    return jsonify({"response": f"{display_dest}? Great choice! {display_dest} has the following cities:\n- {city_list}\nWhich city would you like to visit?"})
                elif preferred_lang == 'ja':
                    return jsonify({"response": f"{display_dest}？素晴らしい選択です！{display_dest}には以下の都市があります：\n- {city_list}\nどの都市に行きたいですか？"})
                elif preferred_lang == 'zh':
                    return jsonify({"response": f"{display_dest}？很好的选择！{display_dest}有以下城市：\n- {city_list}\n您想去哪个城市？"})
                else:
                    return jsonify({"response": f"{display_dest}이요? 멋진 선택입니다! {display_dest}에는 다음과 같은 도시들이 있습니다:\n- {city_list}\n이 중에서 여행하고 싶은 도시가 있으신가요?"})
            else:
                if preferred_lang == 'en':
                    return jsonify({"response": f"Which city in {user_state['destination']} would you like to visit?"})
                elif preferred_lang == 'ja':
                    return jsonify({"response": f"{user_state['destination']}のどの都市に行きたいですか？"})
                elif preferred_lang == 'zh':
                    return jsonify({"response": f"{user_state['destination']}，您想去哪个城市？"})
                else:
                    return jsonify({"response": f"{user_state['destination']}의 어떤 도시를 여행하고 싶으신가요?"})
        # [추가] 도시가 입력된 경우 slot-filling(관심사 등) 질문을 언어별로 반드시 출력
        if user_state.get('destination') and user_state.get('destination_city') and not user_state.get('interest'):
            city = user_state['destination_city']
            if preferred_lang == 'en':
                return jsonify({"response": f"You selected {city}! What are you most interested in for your trip? (e.g., food, nature, culture, shopping, etc.)"})
            elif preferred_lang == 'ja':
                return jsonify({"response": f"{city}を選択されましたね！旅行で最も興味があることは何ですか？（例：食べ物、自然、文化、ショッピングなど）"})
            elif preferred_lang == 'zh':
                return jsonify({"response": f"您选择了{city}！您对旅行最感兴趣的是什么？（例如：美食、自然、文化、购物等）"})
            else:
                return jsonify({"response": f"{city}를 선택하셨군요! 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)"})

            
        # slot-filling: 필요한 정보가 없으면 먼저 질문
        # 아래 코드는 extract_interest 분기에서 안내 메시지와 return이 보장되므로 완전히 삭제
        # if user_state.get('destination') and not user_state.get('interest'):
        #     # 관심사 추출 (예: FOOD, NATURE 등)
        #     interest = extract_interest(message, interest_keywords)
        #     if interest:
        #         user_state['interest'] = interest
        #         session['user_state'] = user_state
        #         # 관심사가 입력되었으니 바로 날짜 질문
        #         if preferred_lang == 'en':
        #             return jsonify({"response": "How many days would you like to plan for?"})
        #         elif preferred_lang == 'ja':
        #             return jsonify({"response": "何日間の予定を立てたいですか？"})
        #         elif preferred_lang == 'zh':
        #             return jsonify({"response": "您想计划几天？"})
        #         else:
        #             return jsonify({"response": "몇 박 며칠 일정으로 계획하고 계신가요?"})
        #     # 관심사 입력이 아니면 관심사가 아닌 입력에 대한 안내
        #     if preferred_lang == 'en':
        #         return jsonify({"response": f"'{message}' is not a valid interest. What are you most interested in for your trip? (e.g., food, nature, culture, shopping, etc.)"})
        #     elif preferred_lang == 'ja':
        #         return jsonify({"response": f"'{message}'は有効な興味ではありません。ご旅行で最も興味があることは何ですか？（例：グルメ、自然、文化、ショッピングなど）"})
        #     elif preferred_lang == 'zh':
        #         return jsonify({"response": f"'{message}'不是有效的兴趣。您对旅行最感兴趣的是什么？（例如：美食、自然、文化、购物等）"})
        #     else:
        #         return jsonify({"response": f"'{message}'는(은) 관심사가 아닙니다. 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)"})

        # user_state에 정보가 있으면 해당 언어로 LLM에 질문
        if user_state and user_state.get('destination') and user_state.get('interest') and user_state.get('duration'):
            destination_info = user_state.get("destination", "")
            if "destination_city" in user_state and user_state["destination_city"]:
                if user_state["destination"] != user_state["destination_city"]:
                    destination_info = f"{user_state['destination']} {user_state['destination_city']}"
                else:
                    destination_info = user_state["destination_city"]
            # 언어별 프롬프트 생성
            if preferred_lang == "en":
                prompt = f"""You are a travel expert. Please answer ONLY in English.\n\nTravel Information:\nDestination: {destination_info}\nInterest: {user_state.get('interest', '')}\nDuration: {user_state.get('duration', '')}\n\nPlease create a detailed travel itinerary for {destination_info} focusing on {user_state.get('interest', 'general tourism')} for {user_state.get('duration', 'a few days')}. Include specific places, restaurants, and activities for each day."""
            elif preferred_lang == "ja":
                prompt = f"""あなたは旅行の専門家です。必ず日本語で答えてください。\n\n旅行情報：\n目的地：{destination_info}\n興味：{user_state.get('interest', '')}\n期間：{user_state.get('duration', '')}\n\n{destination_info}の{user_state.get('interest', '一般的な観光')}に焦点を当てた{user_state.get('duration', '数日間')}の詳細な旅行計画を作成してください。各日の具体的な場所、レストラン、アクティビティを含めてください。"""
            elif preferred_lang == "zh":
                prompt = f"""你是旅游专家。请只用中文回答。\n\n旅游信息：\n目的地：{destination_info}\n兴趣：{user_state.get('interest', '')}\n行程：{user_state.get('duration', '')}\n\n请为{destination_info}创建一个详细的旅游行程，重点关注{user_state.get('interest', '一般旅游')}，行程{user_state.get('duration', '几天')}。请包含每天的具体地点、餐厅和活动。"""
            else:
                prompt = f"""당신은 여행 전문가입니다. 반드시 한국어로만 답변하세요.\n\n여행 정보:\n목적지: {destination_info}\n관심사: {user_state.get('interest', '')}\n일정: {user_state.get('duration', '')}\n\n{destination_info}의 {user_state.get('interest', '일반 관광')}에 초점을 맞춘 {user_state.get('duration', '며칠')} 상세한 여행 일정을 만들어주세요. 각 날짜별 구체적인 장소, 식당, 활동을 포함해주세요."""
            if use_ollama():
                result = get_ollama_response(prompt)
            else:
                result = get_hf_response(prompt)
            return jsonify({"response": result})




    # --- 다국어 입력 감지 및 언어 설정 ---
    # 영어로 입력된 경우 자동으로 영어 모드로 설정
    if not session.get('preferred_language') and any(word in message.lower() for word in ['please', 'recommend', 'trip', 'travel', 'visit', 'go to', 'want to']):
        session['preferred_language'] = 'en'
        print(f"[DEBUG] English input detected, setting language to English")
    
    # 일본어로 입력된 경우 자동으로 일본어 모드로 설정
    if not session.get('preferred_language') and any(word in message for word in ['おすすめ', '旅行', '観光', '行きたい', '教えて', '案内']):
        session['preferred_language'] = 'ja'
        print(f"[DEBUG] Japanese input detected, setting language to Japanese")
    
    # 중국어로 입력된 경우 자동으로 중국어 모드로 설정
    if not session.get('preferred_language') and any(word in message for word in ['推荐', '旅游', '旅行', '想去', '告诉', '介绍']):
        session['preferred_language'] = 'zh'
        print(f"[DEBUG] Chinese input detected, setting language to Chinese")

    # --- 국가+여행 패턴 처리 및 대표 도시 안내 ---
    # 메시지에서 '국가+여행' 패턴 감지 (한국어)
    country_travel_match = re.match(r"([가-힣]+)여행", message.replace(" ", ""))
    if country_travel_match:
        country_candidate = country_travel_match.group(1)
        if is_country(country_candidate):
            user_state["destination"] = country_candidate
            print(f"[DEBUG] Detected country from 여행 패턴: {country_candidate}")
            session["user_state"] = user_state
            # return을 하지 않고 아래 preferred_language 분기로 흐름을 넘김
            country_info = get_country_info(country_candidate, session.get('preferred_language', 'ko'))
            if country_info:
                city_list = "\n- ".join(country_info["cities"])
                session["user_state"] = user_state
                preferred_lang = session.get('preferred_language', 'ko')
                if preferred_lang == 'en':
                    return jsonify({"response": f"{country_candidate}? Great choice! {country_candidate} has the following cities:\n- {city_list}\nWhich city would you like to visit?"})
                elif preferred_lang == 'ja':
                    return jsonify({"response": f"{country_candidate}？素晴らしい選択です！{country_candidate}には以下の都市があります：\n- {city_list}\nどの都市に行きたいですか？"})
                elif preferred_lang == 'zh':
                    return jsonify({"response": f"{country_candidate}？很好的选择！{country_candidate}有以下城市：\n- {city_list}\n您想去哪个城市？"})
                else:
                    return jsonify({"response": f"{country_candidate}이요? 멋진 선택입니다! {country_candidate}에는 다음과 같은 도시들이 있습니다:\n- {city_list}\n이 중에서 여행하고 싶은 도시가 있으신가요?"})
            else:
                session["user_state"] = user_state
                preferred_lang = session.get('preferred_language', 'ko')
                if preferred_lang == 'en':
                    return jsonify({"response": f"{country_candidate}? Great choice! Which city would you like to visit?"})
                elif preferred_lang == 'ja':
                    return jsonify({"response": f"{country_candidate}？素晴らしい選択です！どの都市に行きたいですか？"})
                elif preferred_lang == 'zh':
                    return jsonify({"response": f"{country_candidate}？很好的选择！您想去哪个城市？"})
                else:
                    return jsonify({"response": f"{country_candidate}이요? 멋진 선택입니다! 어떤 도시를 여행하고 싶으신가요?"})
    
    # 영어로 국가 요청 감지 (예: "Please recommend a trip to Korea")
    english_country_match = re.search(r'(?:trip to|visit|go to|travel to)\s+([a-zA-Z]+)', message, re.IGNORECASE)
    if english_country_match:
        country_candidate = english_country_match.group(1)
        if is_country(country_candidate):
            # 영어 국가명을 한국어로 변환하여 저장
            country_mapping = {
                "korea": "한국", "south korea": "한국", "japan": "일본", "china": "중국",
                "usa": "미국", "america": "미국", "united states": "미국",
                "uk": "영국", "united kingdom": "영국", "france": "프랑스",
                "germany": "독일", "italy": "이탈리아", "spain": "스페인",
                "thailand": "태국", "vietnam": "베트남", "singapore": "싱가포르",
                "malaysia": "말레이시아", "australia": "호주", "canada": "캐나다",
                "new zealand": "뉴질랜드"
            }
            
            country_name_lower = country_candidate.lower()
            for eng_name, kor_name in country_mapping.items():
                if eng_name in country_name_lower:
                    user_state["destination"] = kor_name
                    break
            else:
                user_state["destination"] = country_candidate
            
            session['preferred_language'] = 'en'  # 영어 입력이므로 영어 모드로 설정
            print(f"[DEBUG] Detected country from English pattern: {country_candidate} -> {user_state['destination']}")
            country_info = get_country_info(country_candidate, session.get('preferred_language', 'en'))
            if country_info:
                city_list = "\n- ".join(country_info["cities"])
                session["user_state"] = user_state
                return jsonify({"response": f"{country_candidate}? Great choice! {country_candidate} has the following cities:\n- {city_list}\nWhich city would you like to visit?"})
            else:
                session["user_state"] = user_state
                return jsonify({"response": f"{country_candidate}? Great choice! Which city would you like to visit?"})
    
    # 일본어로 국가 요청 감지 (예: "韓国旅行をおすすめ", "日本観光案内")
    japanese_country_match = re.search(r'(韓国|日本|中国|アメリカ|イギリス|フランス|ドイツ|イタリア|スペイン|タイ|ベトナム|シンガポール|オーストラリア|カナダ|ニュージーランド)(旅行|観光|案内|おすすめ)', message)
    if japanese_country_match:
        country_candidate = japanese_country_match.group(1)
        if is_country(country_candidate):
            # 일본어 국가명을 한국어로 변환하여 저장
            country_mapping = {
                "韓国": "한국", "日本": "일본", "中国": "중국", "アメリカ": "미국",
                "イギリス": "영국", "フランス": "프랑스", "ドイツ": "독일",
                "イタリア": "이탈리아", "スペイン": "스페인", "タイ": "태국",
                "ベトナム": "베트남", "シンガポール": "싱가포르", "オーストラリア": "호주",
                "カナダ": "캐나다", "ニュージーランド": "뉴질랜드"
            }
            
            for jp_name, kor_name in country_mapping.items():
                if jp_name in country_candidate:
                    user_state["destination"] = kor_name
                    break
            else:
                user_state["destination"] = country_candidate
            
            session['preferred_language'] = 'ja'  # 일본어 입력이므로 일본어 모드로 설정
            print(f"[DEBUG] Detected country from Japanese pattern: {country_candidate} -> {user_state['destination']}")
            country_info = get_country_info(country_candidate, session.get('preferred_language', 'ja'))
            if country_info:
                city_list = "\n- ".join(country_info["cities"])
                session["user_state"] = user_state
                return jsonify({"response": f"{country_candidate}？素晴らしい選択です！{country_candidate}には以下の都市があります：\n- {city_list}\nどの都市に行きたいですか？"})
            else:
                session["user_state"] = user_state
                return jsonify({"response": f"{country_candidate}？素晴らしい選択です！どの都市に行きたいですか？"})
    
    # 중국어로 국가 요청 감지 (예: "推荐韩国旅游", "日本旅行介绍")
    chinese_country_match = re.search(r'(韩国|日本|中国|美国|英国|法国|德国|意大利|西班牙|泰国|越南|新加坡|澳大利亚|加拿大|新西兰)(旅游|旅行|推荐|介绍)', message)
    if chinese_country_match:
        country_candidate = chinese_country_match.group(1)
        if is_country(country_candidate):
            # 중국어 국가명을 한국어로 변환하여 저장
            country_mapping = {
                "韩国": "한국", "日本": "일본", "中国": "중국", "美国": "미국",
                "英国": "영국", "法国": "프랑스", "德国": "독일",
                "意大利": "이탈리아", "西班牙": "스페인", "泰国": "태국",
                "越南": "베트남", "新加坡": "싱가포르", "澳大利亚": "호주",
                "加拿大": "캐나다", "新西兰": "뉴질랜드"
            }
            
            for cn_name, kor_name in country_mapping.items():
                if cn_name in country_candidate:
                    user_state["destination"] = kor_name
                    break
            else:
                user_state["destination"] = country_candidate
            
            session['preferred_language'] = 'zh'  # 중국어 입력이므로 중국어 모드로 설정
            print(f"[DEBUG] Detected country from Chinese pattern: {country_candidate} -> {user_state['destination']}")
            country_info = get_country_info(country_candidate, session.get('preferred_language', 'zh'))
            if country_info:
                city_list = "\n- ".join(country_info["cities"])
                session["user_state"] = user_state
                return jsonify({"response": f"{country_candidate}？很好的选择！{country_candidate}有以下城市：\n- {city_list}\n您想去哪个城市？"})
            else:
                session["user_state"] = user_state
                return jsonify({"response": f"{country_candidate}？很好的选择！您想去哪个城市？"})

    # 메시지에서 도시, 기간, 관심사 자동 추출 (정보가 없을 때만)
    print(f"[DEBUG] About to extract city from: {message}")
    
    # 관심사 변경 감지 플래그 초기화
    interest_change_detected = False
    
    # 도시 변경 요청 감지 (예: "지역을 서울이 아니라 부산으로 해줘")
    city_change_patterns = [
        r'도시를\s*([가-힣]+)(?:로|으로|도)?\s*변경해줘',
        r'도시를\s*([가-힣]+)(?:로|으로|도)?\s*해줘',
        r'도시를\s*([가-힣]+)(?:로|으로|도)?',
        r'([가-힣]+)로\s*바꿔줘',
        r'([가-힣]+)로\s*변경해줘',
        r'([가-힣]+)\s*대신\s*([가-힣]+)',
        r'([가-힣]+)\s*말고\s*([가-힣]+)'
    ]
    
    city_change_detected = False
    for pattern in city_change_patterns:
        match = re.search(pattern, message)
        if match:
            if len(match.groups()) == 2:
                new_city = match.group(2)
            else:
                new_city = match.group(1)
            print(f"[DEBUG] city_change_patterns matched. new_city: {new_city}")
            # destination_city가 없으면 무조건 세팅
            if not user_state.get("destination_city"):
                user_state["destination_city"] = new_city
                print(f"[DEBUG] [PATCH] destination_city 강제 세팅: {new_city}")

            # 실제 도시인지 확인 (모든 국가의 도시 목록)
            current_country = user_state.get("destination") if is_country(user_state.get("destination", "")) else None
            print(f"[DEBUG] current_country: {current_country}")
            city_candidate = extract_city_from_message(new_city, current_country) if current_country else extract_city_from_message(new_city)
            print(f"[DEBUG] extract_city_from_message result: {city_candidate}")
            is_valid = is_valid_city(city_candidate)
            print(f"[DEBUG] is_valid_city({city_candidate}): {is_valid}")
            if city_candidate:
                print(f"[DEBUG] City change detected: {city_candidate}")
                city = city_candidate
                city_change_detected = True
                break
            else:
                print(f"[DEBUG] Detected '{new_city}' but not a valid city, skipping")
    
    if not city_change_detected:
        # 현재 선택된 국가가 있으면 해당 국가의 도시만 검색
        current_country = user_state.get("destination") if is_country(user_state.get("destination", "")) else None
        city = extract_city_from_message(message, current_country)

        if city and not is_valid_city(city):
            print(f"[DEBUG] '{city}' is not a valid city, asking for another city")
            return jsonify({"response": f"'{city}'는(은) 현재 정보가 없습니다. 다른 도시를 입력해 주세요."})
    
    duration = extract_duration(message)
    
    # duration이 추출되면 user_state에 저장
    if duration:
        user_state["duration"] = duration
        print(f"[DEBUG] Duration saved to user_state: {duration}")
    
    interest_keywords = [
        "음식", "맛집", "식사", "요리", "자연", "산", "바다", "공원", "문화", "박물관", "사찰", "궁전", "쇼핑", "상점", "시장",
        "food", "nature", "culture", "shopping", "FOOD", "NATURE", "CULTURE", "SHOPPING",
        "食べ物", "グルメ", "料理", "自然", "山", "海", "公園", "文化", "博物館", "寺", "宮殿", "ショッピング", "買い物",
        "美食", "料理", "自然", "山", "海", "公园", "文化", "博物馆", "寺庙", "宫殿", "购物", "买东西"
    ]
    print(f"[DEBUG] Extracted city: {city}")
    print(f"[DEBUG] Extracted duration: {duration}")
    print(f"[DEBUG] Interest keywords: {interest_keywords}")
    message_wo_city = message
    city_clean = None
    # --- 국가+여행 패턴 처리 ---
    if city and city.endswith("여행"):
        country_candidate = city[:-2]
        if is_country(country_candidate):
            user_state["destination"] = country_candidate
            print(f"[DEBUG] Detected country from 여행 패턴: {country_candidate}")
    # --- 기존 city/destination 처리 ---
    if city:
        city_clean = city
        if city_clean.endswith("여행"):
            city_clean = city_clean[:-2]
        print(f"[DEBUG] cleaned city for destination: {city_clean}")
        if "destination" in user_state and is_country(user_state["destination"]):
            user_state["destination_city"] = city_clean
            print(f"[DEBUG] destination is country, set destination_city: {city_clean}")
            session["user_state"] = user_state
            # 도시가 입력된 경우, slot-filling 다음 단계(관심사 등)로 바로 진행
            if "destination_city" in user_state and "interest" not in user_state:
                city = user_state["destination_city"]
                preferred_lang = session.get('preferred_language', 'ko')
                if preferred_lang == 'en':
                    return jsonify({"response": f"You selected {city}! What are you most interested in for your trip? (e.g., food, nature, culture, shopping, etc.)"})
                elif preferred_lang == 'ja':
                    return jsonify({"response": f"{city}を選択されましたね！旅行で最も興味があることは何ですか？（例：食べ物、自然、文化、ショッピングなど）"})
                elif preferred_lang == 'zh':
                    return jsonify({"response": f"您选择了{city}！您对旅行最感兴趣的是什么？（例如：美食、自然、文化、购物等）"})
                else:
                    return jsonify({"response": f"{city}를 선택하셨군요! 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)"})
        else:
            user_state["destination"] = city_clean
            if not is_country(city_clean):
                user_state["destination_city"] = city_clean
                print(f"[DEBUG] set destination and destination_city: {city_clean}")
            else:
                if "destination_city" in user_state:
                    del user_state["destination_city"]
        message_wo_city = message.replace(city_clean, "")
        print(f"[DEBUG] City detected, skipping interest extraction for this message.")
        print(f"[DEBUG] user_state after city extraction: {user_state}")
        print(f"[DEBUG] Duration updated in user_state: {duration}")
        print(f"[DEBUG] Current user_state: {user_state}")
        print(f"[DEBUG] Checking if interest exists: {'interest' in user_state}")
        if "interest" in user_state:
            print(f"[DEBUG] Interest value: {user_state['interest']}")
        # 도시 입력 후에는 관심사 질문이 나와야 함
        if "interest" in user_state and user_state["interest"]:
            print(f"[DEBUG] Interest already exists, proceeding to duration question")
            session["user_state"] = user_state
            return jsonify({"response": "몇 박 며칠 일정으로 계획하고 계신가요?"})
        else:
            print(f"[DEBUG] No existing interest found, asking for interest")
            session["user_state"] = user_state
            return jsonify({"response": "여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)"})
    
    # duration이 추출되면 user_state에 저장 (city 블록과 독립적으로)
    if duration:
        user_state["duration"] = duration
        print(f"[DEBUG] Duration saved to user_state: {duration}")
    
    print(f"[DEBUG] user_state after extraction: {user_state}")
    session["user_state"] = user_state

    # 명확한 관심사 입력(예: '관심사: 음식', '음식 여행', '쇼핑 중심' 등)만 반영
    def is_explicit_interest_input(msg, keywords):
        for kw in keywords:
            if f"관심사: {kw}" in msg or f"{kw} 여행" in msg or f"{kw} 중심" in msg:
                return kw
        return None

    interest = None
    explicit_interest = is_explicit_interest_input(message, interest_keywords)
    if explicit_interest:
        user_state["interest"] = explicit_interest
        print(f"[DEBUG] Explicit interest set: {explicit_interest}")
    # 기존 관심사가 없을 때만 추출된 관심사 반영 (관심사 변경/삭제 명령이 있을 때만 interest를 변경)
    elif ("interest" not in user_state or not user_state["interest"]):
        interest = extract_interest(message_wo_city, interest_keywords, city_clean)
        if not interest:
            interest = extract_interest(message, interest_keywords, city_clean)
        if interest:
            user_state["interest"] = interest
            print(f"[DEBUG] Initial interest set: {interest}")
    # 도시/기간만 바뀌는 경우 기존 interest를 유지 (삭제하지 않음)
    # 관심사 변경/삭제 명령이 명확히 감지된 경우에만 interest를 변경/삭제
    # (아래 manual matching에서도 마찬가지로 interest를 명확히 감지한 경우에만 반영)

    # 나머지 기존 로직(도시, duration 등)은 그대로 유지

    # system prompt나 응답에 '추가 정보 요청' 예시가 붙는 경우 제거
    def remove_extra_info_block(text):
        import re
        return re.sub(r'\*\*추가 정보 요청:\*\*.*', '', text, flags=re.DOTALL)

    # 기간 변경 요청 감지 (예: "일정을 2일로 변경해줘", "3일로 줄여줘")
    duration_change_patterns = [
        r'일정을\s*(\d+일)\s*로\s*변경해줘',
        r'일정을\s*(\d+일)\s*로\s*줄여줘',
        r'일정을\s*(\d+일)\s*로\s*늘려줘',
        r'(\d+일)\s*로\s*변경해줘',
        r'(\d+일)\s*로\s*줄여줘',
        r'(\d+일)\s*로\s*늘려줘',
        r'일정을\s*(\d+일)\s*로\s*바꿔줘',
        r'(\d+일)\s*로\s*바꿔줘',
        r'일정을\s*(\d+일)로\s*변경해줘',
        r'일정을\s*(\d+일)로\s*줄여줘',
        r'일정을\s*(\d+일)로\s*늘려줘',
        r'(\d+일)로\s*변경해줘',
        r'(\d+일)로\s*줄여줘',
        r'(\d+일)로\s*늘려줘',
        r'일정을\s*(\d+일)로\s*바꿔줘',
        r'(\d+일)\s*로\s*바꿔줘'
    ]
    
    duration_change_detected = False
    for pattern in duration_change_patterns:
        match = re.search(pattern, message)
        if match:
            new_duration = match.group(1)
            print(f"[DEBUG] Duration change detected: {new_duration}")
            duration = new_duration
            duration_change_detected = True
            break
        #else:
            #print(f"[DEBUG] Duration pattern '{pattern}' did not match message: '{message}'")
    
    # 관심사 추출 실패 시 수동 매칭 (도시 변경이 감지되지 않은 경우에만)
    if not interest and not city_change_detected and not duration_change_detected:
        print(f"[DEBUG] Manual interest matching for: {message}")
        message_upper = message.upper()
        interest_change_patterns = [
            r'관심사를\s*([가-힣]+)이\s*아니라\s*([가-힣]+)로',
            r'관심사를\s*([가-힣]+)에서\s*([가-힣]+)로',
            r'관심사를\s*([가-힣]+)로\s*바꿔줘',
            r'관심사를\s*([가-힣]+)로\s*변경해줘',
            r'([가-힣]+)\s*대신\s*([가-힣]+)',
            r'([가-힣]+)\s*말고\s*([가-힣]+)'
        ]
        for pattern in interest_change_patterns:
            match = re.search(pattern, message)
            if match:
                if len(match.groups()) == 2:
                    new_interest = match.group(2)
                else:
                    new_interest = match.group(1)
                print(f"[DEBUG] Interest change detected: {new_interest}")
                interest = new_interest
                user_state["interest"] = interest  # 명확히 감지된 경우에만 반영
                interest_change_detected = True
                break
        if not interest_change_detected:
            # 기존 관심사 매칭 로직 (명확히 감지된 경우에만 반영)
            if any(keyword in message for keyword in ["食べ物", "グルメ", "料理"]):
                interest = "음식"
                session['preferred_language'] = 'ja'
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched Japanese interest: {interest}")
            elif any(keyword in message for keyword in ["自然", "山", "海", "公園"]):
                interest = "자연"
                session['preferred_language'] = 'ja'
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched Japanese interest: {interest}")
            elif any(keyword in message for keyword in ["文化", "博物館", "寺", "宮殿"]):
                interest = "문화"
                session['preferred_language'] = 'ja'
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched Japanese interest: {interest}")
            elif any(keyword in message for keyword in ["ショッピング", "買い物"]):
                interest = "쇼핑"
                session['preferred_language'] = 'ja'
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched Japanese interest: {interest}")
            elif any(keyword in message for keyword in ["美食", "料理"]):
                interest = "음식"
                session['preferred_language'] = 'zh'
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched Chinese interest: {interest}")
            elif any(keyword in message for keyword in ["自然", "山", "海", "公园"]):
                interest = "자연"
                session['preferred_language'] = 'zh'
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched Chinese interest: {interest}")
            elif any(keyword in message for keyword in ["文化", "博物馆", "寺庙", "宫殿"]):
                interest = "문화"
                session['preferred_language'] = 'zh'
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched Chinese interest: {interest}")
            elif any(keyword in message for keyword in ["购物", "买东西"]):
                interest = "쇼핑"
                session['preferred_language'] = 'zh'
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched Chinese interest: {interest}")
            elif any(keyword in message_upper for keyword in ["음식", "맛집", "식사", "요리", "FOOD"]):
                interest = "음식"
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched interest: {interest}")
            elif any(keyword in message_upper for keyword in ["자연", "산", "바다", "공원", "NATURE"]):
                interest = "자연"
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched interest: {interest}")
            elif any(keyword in message_upper for keyword in ["문화", "박물관", "사찰", "궁전", "CULTURE"]):
                interest = "문화"
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched interest: {interest}")
            elif any(keyword in message_upper for keyword in ["쇼핑", "상점", "시장", "SHOPPING"]):
                interest = "쇼핑"
                user_state["interest"] = interest
                print(f"[DEBUG] Manually matched interest: {interest}")
    
    # 도시 변경이 감지된 경우, 도시만 업데이트하고 새로운 일정 생성
    if city_change_detected:
        # city가 실제 도시명인지 검증
        if not is_valid_city(city):
            print(f"[DEBUG] Invalid city detected after change: {city}")
            return jsonify({"response": f"'{city}'는(은) 현재 정보가 없습니다. 다른 도시를 입력해 주세요."})
        user_state["destination_city"] = city
        print(f"[DEBUG] City updated to: {city}")
        session["user_state"] = user_state
        # 도시 변경 후 새로운 일정 생성
        preferred_lang = session.get('preferred_language', 'ko')
        print(f"[DEBUG] Starting LLM call for city change, preferred_lang: {preferred_lang}")
        try:
            # 목적지 정보 구성
            destination_info = user_state.get("destination", "")
            if user_state["destination"] != user_state["destination_city"]:
                destination_info = f"{user_state['destination']} {user_state['destination_city']}"
            else:
                destination_info = user_state["destination_city"]
            print(f"[DEBUG] Destination info: {destination_info}")
            print(f"[DEBUG] User state for LLM: {user_state}")
            # 언어별 프롬프트 생성
            if preferred_lang == "en":
                prompt = f"""You are a travel expert. Please answer ONLY in English.\n\nTravel Information:\nDestination: {destination_info}\nInterest: {user_state.get('interest', '')}\nDuration: {user_state.get('duration', '')}\n\nPlease create a detailed travel itinerary for {destination_info} focusing on {user_state.get('interest', 'general tourism')} for {user_state.get('duration', 'a few days')}. Include specific places, restaurants, and activities for each day."""
            elif preferred_lang == "ja":
                prompt = f"""あなたは旅行の専門家です。必ず日本語で答えてください。\n\n旅行情報：\n目的地：{destination_info}\n興味：{user_state.get('interest', '')}\n期間：{user_state.get('duration', '')}\n\n{destination_info}の{user_state.get('interest', '一般的な観光')}に焦点を当てた{user_state.get('duration', '数日間')}の詳細な旅行計画を作成してください。各日の具体的な場所、レストラン、アクティビティを含めてください。"""
            elif preferred_lang == "zh":
                prompt = f"""你是旅游专家。请只用中文回答。\n\n旅游信息：\n目的地：{destination_info}\n兴趣：{user_state.get('interest', '')}\n行程：{user_state.get('duration', '')}\n\n请为{destination_info}创建一个详细的旅游行程，重点关注{user_state.get('interest', '一般旅游')}，行程{user_state.get('duration', '几天')}。请包含每天的具体地点、餐厅和活动。"""
            else:  # 한국어
                prompt = f"""당신은 여행 전문가입니다. 반드시 한국어로만 답변하세요.\n\n여행 정보:\n목적지: {destination_info}\n관심사: {user_state.get('interest', '')}\n일정: {user_state.get('duration', '')}\n\n{destination_info}의 {user_state.get('interest', '일반 관광')}에 초점을 맞춘 {user_state.get('duration', '며칠')} 상세한 여행 일정을 만들어주세요. 각 날짜별 구체적인 장소, 식당, 활동을 포함해주세요."""
            print(f"[DEBUG] Generated prompt for LLM")
            # LLM 호출
            if use_ollama():
                print(f"[DEBUG] Calling Ollama...")
                result = get_ollama_response(prompt)
            else:
                print(f"[DEBUG] Calling HuggingFace...")
                result = get_hf_response(prompt)
            print(f"[DEBUG] LLM response received, length: {len(result) if result else 0}")
            return jsonify({"response": f"도시를 {city}로 변경했습니다.\n\n{result}"})
        except Exception as e:
            print(f"LLM request error: {e}")
            return jsonify({"response": f"도시를 {city}로 변경했습니다."})
    
    # 기간 변경이 감지된 경우, 다른 정보는 건드리지 않고 기간만 업데이트
    if duration_change_detected:
        user_state["duration"] = duration
        print(f"[DEBUG] Duration updated to: {duration}")
        session["user_state"] = user_state
        
        # 기간 변경 후 새로운 일정 생성
        preferred_lang = session.get('preferred_language', 'ko')
        print(f"[DEBUG] Starting LLM call for duration change, preferred_lang: {preferred_lang}")
        try:
            # 목적지 정보 구성
            destination_info = user_state.get("destination", "")
            if user_state["destination"] != user_state["destination_city"]:
                destination_info = f"{user_state['destination']} {user_state['destination_city']}"
            else:
                destination_info = user_state["destination_city"]
            print(f"[DEBUG] Destination info: {destination_info}")
            print(f"[DEBUG] User state for LLM: {user_state}")
            # 언어별 프롬프트 생성
            if preferred_lang == "en":
                prompt = f"""You are a travel expert. Please answer ONLY in English.\n\nTravel Information:\nDestination: {destination_info}\nInterest: {user_state.get('interest', '')}\nDuration: {user_state.get('duration', '')}\n\nPlease create a detailed travel itinerary for {destination_info} focusing on {user_state.get('interest', 'general tourism')} for {user_state.get('duration', 'a few days')}. Include specific places, restaurants, and activities for each day."""
            elif preferred_lang == "ja":
                prompt = f"""あなたは旅行の専門家です。必ず日本語で答えてください。\n\n旅行情報：\n目的地：{destination_info}\n興味：{user_state.get('interest', '')}\n期間：{user_state.get('duration', '')}\n\n{destination_info}の{user_state.get('interest', '一般的な観光')}に焦点を当てた{user_state.get('duration', '数日間')}の詳細な旅行計画を作成してください。各日の具体的な場所、レストラン、アクティビティを含めてください。"""
            elif preferred_lang == "zh":
                prompt = f"""你是旅游专家。请只用中文回答。\n\n旅游信息：\n目的地：{destination_info}
兴趣：{user_state.get('interest', '')}
行程：{user_state.get('duration', '')}

请为{destination_info}创建一个详细的旅游行程，重点关注{user_state.get('interest', '一般旅游')}，行程{user_state.get('duration', '几天')}。请包含每天的具体地点、餐厅和活动。"""
            else:  # 한국어
                prompt = f"""당신은 여행 전문가입니다. 반드시 한국어로만 답변하세요.\n\n여행 정보:
목적지: {destination_info}
관심사: {user_state.get('interest', '')}
일정: {user_state.get('duration', '')}

{destination_info}의 {user_state.get('interest', '일반 관광')}에 초점을 맞춘 {user_state.get('duration', '며칠')} 상세한 여행 일정을 만들어주세요. 각 날짜별 구체적인 장소, 식당, 활동을 포함해주세요."""
            # Day N 프롬프트 강화
            n_days = None
            if user_state.get('duration'):
                match = re.search(r'(\d+)', user_state['duration'])
                if match:
                    n_days = int(match.group(1))
                    prompt += f"\n반드시 Day 1부터 Day {n_days}까지 {n_days}일치 일정을 각각 구분해서 작성하세요."
            print(f"[DEBUG] Generated prompt for LLM (duration change)")
            # LLM 호출
            if use_ollama():
                print(f"[DEBUG] Calling Ollama...")
                result = get_ollama_response(prompt)
            else:
                print(f"[DEBUG] Calling HuggingFace...")
                result = get_hf_response(prompt)
            print(f"[DEBUG] LLM response received, length: {len(result) if result else 0}")
            # Day N 후처리: split_days/filter_to_n_days 적용
            if n_days:
                from backend.app import split_days, filter_to_n_days  # self-import 허용(로컬 함수)
                days = split_days(result)
                days = days[:n_days]
                # Day별로 다시 합치기
                result = '\n\n'.join(days)
            return jsonify({"response": f"일정을 {duration}로 변경했습니다.\n\n{result}"})
            
        except Exception as e:
            print(f"LLM request error: {e}")
            return jsonify({"response": f"일정을 {duration}로 변경했습니다."})
    
    # 관심사 변경이 감지된 경우, 다른 정보는 건드리지 않고 관심사만 업데이트
    if interest_change_detected:
        user_state["interest"] = interest
        print(f"[DEBUG] Interest updated to: {interest}")
        session["user_state"] = user_state
        
        # 관심사 변경 후 새로운 일정 생성
        preferred_lang = session.get('preferred_language', 'ko')
        print(f"[DEBUG] Starting LLM call for interest change, preferred_lang: {preferred_lang}")
        try:
            # 목적지 정보 구성
            destination_info = user_state.get("destination", "")
            if user_state["destination"] != user_state["destination_city"]:
                destination_info = f"{user_state['destination']} {user_state['destination_city']}"
            else:
                destination_info = user_state["destination_city"]
            
            print(f"[DEBUG] Destination info: {destination_info}")
            print(f"[DEBUG] User state for LLM: {user_state}")
            
            # 언어별 프롬프트 생성
            if preferred_lang == "en":
                prompt = f"""You are a travel expert. Please answer ONLY in English.

Travel Information:
Destination: {destination_info}
Interest: {user_state.get('interest', '')}
Duration: {user_state.get('duration', '')}

Please create a detailed travel itinerary for {destination_info} focusing on {user_state.get('interest', 'general tourism')} for {user_state.get('duration', 'a few days')}. Include specific places, restaurants, and activities for each day."""
            
            elif preferred_lang == "ja":
                prompt = f"""あなたは旅行の専門家です。必ず日本語で答えてください。

旅行情報：
目的地：{destination_info}
興味：{user_state.get('interest', '')}
期間：{user_state.get('duration', '')}

{destination_info}の{user_state.get('interest', '一般的な観光')}に焦点を当てた{user_state.get('duration', '数日間')}の詳細な旅行計画を作成してください。各日の具体的な場所、レストラン、アクティビティを含めてください。"""
            
            elif preferred_lang == "zh":
                prompt = f"""你是旅游专家。请只用中文回答。

旅游信息：
目的地：{destination_info}
兴趣：{user_state.get('interest', '')}
行程：{user_state.get('duration', '')}

请为{destination_info}创建一个详细的旅游行程，重点关注{user_state.get('interest', '一般旅游')}，行程{user_state.get('duration', '几天')}。请包含每天的具体地点、餐厅和活动。"""
            
            else:  # 한국어
                prompt = f"""당신은 여행 전문가입니다. 반드시 한국어로만 답변하세요.

여행 정보:
목적지: {destination_info}
관심사: {user_state.get('interest', '')}
일정: {user_state.get('duration', '')}

{destination_info}의 {user_state.get('interest', '일반 관광')}에 초점을 맞춘 {user_state.get('duration', '며칠')} 상세한 여행 일정을 만들어주세요. 각 날짜별 구체적인 장소, 식당, 활동을 포함해주세요."""
            
            print(f"[DEBUG] Generated prompt for LLM")
            
            # LLM 호출
            if use_ollama():
                print(f"[DEBUG] Calling Ollama...")
                result = get_ollama_response(prompt)
            else:
                print(f"[DEBUG] Calling HuggingFace...")
                result = get_hf_response(prompt)
            
            print(f"[DEBUG] LLM response received, length: {len(result) if result else 0}")
            
            return jsonify({"response": f"관심사를 {interest}로 변경했습니다.\n\n{result}"})
            
        except Exception as e:
            print(f"LLM request error: {e}")
            return jsonify({"response": f"관심사를 {interest}로 변경했습니다."})
    
    # 관심사가 설정되었지만 기간이 없는 경우 기간 질문
    if interest and "duration" not in user_state:
        user_state["interest"] = interest
        session["user_state"] = user_state
        preferred_lang = session.get('preferred_language', 'ko')
        if preferred_lang == 'en':
            return jsonify({"response": "How many days would you like to plan for?"})
        elif preferred_lang == 'ja':
            return jsonify({"response": "何日間の予定を立てたいですか？"})
        elif preferred_lang == 'zh':
            return jsonify({"response": "您想计划几天？"})
        else:
            return jsonify({"response": "몇 박 며칠 일정으로 계획하고 계신가요?"})
    
    # 관심사 추출 실패 시 user_state에서 interest 삭제 (단, 이번 입력이 duration 입력이 아닐 때만)
    if not interest and "interest" in user_state and not duration:
        print(f"[DEBUG] No interest found, removing stale interest from user_state (not a duration input)")
        del user_state["interest"]
    # duration 입력 시에는 기존 관심사를 유지
    elif duration and "interest" in user_state:
        print(f"[DEBUG] Duration input detected, keeping existing interest: {user_state['interest']}")
        interest = user_state["interest"]
    
    # 강제 관심사 설정 (정확한 매칭)
    if not interest and (message.strip().upper() in ["음식", "FOOD", "자연", "NATURE", "문화", "CULTURE", "쇼핑", "SHOPPING"] or 
                        message.strip() in ["食べ物", "グルメ", "料理", "自然", "山", "海", "公園", "文化", "博物館", "寺", "宮殿", "ショッピング", "買い物", "美食", "购物", "买东西"]):
        
        # 일본어 관심사 감지 및 언어 설정
        if message.strip() in ["食べ物", "グルメ", "料理"]:
            interest = "음식"
            session['preferred_language'] = 'ja'
        elif message.strip() in ["自然", "山", "海", "公園"]:
            interest = "자연"
            session['preferred_language'] = 'ja'
        elif message.strip() in ["文化", "博物館", "寺", "宮殿"]:
            interest = "문화"
            session['preferred_language'] = 'ja'
        elif message.strip() in ["ショッピング", "買い物"]:
            interest = "쇼핑"
            session['preferred_language'] = 'ja'
        
        # 중국어 관심사 감지 및 언어 설정
        elif message.strip() in ["美食"]:
            interest = "음식"
            session['preferred_language'] = 'zh'
        elif message.strip() in ["自然", "山", "海", "公园"]:
            interest = "자연"
            session['preferred_language'] = 'zh'
        elif message.strip() in ["文化", "博物馆", "寺庙", "宫殿"]:
            interest = "문화"
            session['preferred_language'] = 'zh'
        elif message.strip() in ["购物", "买东西"]:
            interest = "쇼핑"
            session['preferred_language'] = 'zh'
        
        # 한국어/영어 관심사 감지
        elif message.strip().upper() in ["음식", "FOOD"]:
            interest = "음식"
        elif message.strip().upper() in ["자연", "NATURE"]:
            interest = "자연"
        elif message.strip().upper() in ["문화", "CULTURE"]:
            interest = "문화"
        elif message.strip().upper() in ["쇼핑", "SHOPPING"]:
            interest = "쇼핑"
        
        print(f"[DEBUG] Force set interest: {interest}")
    
    
    
    # 잘못된 관심사 수정 (도시명이 관심사로 설정된 경우)
    if interest and interest in ["want", "travel", "to", "Korea", "korea"]:
        print(f"[DEBUG] Invalid interest detected: {interest}, clearing it")
        interest = None
    # 값이 있을 때만 user_state에 저장
    if city:
        # 기존 destination이 국가명일 때 도시명 입력이 오면 덮어쓰기
        if (
            "destination" not in user_state
            or not user_state["destination"]
            or is_country(user_state["destination"])
        ):
            city_clean = city
            if city_clean.endswith("여행"):
                city_clean = city_clean[:-2]
            print(f"[DEBUG] cleaned city for destination: {city_clean}")
            user_state["destination"] = city_clean
    
    # 수동으로 Korea 감지 (임시 해결책)
    if "korea" in message.lower():
        print(f"[DEBUG] Korea detected in message, forcing destination to Korea")
        user_state["destination"] = "Korea"
        city = "Korea"  # city 변수도 업데이트
        print(f"[DEBUG] Forced destination set to: {user_state['destination']}")
    
    # 잘못된 도시명 수정
    if city and city.lower() in ["want", "travel", "to", "from", "with", "and", "or", "the", "a", "an", "in", "on", "at", "for", "of", "by", "about", "like", "go", "visit", "see", "explore", "tour", "trip", "vacation", "holiday"]:
        print(f"[DEBUG] Invalid city detected: {city}, clearing it")
        city = None
        if "destination" in user_state:
            del user_state["destination"]
    
    # 값이 있을 때만 user_state에 저장
    if interest:
        if "interest" not in user_state or not user_state["interest"]:
            user_state["interest"] = interest
            print(f"[DEBUG] Interest updated in user_state: {interest}")
        elif user_state["interest"] != interest and interest in interest_keywords:
            # 명확히 새로운 관심사일 때만 덮어쓰기
            print(f"[DEBUG] Overwriting interest: {user_state['interest']} -> {interest}")
            user_state["interest"] = interest
    
    print(f"[DEBUG] user_state after extraction: {user_state}")
    session["user_state"] = user_state

    # 다음 질문 결정 (비어있는 정보만 순서대로 질문)
    print(f"[DEBUG] Checking next question - user_state: {user_state}")
    
    preferred_lang = session.get('preferred_language')
    print(f"[DEBUG] Preferred language for next question: {preferred_lang}")
    # 언어 감지 결과도 항상 출력
    lang = detect_language(" ".join([str(user_state.get(f, "")) for f in ["destination", "destination_city", "duration", "interest"] if user_state.get(f)]))
    print(f"[DEBUG] Detected as {lang} (most characters)")

    # 목적지가 국가만 입력된 경우, 도시를 추가로 질문
    if "destination" in user_state and user_state["destination"] and is_country(user_state["destination"]) and "destination_city" not in user_state:
        # 입력 메시지에서 도시 추출 (현재 선택된 국가의 도시만 검색)
        current_country = user_state.get("destination") if is_country(user_state.get("destination", "")) else None
        city_candidate = extract_city_from_message(message, current_country)
        print(f"[DEBUG] preferred_lang1: {preferred_lang}")
        # 도시가 추출되지 않은 경우 (잘못된 도시 입력)
        if not city_candidate:
            preferred_lang = session.get('preferred_language', 'ko')
            if preferred_lang == 'en':
                return jsonify({"response": f"'{message}' is not a city in {user_state['destination']}. Please enter a valid city from the list above."})
            elif preferred_lang == 'ja':
                return jsonify({"response": f"'{message}'は{user_state['destination']}の都市ではありません。上記のリストから有効な都市を入力してください。"})
            elif preferred_lang == 'zh':
                return jsonify({"response": f"'{message}'不是{user_state['destination']}的城市。请从上面的列表中选择一个有效的城市。"})
            else:
                return jsonify({"response": f"'{message}'는(은) {user_state['destination']}의 도시가 아닙니다. 위 목록에서 유효한 도시를 입력해 주세요."})
        
        # 도시가 추출되었지만 유효하지 않은 경우
        if city_candidate and not is_valid_city(city_candidate):
            preferred_lang = session.get('preferred_language', 'ko')
            if preferred_lang == 'en':
                return jsonify({"response": f"'{city_candidate}' currently has no information available. Please enter a different city."})
            elif preferred_lang == 'ja':
                return jsonify({"response": f"'{city_candidate}'には現在情報がありません。別の都市を入力してください。"})
            elif preferred_lang == 'zh':
                return jsonify({"response": f"'{city_candidate}'目前没有可用信息。请输入其他城市。"})
            else:
                return jsonify({"response": f"'{city_candidate}'는(은) 현재 정보가 없습니다. 다른 도시를 입력해 주세요."})
        
        # 도시가 추출되지 않았으므로 도시 목록 다시 보여주기
        country_info = get_country_info(user_state["destination"], session.get('preferred_language', 'ko'))
        if country_info:
            if preferred_lang == 'en':
                return jsonify({"response": f"{country_info['greeting']} Which city in {country_info['name']} would you like to visit? {country_info['popular']}"})
            elif preferred_lang == 'zh':
                return jsonify({"response": f"{country_info['name']}，您想去哪个城市？{country_info['popular']}"})
            elif preferred_lang == 'ja':
                return jsonify({"response": f"{country_info['name']}のどの都市に行きたいですか？{country_info['popular']}"})
            else:
                return jsonify({"response": f"{country_info['greeting']} {country_info['name']}의 어떤 도시를 여행하고 싶으신가요? {country_info['popular']}"})
        else:
            if preferred_lang == 'en':
                return jsonify({"response": f"Which city in {user_state['destination']} would you like to visit?"})
            elif preferred_lang == 'zh':
                return jsonify({"response": f"{user_state['destination']}，您想去哪个城市？"})
            elif preferred_lang == 'ja':
                return jsonify({"response": f"{user_state['destination']}のどの都市に行きたいですか？"})
            else:
                return jsonify({"response": f"{user_state['destination']}의 어떤 도시를 여행하고 싶으신가요?"})
    # 국가/도시 모두 비어있을 때만 국가/도시 질문
    elif "destination" not in user_state or not user_state["destination"]:
        print(f"[DEBUG] Destination missing, asking for destination")
        if preferred_lang == 'en':
            return jsonify({"response": "Which city or country would you like to travel to?"})
        elif preferred_lang == 'zh':
            return jsonify({"response": "您想去哪个城市或国家？"})
        elif preferred_lang == 'ja':
            return jsonify({"response": "どの都市や国に行きたいですか？"})
        else:
            return jsonify({"response": "여행하실 도시나 국가는 어디인가요?"})

    # 정보가 누락된 경우에만 질문 (순서: destination -> interest -> duration)
    if "destination" not in user_state or not user_state["destination"]:
        print(f"[DEBUG] Destination missing, asking for destination")
        if preferred_lang == 'en':
            return jsonify({"response": "Which city or country would you like to travel to?"})
        elif preferred_lang == 'zh':
            return jsonify({"response": "您想去哪个城市或国家？"})
        elif preferred_lang == 'ja':
            return jsonify({"response": "どの都市や国に行きたいですか？"})
        else:
            return jsonify({"response": "여행하실 도시나 국가는 어디인가요?"})
    
    # [통합] 관심사 입력에 대한 적절한 처리 (모든 분기에서 공통)
    print(f"[DEBUG] extract_interest condition check:")
    print(f"[DEBUG] - user_state.get('destination_city'): {user_state.get('destination_city')}")
    print(f"[DEBUG] - not user_state.get('interest'): {not user_state.get('interest')}")
    print(f"[DEBUG] - not is_country(message): {not is_country(message)}")
    print(f"[DEBUG] - not is_valid_city(message): {not is_valid_city(message)}")
    print(f"[DEBUG] - message: '{message}'")
    
    if (user_state.get('destination_city') and not user_state.get('interest') and 
        not is_country(message) and not is_valid_city(message)):
        # 관심사 키워드 목록
        interest_keywords = [
            "음식", "맛집", "식사", "요리", "자연", "산", "바다", "공원", "문화", "박물관", "사찰", "궁전", "쇼핑", "상점", "시장",
            "food", "nature", "culture", "shopping", "FOOD", "NATURE", "CULTURE", "SHOPPING",
            "食べ物", "グルメ", "料理", "自然", "山", "海", "公園", "文化", "博物館", "寺", "宮殿", "ショッピング", "買い物",
            "美食", "料理", "自然", "山", "海", "公园", "文化", "博物馆", "寺庙", "宫殿", "购物", "买东西"
        ]
        # 관심사 추출 시도
        interest = extract_interest(message, interest_keywords)

        preferred_lang = session.get('preferred_language', 'ko')
        if interest:
            user_state['interest'] = interest
            session['user_state'] = user_state
            if preferred_lang == 'en':
                return jsonify({"response": "How many days would you like to plan for?"})
            elif preferred_lang == 'ja':
                return jsonify({"response": "何日間の予定ですか？"})
            elif preferred_lang == 'zh':
                return jsonify({"response": "您想计划几天？"})
            else:
                return jsonify({"response": "몇 박 며칠 일정으로 계획하고 계신가요?"})
        else:
            if preferred_lang == 'en':
                return jsonify({"response": f"'{message}' is not an interest. What interests you most about travel? (e.g., food, nature, culture, shopping, etc.)"})
            elif preferred_lang == 'ja':
                return jsonify({"response": f"'{message}'は興味ではありません。旅行で最も興味があることは何ですか？(例：食べ物、自然、文化、ショッピングなど)"})
            elif preferred_lang == 'zh':
                return jsonify({"response": f"'{message}'不是兴趣。您对旅行最感兴趣的是什么？(例如：美食、自然、文化、购物等)"})
            else:
                return jsonify({"response": f"'{message}'는(은) 관심사가 아닙니다. 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)"})

    # 관심사가 있으면 duration 질문
    if "duration" not in user_state or not user_state["duration"]:
        print(f"[DEBUG] Duration missing, asking for duration")
        if preferred_lang == 'en':
            return jsonify({"response": "How many days would you like to plan for?"})
        elif preferred_lang == 'zh':
            return jsonify({"response": "您想计划几天？"})
        elif preferred_lang == 'ja':
            return jsonify({"response": "何日間の予定ですか？"})
        else:
            return jsonify({"response": "몇 박 며칠 일정으로 계획하고 계신가요?"})
        # return문 뒤에 코드가 더 진행되지 않도록 반드시 return으로 함수 종료

    # 의미 없는 입력 처리 (숫자만 있거나 랜덤 텍스트)
    if (
        not user_state.get("destination")
        and not user_state.get("interest")
        and not user_state.get("duration")
        and (message.strip().isdigit() or len(message.strip()) <= 3)
        and not city
    ):
        print(f"[DEBUG] Meaningless input detected: {message}, ignoring for interest extraction")
        preferred_lang = session.get('preferred_language', 'ko')
        if preferred_lang == 'en':
            return jsonify({"response": "I couldn't understand your input. Please try again.\nWhich city or country would you like to travel to?"})
        elif preferred_lang == 'ja':
            return jsonify({"response": "入力が理解できませんでした。もう一度お試しください。\n旅行したい都市や国はどこですか？"})
        elif preferred_lang == 'zh':
            return jsonify({"response": "我无法理解您的输入。请重试。\n您想去哪个城市或国家？"})
        else:
            return jsonify({"response": "입력을 이해하지 못했어요. 다시 한번 말씀해 주세요.\n여행하실 도시나 국가는 어디인가요?"})

    # [통합] 관심사 입력에 대한 적절한 처리 (모든 분기에서 공통)
    print(f"[DEBUG] extract_interest condition check:")
    print(f"[DEBUG] - user_state.get('destination_city'): {user_state.get('destination_city')}")
    print(f"[DEBUG] - not user_state.get('interest'): {not user_state.get('interest')}")
    print(f"[DEBUG] - not is_country(message): {not is_country(message)}")
    print(f"[DEBUG] - not is_valid_city(message): {not is_valid_city(message)}")
    print(f"[DEBUG] - message: '{message}'")
    
    if (user_state.get('destination_city') and not user_state.get('interest') and 
        not is_country(message) and not is_valid_city(message)):
        # 관심사 키워드 목록
        interest_keywords = [
            "음식", "맛집", "식사", "요리", "자연", "산", "바다", "공원", "문화", "박물관", "사찰", "궁전", "쇼핑", "상점", "시장",
            "food", "nature", "culture", "shopping", "FOOD", "NATURE", "CULTURE", "SHOPPING",
            "食べ物", "グルメ", "料理", "自然", "山", "海", "公園", "文化", "博物館", "寺", "宮殿", "ショッピング", "買い物",
            "美食", "料理", "自然", "山", "海", "公园", "文化", "博物馆", "寺庙", "宫殿", "购物", "买东西"
        ]


    preferred_lang = session.get('preferred_language', 'ko')
    if interest:
        user_state['interest'] = interest
        session['user_state'] = user_state
        if preferred_lang == 'en':
            return jsonify({"response": "How many days would you like to plan for?"})
        elif preferred_lang == 'ja':
            return jsonify({"response": "何日間の予定ですか？"})
        elif preferred_lang == 'zh':
            return jsonify({"response": "您想计划几天？"})
        else:
            return jsonify({"response": "몇 박 며칠 일정으로 계획하고 계신가요?"})
    else:
        if preferred_lang == 'en':
            return jsonify({"response": f"'{message}' is not an interest. What interests you most about travel? (e.g., food, nature, culture, shopping, etc.)"})
        elif preferred_lang == 'ja':
            return jsonify({"response": f"'{message}'は興味ではありません。旅行で最も興味があることは何ですか？(例：食べ物、自然、文化、ショッピングなど)"})
        elif preferred_lang == 'zh':
            return jsonify({"response": f"'{message}'不是兴趣。您对旅行最感兴趣的是什么？(例如：美食、自然、文化、购物等)"})
        else:
            return jsonify({"response": f"'{message}'는(은) 관심사가 아닙니다. 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)"})

    # 모든 정보가 모이면 LLM 프롬프트 생성
    if (user_state.get('destination_city') and user_state.get('interest') and user_state.get('duration')):
        lang = detect_language(" ".join([str(user_state.get(f, "")) for f in ["destination", "destination_city", "duration", "interest"] if user_state.get(f)]))
        prompt = generate_prompt(user_state)
        print(f"[DEBUG] destination_info (corrected): {user_state.get('destination')}, user_state['destination']: {user_state.get('destination')}")
        
        # 목적지 정보 구성 (국가 + 도시 또는 도시만)
        destination_info = user_state["destination"]
        # '여행' 등 접미사가 붙어 있으면 제거
        if destination_info.endswith("여행"):
            destination_info = destination_info[:-2]
        if "destination_city" in user_state and user_state["destination_city"]:
            if user_state["destination"] != user_state["destination_city"]:
                destination_info = f"{user_state['destination']} {user_state['destination_city']}"
            else:
                destination_info = user_state["destination"]
        print(f"[DEBUG] destination_info (corrected): {destination_info}, user_state['destination']: {user_state['destination']}")
        # 여행 기간(며칠) 추출
        duration_text = user_state.get('duration', '')
        duration_days = 1
        match = re.search(r'(\d+)', duration_text)
        if match:
            duration_days = int(match.group(1))
        # 강화된 프롬프트 적용
        prompt = f"""당신은 한국 여행 전문가입니다. 다음 규칙을 반드시 지키세요:

1. 반드시 {destination_info}의 실제 존재하는 장소와 맛집만 포함하세요.
2. {user_state['duration']} 일정을 Day 1, Day 2, Day 3로 구분해서 작성하세요.
3. 각 Day마다 아침, 점심, 저녁 일정을 포함하세요. 아침에는 아침식사, 점심에는 점심식사, 저녁에는 저녁식사를 안내하세요.
4. 같은 시간대(아침/점심/저녁)에 같은 식사나 장소가 반복되면 안 됩니다.
5. 구체적인 장소명과 음식점명을 사용하세요. 중복되는 장소, 시간, 식사는 절대 포함하지 마세요.

예시:
* 아침: {destination_info}의 실제 맛집 예시
* 점심: {destination_info}의 실제 맛집 예시
* 저녁: {destination_info}의 실제 관광지 예시

{destination_info}에서 {user_state['interest']} 중심의 {user_state['duration']} 여행 일정을 만들어주세요."""

        # 캐시 키 생성
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        # 캐시에서 응답 확인
        if cache_key in response_cache:
            cached_result = response_cache[cache_key]
            save_chat_history("user", prompt, cached_result)
            # PDF 생성은 백그라운드에서 처리 (원본 응답 기준)
            def generate_pdf_async():
                try:
                    pdf = PDFGenerator()
                    pdf.add_schedule(cached_result)
                    pdf.output("travel_schedule.pdf")
                except Exception as pdf_e:
                    print(f"PDF 생성 오류: {pdf_e}")
            pdf_thread = threading.Thread(target=generate_pdf_async)
            pdf_thread.daemon = True
            pdf_thread.start()
            session['last_days'] = [cached_result]  # 일정 캐시는 원본 기준
            print(f"[DEBUG] session['last_days'] after schedule: {session['last_days']}")
            return jsonify({"response": cached_result})

        try:
            try:
                if use_ollama():
                    # Ollama 서버 상태 확인
                    ollama_status, status_message = check_ollama_status()
                    if not ollama_status:
                        return jsonify({"response": f"Ollama 서버 문제: {status_message}"})
                    result = get_ollama_response(prompt)
                    print(f"Ollama 원본 응답: {result}")
                else:
                    result = get_hf_response(prompt)
                    print(f"HuggingFace 원본 응답: {result}")
            except Exception as e:
                print(f"LLM 요청 중 오류: {e}")
                raise e
            # 후처리 없이 Ollama 원본 응답을 그대로 반환
            response_cache[cache_key] = result
            save_chat_history("user", prompt, result)
            # '추가 정보 요청' 예시가 답변 끝에 붙는 경우 제거
            result = remove_extra_info_block(result)
            return jsonify({"response": result})
        except Exception as e:
            import io
            tb = io.StringIO()
            traceback.print_exc(file=tb)
            tb_str = tb.getvalue()
            error_message = f"[서버 오류]\n{str(e)}\n\n[Traceback]\n{tb_str}"
            return jsonify({"error": error_message}), 500

@app.route("/download-pdf", methods=["GET", "POST"])
def download_pdf():
    def clean_pdf_text(text):
        import re
        # 1. [AI], [], !, ? 등 불필요한 기호/빈 메시지 제거
        text = re.sub(r'\[AI\]|\[\]|^\s*[!?]\s*$', '', text, flags=re.MULTILINE)
        # 2. ##, **, * 등 마크다운 기호 제거 및 구조화
        text = re.sub(r'^##\s*', '', text, flags=re.MULTILINE)  # ## 제목 제거
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)        # **굵은글씨** 제거
        text = re.sub(r'^\* ', '• ', text, flags=re.MULTILINE)  # * 리스트 → •
        text = re.sub(r'^- ', '• ', text, flags=re.MULTILINE)    # - 리스트 → •
        # 3. Day/일차/숫자 등 제목 구조화
        text = re.sub(r'^(\d+)\s*$', r'\1일차', text, flags=re.MULTILINE)
        text = re.sub(r'^(\d+)\n[-:]+', r'\1일차\n' + '-'*20, text, flags=re.MULTILINE)
        text = re.sub(r'^(\d+)일차:?', r'\1일차\n' + '-'*20, text, flags=re.MULTILINE)
        # 4. 콜론(:)으로 끝나는 제목 정리
        text = re.sub(r'^(.+):\s*$', r'\1', text, flags=re.MULTILINE)
        # 5. & → , 등으로 변환
        text = text.replace('&', ',')
        # 6. 여러 연속 빈 줄 정리
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 7. 앞뒤 공백/빈 줄 정리
        text = text.strip()
        return text
    if request.method == "POST":
        data = request.get_json(force=True)
        messages = data.get("messages", [])
        title = data.get("title", "여행 일정표")
        # 메시지 role별로 구분해서 텍스트 합치기
        text_lines = []
        for msg in messages:
            if msg["role"] == "user":
                text_lines.append(f"[사용자] {msg['content']}")
            elif msg["role"] == "assistant":
                text_lines.append(f"[AI] {msg['content']}")
        full_text = "\n\n".join(text_lines)
        # 마크다운/불필요한 기호 등 정제
        plain_text = clean_pdf_text(full_text)
        from extended_features import PDFGenerator
        pdf = PDFGenerator(title)
        pdf.add_schedule(plain_text)
        filename = pdf.output()
        return send_file(filename, as_attachment=True)
    # 기존 GET 방식
    if os.path.exists("travel_schedule.pdf"):
        return send_file("travel_schedule.pdf", as_attachment=True)
    return jsonify({"error": "PDF not found"}), 404

@app.route("/history")
def history():
    return jsonify(load_chat_history())

def extract_city_from_message(text, country=None):
    # 국가별 도시 리스트
    CITIES_BY_COUNTRY = {
        "한국": [
            "서울", "부산", "울산", "대구", "광주", "제주", "인천", "수원", "전주", "강릉", "춘천", "포항", "창원", "여수", "경주", "목포", "진주", "천안", "청주", "안동", "군산", "속초", "통영", "김해", "광명", "의정부", "평택", "구미", "원주", "아산", "서산", "제천", "공주", "남원", "순천", "부천", "동해", "삼척", "정읍", "영주", "영천", "문경", "상주", "밀양", "거제", "양산", "김천", "논산", "나주", "보령", "사천", "오산", "이천", "파주", "양평", "고양", "하남", "광주(경기)", "광양", "여주", "화성", "군포", "안산", "시흥", "의왕", "안양", "과천", "성남", "용인", "대전", "세종", "제주도",            "SEOUL", "BUSAN", "DAEGU", "GWANGJU", "JEJU", "INCHEON", "SUWON", "JEONJU", "GANGNEUNG", "CHUNCHEON", "POHANG", "CHANGWON", "YEOSU", "GYEONGJU", "MOKPO", "JINJU", "CHEONAN", "CHEONGJU", "ANDONG", "GUNSAN", "SOKCHO", "TONGYEONG", "GIMHAE", "GWANGMYEONG", "UIJEONGBU", "PYEONGTAEK", "GUMI", "WONJU", "ASAN", "SEOSAN", "JECHEON", "GONGJU", "NAMWON", "SUNCHEON", "BUCHEON", "DONGHAE", "SAMCHEOK", "JEONGEUP", "YEONGJU", "YEONGCHUN", "MUNGYEONG", "SANGJU", "MIRYANG", "GEOJE", "YANGSAN", "GIMCHEON", "NONSAN", "NAJU", "BORYEONG", "SACHEON", "OSAN", "ICHEON", "PAJU", "YANGPYEONG", "GOYANG", "HANAM", "GWANGJU_GYEONGGI", "GWANGYANG", "YEOJU", "HWASEONG", "GUNPO", "ANSAN", "SIHEUNG", "UIWANG", "ANYANG", "GWACHEON", "SEONGNAM", "YONGIN", "DAEJEON", "SEJONG"
        ],
        "일본": [
            "도쿄", "오사카", "교토", "후쿠오카", "삿포로", "나고야", "요코하마", "고베", "히로시마", "나라",
            "TOKYO", "OSAKA", "KYOTO", "FUKUOKA", "SAPPORO", "NAGOYA", "YOKOHAMA", "KOBE", "HIROSHIMA", "NARA",
            "東京", "大阪", "京都", "福岡", "札幌", "名古屋", "横浜", "神戸", "広島", "奈良"
        ],
        "중국": [
            "베이징", "상하이", "시안", "청두", "광저우", "항저우", "난징", "칭다오", "다롄", "선전",
            "BEIJING", "SHANGHAI", "XIAN", "CHENGDU", "GUANGZHOU", "HANGZHOU", "NANJING", "QINGDAO", "DALIAN", "SHENZHEN",
            "北京", "上海", "西安", "成都", "广州", "杭州", "南京", "青岛", "大连", "深圳"
        ],
        "미국": [
            "뉴욕", "로스앤젤레스", "시카고", "라스베가스", "샌프란시스코", "마이애미", "보스턴", "워싱턴DC", "시애틀", "뉴올리언스",
            "NEW YORK", "LOS ANGELES", "CHICAGO", "LAS VEGAS", "SAN FRANCISCO", "MIAMI", "BOSTON", "WASHINGTON DC", "SEATTLE", "NEW ORLEANS"
        ],
        "프랑스": [
            "파리", "니스", "리옹", "마르세유", "보르도", "툴루즈", "스트라스부르", "아비뇽", "칸", "몽생미셸",
            "PARIS", "NICE", "LYON", "MARSEILLE", "BORDEAUX", "TOULOUSE", "STRASBOURG", "AVIGNON", "CANNES", "MONT SAINT MICHEL",
            "MONT-SAINT-MICHEL"
        ],
        "영국": [
            "런던", "맨체스터", "리버풀", "에딘버러", "글래스고", "버밍엄", "브리스톨", "옥스포드", "케임브리지", "바스",
            "LONDON", "MANCHESTER", "LIVERPOOL", "EDINBURGH", "GLASGOW", "BIRMINGHAM", "BRISTOL", "OXFORD", "CAMBRIDGE", "BATH"
        ],
        "독일": [
            "베를린", "뮌헨", "함부르크", "프랑크푸르트", "쾰른", "드레스덴", "뉘른베르크", "하이델베르크", "로텐부르크", "뷔르츠부르크",
            "BERLIN", "MUNICH", "HAMBURG", "FRANKFURT", "COLOGNE", "DRESDEN", "NUREMBERG", "HEIDELBERG", "ROTHENBURG", "WURZBURG",
            "MÜNCHEN", "KÖLN", "NÜRNBERG", "ROTHENBURG", "WÜRZBURG"
        ],
        "이탈리아": [
            "로마", "밀란", "베네치아", "피렌체", "나폴리", "토리노", "볼로냐", "시라쿠사", "팔레르모", "베로나",
            "ROME", "MILAN", "VENICE", "FLORENCE", "NAPLES", "TURIN", "BOLOGNA", "SYRACUSE", "PALERMO", "VERONA",
            "ROMA", "MILANO", "VENEZIA", "FIRENZE", "NAPOLI", "TORINO", "SIRACUSA"
        ],
        "스페인": [
            "마드리드", "바르셀로나", "발렌시아", "세비야", "그라나다", "말라가", "빌바오", "코르도바", "톨레도", "산티아고데콤포스텔라",
            "MADRID", "BARCELONA", "VALENCIA", "SEVILLE", "GRANADA", "MALAGA", "BILBAO", "CORDOBA", "TOLEDO", "SANTIAGO DE COMPOSTELA",
            "SEVILLA", "MÁLAGA", "CÓRDOBA"
        ],
        "태국": [
            "방콕", "푸켓", "치앙마이", "파타야", "크라비", "코사무이", "아유타야", "칸차나부리", "핫야이", "우돈타니",
            "BANGKOK", "PHUKET", "CHIANG MAI", "PATTAYA", "KRABI", "KOH SAMUI", "AYUTTHAYA", "KANCHANABURI", "HAT YAI", "UDON THANI",
            "กรุงเทพฯ", "ภูเก็ต", "เชียงใหม่", "พัทยา", "กระบี่", "เกาะสมุย", "อยุธยา", "กาญจนบุรี", "หาดใหญ่", "อุดรธานี"
        ],
        "베트남": [
            "하노이", "호치민", "다낭", "하롱베이", "후에", "호이안", "달랏", "나트랑", "사파",
            "HANOI", "HO CHI MINH", "DANANG", "HALONG BAY", "HUE", "HOI AN", "DALAT", "NHA TRANG", "SAPA",
            "HÀ NỘI", "HỒ CHÍ MINH", "ĐÀ NẴNG", "VỊNH HẠ LONG", "HUẾ", "HỘI AN", "ĐÀ LẠT", "SA PA"
        ],
        "싱가포르": [
            "싱가포르시티", "센토사", "마리나베이", "차이나타운", "리틀인디아", "아랍스트리트", "오차드", "클라키", "우드랜드", "주롱",
            "SINGAPORE CITY", "SENTOSA", "MARINA BAY", "CHINATOWN", "LITTLE INDIA", "ARAB STREET", "ORCHARD", "CLARKE QUAY", "WOODLANDS", "JURONG"
        ],
        "호주": [
            "시드니", "멜버른", "브리즈번", "퍼스", "애들레이드", "골드코스트", "케언즈", "다윈", "호바트", "앨리스스프링스",
            "SYDNEY", "MELBOURNE", "BRISBANE", "PERTH", "ADELAIDE", "GOLD COAST", "CAIRNS", "DARWIN", "HOBART", "ALICE SPRINGS"
        ]
    }
    
    # 국가가 지정된 경우 해당 국가의 도시만 검색
    if country and country in CITIES_BY_COUNTRY:
        cities_to_search = CITIES_BY_COUNTRY[country]
    else:
        # 국가가 지정되지 않은 경우 모든 도시 검색 (기존 동작)
        cities_to_search = []
        for country_cities in CITIES_BY_COUNTRY.values():
            cities_to_search.extend(country_cities)
    
    import re
    text_upper = text.strip().upper()
    # 1. 정확 일치 우선
    for city in cities_to_search:
        if city.upper() == text_upper:
            return city
    # 2. 조사 제거 후 정확 일치
    text_clean = re.sub(r'(으로|로|에|에서|까지|로의|의|에의|에서의|로의|로부터|에서부터|로부터|에까지|에서까지|로까지)', '', text).strip()
    text_clean_upper = text_clean.upper()
    for city in cities_to_search:
        if city.upper() == text_clean_upper:
            return city
    # 3. 부분 일치(문장 내 포함) - 정말 필요한 경우만
    for city in cities_to_search:
        if city.upper() in text_upper:
            return city
    for city in cities_to_search:
        if city.upper() in text_clean_upper:
            return city
    return None

def get_restaurant_recommendations(city):
    """도시별 실제 맛집 추천"""
    
    # 도시별 실제 맛집 데이터베이스
    city_restaurants = {
        "서울": [
            "삼청동 카페", "신사동 가로수길 맛집", "한남동 맛집", "북촌손만두", 
            "광장시장 진주집", "홍대 닭갈비", "춘천닭갈비", "을지면옥", 
            "이태원 바베큐", "우래옥", "성수동 베이커리", "백리향", 
            "강남역 맛집", "명동교자", "압구정 스시"
        ],
        "부산": [
            "부산 돼지국밥", "민락수변포차", "남포동 족발", "자갈치시장 횟집", 
            "부산 닭갈비", "광안리 해물탕", "부산 회센터", "초량돼지갈비", 
            "동래 불고기", "해운대 돈까스", "국제시장 비빔당면", "서면 밀면", 
            "해운대 암소갈비", "사상돼지국밥", "송도 해수욕장 맛집"
        ],
        "제주": [
            "성산일출봉 근처 맛집", "함덕해수욕장 해산물", "조천읍 해산물", 
            "애월 감귤밭 카페", "제주흑돼지", "서귀포 회센터", "한라산 등산 후 식당", 
            "한림칼국수", "오설록 카페", "모슬포항 전복뚝배기", "네거리식당", 
            "돈사돈", "중문관광단지 맛집", "연탄불고기", "순쥥이네명가"
        ],
        "대구": [
            "동인동 찜갈비", "수성못 맛집", "이월드 맛집", "미성당 납작만두", 
            "범어동 스시", "앞산 전망대 카페", "월배시장 국밥", "화원읍 맛집", 
            "누리쌈밥", "대구 칼국수", "동성로 치킨", "대구 곱창", 
            "막창골목", "칠곡 맛집", "서문시장 야시장"
        ],
        "광주": [
            "무등산 등산 맛집", "광산구 횟집", "대인시장 육전", "진미통닭", 
            "상무지구 카페", "화정곱창", "광천터미널 맛집", "광주 비빔밥", 
            "서창동 국밥", "송정떡갈비", "광주 닭갈비", "궁전제과", 
            "첨단맛집", "양림동 카페거리", "충장로 맛집"
        ]
    }
    
    # 도시 매칭 (부분 일치도 허용)
    matched_city = None
    for city_name in city_restaurants.keys():
        if city_name in city or city in city_name:
            matched_city = city_name
            break
    
    if not matched_city:
        return jsonify({"response": f"'{city}'의 맛집 정보는 아직 준비 중입니다. 서울, 부산, 제주, 대구, 광주 중에서 선택해주세요."})
    
    # 해당 도시의 맛집 중 랜덤하게 5개 선택
    restaurants = city_restaurants[matched_city]
    selected_restaurants = random.sample(restaurants, min(5, len(restaurants)))
    
    response = f"{matched_city} 맛집 추천입니다!\n\n"
    response += "### 추천 맛집\n"
    for i, restaurant in enumerate(selected_restaurants, 1):
        response += f"{i}. {restaurant}\n"
    
    response += f"\n### 특징\n"
    response += f"- {matched_city}의 대표적인 현지 맛집들입니다\n"
    response += "- 현지인들이 추천하는 인기 장소입니다\n"
    response += "- 각각 다른 분야의 음식을 맛볼 수 있습니다\n"
    response += f"\n더 자세한 정보나 다른 도시의 맛집이 궁금하시면 언제든 말씀해주세요!"
    
    return jsonify({"response": response})

# Day별로 분리하는 함수 추가

def split_days(llm_response: str):
    import re
    # 다양한 Day 패턴 인식 (###, ####, ##, Day 1, Day 2, 1일차, 2일차, Day1, DAY1, day1, 1일, 2일 등)
    # 기존보다 더 다양한 Day 패턴을 robust하게 인식
    day_pattern = re.compile(r"(^|\n)(#+\s*)?(\*\*)?\s*Day\s*([0-9]+)\s*(\*\*)?\s*:?|(^|\n)(#+\s*)?(\*\*)?\s*DAY\s*([0-9]+)\s*(\*\*)?\s*:?|(^|\n)(#+\s*)?(\*\*)?\s*Day([0-9]+)\s*(\*\*)?\s*:?|(^|\n)(#+\s*)?(\*\*)?\s*([0-9]+)일차|(^|\n)(#+\s*)?(\*\*)?\s*([0-9]+)일|(^|\n)(#+\s*)?(\*\*)?\s*Day\s*([0-9]+):", re.IGNORECASE)
    days = []
    matches = list(day_pattern.finditer(llm_response))
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i+1].start() if i+1 < len(matches) else len(llm_response)
        day_text = llm_response[start:end].strip()
        if day_text:
            days.append(day_text)
    # fallback: Day 제목이 없으면, 더블 뉴라인으로 분리
    if not days:
        blocks = [b.strip() for b in llm_response.split('\n\n') if b.strip()]
        if len(blocks) > 1:
            days = blocks
        else:
            days = [llm_response]
    # Day별 내용이 없는 경우 제거(최종)
    days = [d for d in days if len(d.strip().split('\n')) > 1]
    print(f"[DEBUG] split_days result: {days}")
    return days

# 기간(일정) 자동 추출 함수 추가

def extract_duration(text):
    # 복합 표현 처리 ("1달 3일", "2주 5일" 등)
    total_days = 0
    
    # 달 단위 추출 ("1달", "2달", "1 month", "2 months" 등)
    month_match = re.search(r'(\d+)\s*(달|개월|months?|MONTH)', text, re.IGNORECASE)
    if month_match:
        months = int(month_match.group(1))
        total_days += months * 30  # 1달 = 30일로 계산
    
    # 주 단위 추출 ("1주일", "2주", "1 week", "2 weeks" 등)
    week_match = re.search(r'(\d+)\s*(주일?|주|weeks?|WEEK)', text, re.IGNORECASE)
    if week_match:
        weeks = int(week_match.group(1))
        total_days += weeks * 7
    
    # 일 단위 추출 ("3일", "2박 3일", "삼일", "3 days", "3DAY" 등)
    day_match = re.search(r'(\d+)\s*(일|박|days?|DAY)', text, re.IGNORECASE)
    if day_match:
        days = int(day_match.group(1))
        total_days += days
    
    # 복합 표현이 있으면 총 일수 반환
    if total_days > 0:
        return f"{total_days}일"
    
    # 단일 표현 처리 (기존 로직)
    # 일 단위만 있는 경우
    match = re.search(r'(\d+)\s*(일|박|days?|DAY)', text, re.IGNORECASE)
    if match:
        return f"{match.group(1)}일"
    
    # 주 단위만 있는 경우
    week_match = re.search(r'(\d+)\s*(주일?|주|weeks?|WEEK)', text, re.IGNORECASE)
    if week_match:
        weeks = int(week_match.group(1))
        return f"{weeks * 7}일"
    
    # 달 단위만 있는 경우
    month_match = re.search(r'(\d+)\s*(달|개월|months?|MONTH)', text, re.IGNORECASE)
    if month_match:
        months = int(month_match.group(1))
        return f"{months * 30}일"
    
    # 영어 숫자 매핑
    english_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, 
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }
    
    # 영어 숫자 + days 패턴 매칭 (다양한 표현 지원)
    for eng_word, num in english_num.items():
        # "two days", "cut it down to two days", "change to two days" 등
        if re.search(rf'(?:cut\s+it\s+down\s+to|change\s+to|make\s+it|set\s+to|update\s+to)?\s*{eng_word}\s*days?', text, re.IGNORECASE):
            return f"{num}일"
    
    # 영어 숫자 + weeks 패턴 매칭 추가
    for eng_word, num in english_num.items():
        if re.search(rf'(?:cut\s+it\s+down\s+to|change\s+to|make\s+it|set\s+to|update\s+to)?\s*{eng_word}\s*weeks?', text, re.IGNORECASE):
            return f"{num * 7}일"
    
    # 영어 숫자 + months 패턴 매칭 추가
    for eng_word, num in english_num.items():
        if re.search(rf'(?:cut\s+it\s+down\s+to|change\s+to|make\s+it|set\s+to|update\s+to)?\s*{eng_word}\s*months?', text, re.IGNORECASE):
            return f"{num * 30}일"
    
    # 한글 숫자 매핑
    hangul_num = {
        "하루": 1, "이틀": 2, "삼일": 3, "사일": 4, "오일": 5, "육일": 6, "칠일": 7, "팔일": 8, "구일": 9, "십일": 10
    }
    for k, v in hangul_num.items():
        if k in text:
            return f"{v}일"
    
    # 한글 주 단위 표현 ("일주일", "이주일", "삼주일" 등)
    hangul_week = {
        "일주일": 7, "이주일": 14, "삼주일": 21, "사주일": 28, "오주일": 35,
        "일주": 7, "이주": 14, "삼주": 21, "사주": 28, "오주": 35
    }
    for k, v in hangul_week.items():
        if k in text:
            return f"{v}일"
    
    # 한글 달 단위 표현 ("한달", "두달", "삼달" 등)
    hangul_month = {
        "한달": 30, "두달": 60, "삼달": 90, "사달": 120, "오달": 150,
        "한개월": 30, "두개월": 60, "삼개월": 90, "사개월": 120, "오개월": 150
    }
    for k, v in hangul_month.items():
        if k in text:
            return f"{v}일"
    
    return None

# 한글, 숫자, 일부 기호만 남기는 후처리 함수 추가 (더 관대하게 수정)
def keep_korean_only(text):
    # 베트남어, 태국어, 중국어 제거 (더 정확한 범위)
    # 베트남어 유니코드 범위: \u00C0-\u017F (라틴 확장)
    # 태국어 유니코드 범위: \u0E00-\u0E7F
    # 중국어 유니코드 범위: \u4e00-\u9fff
    
    # 베트남어, 태국어, 중국어 제거
    cleaned = re.sub(r"[\u00C0-\u017F\u0E00-\u0E7F\u4e00-\u9fff]", "", text)
    
    # 영어 단어 제거 (3글자 이상만, 2글자는 허용)
    cleaned = re.sub(r"[A-Za-z]{3,}", "", cleaned)
    
    # 기타 특수문자 제거 (한글, 숫자, 일부 기호만 남김)
    cleaned = re.sub(r"[^가-힣0-9\s:.,\-\*]", "", cleaned)
    
    # 줄별 필터링 (더 관대하게)
    lines = cleaned.split('\n')
    filtered_lines = []
    for line in lines:
        # 알파벳, 영어, 외국어, 외래어, 이상한 표현 포함 줄 제거
        if re.search(r'[A-Za-z]', line):
            continue
        if re.search(r'(try|actual|nearby|restaurant|food|view|visit|famous|menu|cafe|hotel|breakfast|lunch|dinner|experience|must-visit|introduce|enjoy|include|various|etc)', line, re.IGNORECASE):
            continue
        if re.search(r'[\u00C0-\u017F\u0E00-\u0E7F\u4e00-\u9fff]', line):
            continue
        if len(line.strip()) < 1:
            continue
        if re.match(r'^[^\w가-힣]*$', line.strip()):
            continue
        if re.search(r'(thưởng|consuming|카ffee|ordering|스시도보|쿠키|malt|dưới|đây|rằng|hữu|ích|loads|restaurant|try|고ung가루|계양구리|부거)', line, re.IGNORECASE):
            continue
        if re.match(r'^[\d\s:.,\-]+$', line.strip()):
            continue
        if not re.search(r'[가-힣0-9]', line.strip()):
            continue
        filtered_lines.append(line)
    return '\n'.join(filtered_lines)

# 08:00, 12:00, 18:00 일정만 남기고 나머지 시간대와 '비자' 섹션을 제거하는 후처리 함수 추가
def filter_schedule_times(text):
    # Day별 일정만 추출
    lines = text.split('\n')
    filtered = []
    in_visa_section = False
    keep_next = False
    for i, line in enumerate(lines):
        # '비자' 섹션 시작 시 이후 모두 무시
        if '비자' in line:
            in_visa_section = True
            continue
        if in_visa_section:
            continue
        # Day 제목(### Day 1 등)은 무조건 남김
        if re.match(r"^#+\s*Day", line):
            filtered.append(line)
            keep_next = False
            continue
        # 08:00, 12:00, 18:00 일정은 남기고, 그 다음 줄이 '교통편'이면 함께 남김
        if re.match(r".*(08:00|12:00|18:00).*", line):
            filtered.append(line)
            # 다음 줄이 교통편이면 함께 남김
            if i+1 < len(lines) and '교통편' in lines[i+1]:
                filtered.append(lines[i+1])
            keep_next = False
            continue
        # Day 제목, 설명 등은 그대로 유지
        if re.match(r"^\*|^설명|^교통편|^기간|^여행지|^관심사|^\s*$", line):
            filtered.append(line)
            keep_next = False
            continue
    return '\n'.join(filtered)

# Day 제목이 없으면 08:00~18:00 일정 3개씩 묶어서 Day 1, Day 2, Day 3 제목을 자동으로 붙여주는 함수 추가
def ensure_day_titles(text):
    lines = text.split('\n')
    new_lines = []
    day_count = 1
    count = 0
    for line in lines:
        if re.match(r'.*(08:00|12:00|18:00).*', line):
            if count % 3 == 0:
                new_lines.append(f'### Day {day_count}')
                day_count += 1
            count += 1
        new_lines.append(line)
    return '\n'.join(new_lines)

# Day별로 같은 음식점/가게 이름이 반복되면 '다른 현지 음식점'으로 치환하는 함수
import itertools

def replace_duplicate_shops(day_lines):
    seen = set()
    result = []
    for line in day_lines:
        shop_match = re.search(r'-\s*([가-힣0-9 ]+)', line)
        if shop_match:
            shop = shop_match.group(1).strip()
            if shop in seen:
                line = re.sub(shop, '다른 현지 음식점', line)
            else:
                seen.add(shop)
        result.append(line)
    return result

# Day 1~N(여행일수)까지만 남기고, Day N+1 이후는 모두 제거하며, Day 제목/일정이 중복되면 첫 번째만 남기는 함수(단, Day 제목은 항상 남김)로 수정
def filter_to_n_days(text, n_days):
    # split_days로 분리된 경우라면 리스트로 들어옴
    if isinstance(text, list):
        return text[:n_days]
    # 문자열이라면 split_days로 분리 후 N개만 반환
    days = split_days(text)
    return days[:n_days]

# 하루 일정만 남기는 함수 추가

def keep_only_one_day(text):
    lines = text.split('\n')
    result = []
    found = {'아침': False, '점심': False, '저녁': False}
    for line in lines:
        l = line.strip()
        if l.startswith('### Day 1') or l.startswith('Day 1') or l.startswith('**Day 1**'):
            result.append(line)
        elif '아침' in l and not found['아침']:
            result.append(line)
            found['아침'] = True
        elif '점심' in l and not found['점심']:
            result.append(line)
            found['점심'] = True
        elif '저녁' in l and not found['저녁']:
            result.append(line)
            found['저녁'] = True
        # 아침/점심/저녁 다 찾으면 종료
        if all(found.values()):
            break
    return '\n'.join(result)


def generate_prompt(user_state, lang_code="ko"):
    destination = user_state.get("destination", "")
    destination_city = user_state.get("destination_city", "")
    if destination_city and destination_city == destination:
        destination_info = destination_city
    elif destination_city:
        destination_info = f"{destination} {destination_city}"
    else:
        destination_info = destination
    interest = user_state.get("interest", "")
    duration = user_state.get("duration", "")
    # 언어별 안내문
    if lang_code == "en":
        lang_instruction = "Please answer in English."
    elif lang_code == "ja":
        lang_instruction = "日本語で答えてください。"
    elif lang_code == "zh":
        lang_instruction = "请用中文回答。"
    else:
        lang_instruction = "반드시 한국어로만 답변하세요."
    prompt = f"{lang_instruction}\n여행 정보:\n목적지: {destination_info}\n관심사: {interest}\n일정: {duration}"
    return prompt

# extract_interest 함수 복원

def extract_interest(msg, keywords, city=None):
    import re
    tokens = re.findall(r'[가-힣]+|[a-zA-Z]+|[0-9]+', msg)
    print(f"[DEBUG] interest tokens: {tokens}")
    # 국가명 목록 (관심사에서 제외)
    countries = [
        "korea", "south korea", "japan", "china", "usa", "america", "uk", "france", "germany", "italy", "spain", "thailand", "vietnam", "singapore", "malaysia", "australia", "canada", "new zealand",
        "한국", "대한민국", "일본", "중국", "미국", "영국", "프랑스", "독일", "이탈리아", "스페인", "태국", "베트남", "싱가포르", "말레이시아", "호주", "캐나다", "뉴질랜드"
    ]
    # 1. 정확 일치 우선 (대소문자 구분 없이)
    for token in tokens:
        if token.upper() in [k.upper() for k in keywords] and token.lower() not in [c.lower() for c in countries]:
            print(f"[DEBUG] interest token exact match: {token}")
            # 영어 관심사를 한국어로 매핑
            if token.upper() in ["FOOD"]:
                return "음식"
            elif token.upper() in ["NATURE"]:
                return "자연"
            elif token.upper() in ["CULTURE"]:
                return "문화"
            elif token.upper() in ["SHOPPING"]:
                return "쇼핑"
            # 일본어 관심사를 한국어로 매핑
            elif token in ["食べ物", "グルメ", "料理"]:
                return "음식"
            elif token in ["自然", "山", "海", "公園"]:
                return "자연"
            elif token in ["文化", "博物館", "寺", "宮殿"]:
                return "문화"
            elif token in ["ショッピング", "買い物"]:
                return "쇼핑"
            # 중국어 관심사를 한국어로 매핑
            elif token in ["美食", "料理"]:
                return "음식"
            elif token in ["自然", "山", "海", "公园"]:
                return "자연"
            elif token in ["文化", "博物馆", "寺庙", "宫殿"]:
                return "문화"
            elif token in ["购物", "买东西"]:
                return "쇼핑"
            else:
                return token
    # 2. 부분 매칭 (도시명/국가명 포함 토큰은 제외, 2글자 초과만)
    for token in tokens:
        if city and city in token:
            continue
        if token.lower() in [c.lower() for c in countries]:
            print(f"[DEBUG] Skipping country token: {token}")
            continue
        for keyword in keywords:
            if len(token) > 2 and keyword.lower() in token.lower():
                print(f"[DEBUG] interest token partial match: {token} (keyword: {keyword})")
                # 영어 관심사를 한국어로 매핑
                if keyword.lower() in ["food"]:
                    return "음식"
                elif keyword.lower() in ["nature"]:
                    return "자연"
                elif keyword.lower() in ["culture"]:
                    return "문화"
                elif keyword.lower() in ["shopping"]:
                    return "쇼핑"
                # 일본어 관심사를 한국어로 매핑
                elif keyword in ["食べ物", "グルメ", "料理"]:
                    return "음식"
                elif keyword in ["自然", "山", "海", "公園"]:
                    return "자연"
                elif keyword in ["文化", "博物館", "寺", "宮殿"]:
                    return "문화"
                elif keyword in ["ショッピング", "買い物"]:
                    return "쇼핑"
                # 중국어 관심사를 한국어로 매핑
                elif keyword in ["美食", "料理"]:
                    return "음식"
                elif keyword in ["自然", "山", "海", "公园"]:
                    return "자연"
                elif keyword in ["文化", "博物馆", "寺庙", "宫殿"]:
                    return "문화"
                elif keyword in ["购物", "买东西"]:
                    return "쇼핑"
                else:
                    return keyword
    return None

# 동적 system prompt 생성 함수 추가

def get_system_prompt(lang_code: str) -> str:
    if lang_code == "en":
        return "You are a travel expert. Please answer ONLY in English."
    elif lang_code == "ja":
        return "あなたは旅行の専門家です。必ず日本語で答えてください。"
    elif lang_code == "zh":
        return "你是旅游专家。请只用中文回答。"
    else:
        return "당신은 여행 전문가입니다. 반드시 한국어로만 답변하세요."

# 언어 요청 감지 함수 추가

def detect_language_request(message):
    message_lower = message.lower()
    if any(p in message_lower for p in [
        "영어로", "in english", "answer in english", "please respond in english", "영어로 대답해줘", "영어로 말해줘", "영어로 말해줄래"
    ]):
        return "en"
    if any(p in message_lower for p in [
        "일본어로", "in japanese", "answer in japanese", "please respond in japanese", "일본어로 대답해줘", "일본어로 말해줘", "일본어로 말해줄래"
    ]):
        return "ja"
    if any(p in message_lower for p in [
        "중국어로", "in chinese", "answer in chinese", "please respond in chinese", "중국어로 대답해줘", "중국어로 말해줘", "중국어로 말해줄래"
    ]):
        return "zh"
    return "ko"

@app.route('/reset_user_state', methods=['POST'])
def reset_user_state():
    session["user_state"] = {}
    session["last_days"] = None
    session["preferred_language"] = None
    print("[DEBUG] user_state/session 초기화 (웹페이지 INITIALIZE)")
    return jsonify({"status": "ok"})

# --- 도시 유효성 검사 함수 추가 (extract_city_from_message의 CITIES와 동일하게 사용)
def is_valid_city(city):
    CITIES = [
        # 한국
        "서울", "부산", "울산", "대구", "광주", "제주", "인천", "수원", "전주", "강릉", "춘천", "포항", "창원", "여수", "경주", "목포", "진주", "천안", "청주", "안동", "군산", "속초", "통영", "김해", "광명", "의정부", "평택", "구미", "원주", "아산", "서산", "제천", "공주", "남원", "순천", "부천", "동해", "삼척", "정읍", "영주", "영천", "문경", "상주", "밀양", "거제", "양산", "김천", "논산", "나주", "보령", "사천", "오산", "이천", "파주", "양평", "고양", "하남", "광주(경기)", "광양", "여주", "화성", "군포", "안산", "시흥", "의왕", "안양", "과천", "성남", "용인", "대전", "세종", "제주도",
        # 한국 (영어)
        "SEOUL", "BUSAN", "DAEGU", "GWANGJU", "JEJU", "INCHEON", "SUWON", "JEONJU", "GANGNEUNG", "CHUNCHEON", "POHANG", "CHANGWON", "YEOSU", "GYEONGJU", "MOKPO", "JINJU", "CHEONAN", "CHEONGJU", "ANDONG", "GUNSAN", "SOKCHO", "TONGYEONG", "GIMHAE", "GWANGMYEONG", "UIJEONGBU", "PYEONGTAEK", "GUMI", "WONJU", "ASAN", "SEOSAN", "JECHEON", "GONGJU", "NAMWON", "SUNCHEON", "BUCHEON", "DONGHAE", "SAMCHEOK", "JEONGEUP", "YEONGJU", "YEONGCHUN", "MUNGYEONG", "SANGJU", "MIRYANG", "GEOJE", "YANGSAN", "GIMCHEON", "NONSAN", "NAJU", "BORYEONG", "SACHEON", "OSAN", "ICHEON", "PAJU", "YANGPYEONG", "GOYANG", "HANAM", "GWANGJU_GYEONGGI", "GWANGYANG", "YEOJU", "HWASEONG", "GUNPO", "ANSAN", "SIHEUNG", "UIWANG", "ANYANG", "GWACHEON", "SEONGNAM", "YONGIN", "DAEJEON", "SEJONG",
        # 일본
        "도쿄", "오사카", "교토", "후쿠오카", "삿포로", "나고야", "요코하마", "고베", "히로시마", "나라",
        # 일본 (영어)
        "TOKYO", "OSAKA", "KYOTO", "FUKUOKA", "SAPPORO", "NAGOYA", "YOKOHAMA", "KOBE", "HIROSHIMA", "NARA",
        # 일본 (일본어)
        "東京", "大阪", "京都", "福岡", "札幌", "名古屋", "横浜", "神戸", "広島", "奈良",
        # 중국
        "베이징", "상하이", "시안", "청두", "광저우", "항저우", "난징", "칭다오", "다롄", "선전",
        # 중국 (영어)
        "BEIJING", "SHANGHAI", "XIAN", "CHENGDU", "GUANGZHOU", "HANGZHOU", "NANJING", "QINGDAO", "DALIAN", "SHENZHEN",
        # 중국 (중국어)
        "北京", "上海", "西安", "成都", "广州", "杭州", "南京", "青岛", "大连", "深圳",
        # 미국
        "뉴욕", "로스앤젤레스", "시카고", "라스베가스", "샌프란시스코", "마이애미", "보스턴", "워싱턴DC", "시애틀", "뉴올리언스",
        # 미국 (영어)
        "NEW YORK", "LOS ANGELES", "CHICAGO", "LAS VEGAS", "SAN FRANCISCO", "MIAMI", "BOSTON", "WASHINGTON DC", "SEATTLE", "NEW ORLEANS"
    ]
    return city is not None and city.upper() in [c.upper() for c in CITIES]

    # --- slot-filling 개선: 모든 정보가 채워졌으면 곧바로 일정 생성 ---
    if all(user_state.get(k) for k in ["destination", "destination_city", "duration", "interest"]):
        destination_info = user_state.get("destination", "")
        if user_state["destination"] != user_state["destination_city"]:
            destination_info = f"{user_state['destination']} {user_state['destination_city']}"
        else:
            destination_info = user_state["destination_city"]
        preferred_lang = session.get('preferred_language', 'ko')
        # 언어별 프롬프트 생성
        if preferred_lang == "en":
            prompt = f"""You are a travel expert. Please answer ONLY in English.\n\nTravel Information:\nDestination: {destination_info}\nInterest: {user_state.get('interest', '')}\nDuration: {user_state.get('duration', '')}\n\nPlease create a detailed travel itinerary for {destination_info} focusing on {user_state.get('interest', 'general tourism')} for {user_state.get('duration', 'a few days')}. Include specific places, restaurants, and activities for each day."""
        elif preferred_lang == "ja":
            prompt = f"""あなたは旅行の専門家です。必ず日本語で答えてください。\n\n旅行情報：\n目的地：{destination_info}\n興味：{user_state.get('interest', '')}\n期間：{user_state.get('duration', '')}\n\n{destination_info}の{user_state.get('interest', '一般的な観光')}に焦点を当てた{user_state.get('duration', '数日間')}の詳細な旅行計画を作成してください。各日の具体的な場所、レストラン、アクティビティを含めてください。"""
        elif preferred_lang == "zh":
            prompt = f"""你是旅游专家。请只用中文回答。\n\n旅游信息：\n目的地：{destination_info}\n兴趣：{user_state.get('interest', '')}\n行程：{user_state.get('duration', '')}\n\n请为{destination_info}创建一个详细的旅游行程，重点关注{user_state.get('interest', '一般旅游')}，行程{user_state.get('duration', '几天')}。请包含每天的具体地点、餐厅和活动。"""
        else:
            prompt = f"""당신은 여행 전문가입니다. 반드시 한국어로만 답변하세요.\n\n여행 정보:\n목적지: {destination_info}\n관심사: {user_state.get('interest', '')}\n일정: {user_state.get('duration', '')}\n\n{destination_info}의 {user_state.get('interest', '일반 관광')}에 초점을 맞춘 {user_state.get('duration', '며칠')} 상세한 여행 일정을 만들어주세요. 각 날짜별 구체적인 장소, 식당, 활동을 포함해주세요."""
        if use_ollama():
            result = get_ollama_response(prompt)
        else:
            result = get_hf_response(prompt)
        return jsonify({"response": result})

    # --- 교통수단 키워드 감지 및 처리 ---
    transport_keywords = {
        "고속버스": "bus",
        "버스": "bus",
        "ktx": "ktx",
        "지하철": "subway",
        "전철": "subway"
    }
    msg_clean = message.replace(" ", "").lower()
    for keyword, mode in transport_keywords.items():
        if keyword in msg_clean:
            if mode == "bus":
                bus_line, station, destination = extract_bus_info(message)
                if not bus_line and not station:
                    result = (
                        "고속버스 정보를 안내해드리려면 아래 정보를 입력해 주세요! 🚌\n\n"
                        "필요 정보:\n"
                        "• 출발 터미널 또는 도시명\n"
                        "• 도착 터미널 또는 도시명\n"
                        "• (선택) 원하는 날짜/시간\n\n"
                        "예시 질문:\n"
                        "• '고속버스 서울고속터미널에서 부산종합터미널까지 경로 알려줘'\n"
                        "• '서울고속터미널 시간표 알려줘'\n"
                        "• '부산에서 대구까지 고속버스 요금 알려줘'"
                    )
                else:
                    result = get_bus_info(bus_line, station, destination)
            elif mode == "ktx":
                try:
                    from transport import extract_ktx_info
                except ImportError:
                    extract_ktx_info = None
                if extract_ktx_info:
                    dep, arr, date = extract_ktx_info(message)
                else:
                    dep, arr, date = None, None, None
                if not dep or not arr:
                    result = (
                        "KTX 정보를 안내해드리려면 출발지와 도착지를 입력해 주세요! 🚄\n"
                        "예시: 'KTX 서울에서 부산까지 시간표 알려줘'"
                    )
                else:
                    url = get_ktx_info(dep, arr, date)
                    result = f"KTX API 호출 URL: {url}"
            elif mode == "subway":
                line, station, destination = extract_subway_info(message)
                if not station:
                    result = (
                        "지하철 정보를 안내해드리려면 역명 또는 노선명을 입력해 주세요! 🚇\n"
                        "예시: '지하철 2호선 강남역 시간표 알려줘'"
                    )
                else:
                    url = get_subway_info(line, station, destination)
                    result = f"지하철 API 호출 URL: {url}"
            else:
                result = "지원하지 않는 교통수단입니다."
            return jsonify({"response": result})

    # --- 교통수단 키워드 감지 및 transport_chat_handler 직접 호출 ---
    transport_keywords = ["고속버스", "버스", "ktx", "지하철", "전철"]
    msg_clean = message.replace(" ", "").lower()
    for keyword in transport_keywords:
        if keyword in msg_clean:
            try:
                from transport import transport_chat_handler
            except ImportError:
                transport_chat_handler = None
            if transport_chat_handler:
                # session은 flask의 session 또는 dict로 전달
                result = transport_chat_handler(message, session)
                if isinstance(result, dict) and "response" in result:
                    return jsonify({"response": result["response"]})
                else:
                    return jsonify({"response": str(result)})
            else:
                return jsonify({"response": "교통 정보 처리 모듈을 불러올 수 없습니다."})

    # 기본 응답 (모든 조건에 해당하지 않을 때)
    return jsonify({"response": "입력을 이해하지 못했어요. 다시 한번 말씀해 주세요."})

@app.route('/user_state')
def get_user_state():
    user_state = session.get('user_state', {})
    return jsonify(user_state)

@app.route('/user_state', methods=['POST'])
def set_user_state():
    data = request.get_json(force=True)
    user_state = session.get('user_state', {})
    for k in ['destination', 'destination_city', 'interest', 'duration']:
        if k in data:
            user_state[k] = data[k]
    session['user_state'] = user_state
    return jsonify({'result': 'ok', 'user_state': user_state})

if __name__ == "__main__":
    app.run(debug=True) 

