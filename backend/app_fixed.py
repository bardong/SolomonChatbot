import os
import re
import random
import json
from flask import Flask, request, jsonify, session, send_file, send_from_directory
from flask_cors import CORS
from utils import use_ollama, get_hf_response, get_ollama_response, check_ollama_status
from extended_features import generate_pdf_from_chat_history, remove_emoji_and_symbols
import threading
import time
from datetime import datetime
import requests
from langdetect import detect
from llm import get_ollama_response, get_hf_response

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
CORS(app)

# 세션 초기화
@app.before_request
def before_request():
    if 'user_state' not in session:
        session['user_state'] = {}

# ====== 국가별 도시 정보 ======
COUNTRY_ATTRACTIONS = {
    "한국": {
        "name": "한국",
        "greeting": "안녕하세요!",
        "popular": "인기 도시로는 서울, 부산, 제주도, 경주, 전주, 여수, 강릉, 춘천 등이 있습니다.",
        "cities": ["서울", "부산", "제주도", "경주", "전주", "여수", "강릉", "춘천", "대구", "인천", "광주", "대전", "울산", "수원", "고양", "용인", "창원", "포항", "천안", "청주"],
        "cities_en": ["Seoul", "Busan", "Jeju Island", "Gyeongju", "Jeonju", "Yeosu", "Gangneung", "Chuncheon", "Daegu", "Incheon", "Gwangju", "Daejeon", "Ulsan", "Suwon", "Goyang", "Yongin", "Changwon", "Pohang", "Cheonan", "Cheongju"],
        "cities_ja": ["ソウル", "釜山", "済州島", "慶州", "全州", "麗水", "江陵", "春川", "大邱", "仁川", "光州", "大田", "蔚山", "水原", "高陽", "龍仁", "昌原", "浦項", "天安", "清州"],
        "cities_zh": ["首尔", "釜山", "济州岛", "庆州", "全州", "丽水", "江陵", "春川", "大邱", "仁川", "光州", "大田", "蔚山", "水原", "高阳", "龙仁", "昌原", "浦项", "天安", "清州"]
    },
    "일본": {
        "name": "일본",
        "greeting": "こんにちは！",
        "popular": "인기 도시로는 도쿄, 오사카, 교토, 나고야, 삿포로, 후쿠오카, 고베, 요코하마 등이 있습니다.",
        "cities": ["도쿄", "오사카", "교토", "나고야", "삿포로", "후쿠오카", "고베", "요코하마", "가와사키", "교토", "사이타마", "히로시마", "센다이", "지바", "기타큐슈", "사카이", "니가타", "하마마쓰", "구마모토", "사가미하라"],
        "cities_en": ["Tokyo", "Osaka", "Kyoto", "Nagoya", "Sapporo", "Fukuoka", "Kobe", "Yokohama", "Kawasaki", "Saitama", "Hiroshima", "Sendai", "Chiba", "Kitakyushu", "Sakai", "Niigata", "Hamamatsu", "Kumamoto", "Sagamihara"],
        "cities_ja": ["東京", "大阪", "京都", "名古屋", "札幌", "福岡", "神戸", "横浜", "川崎", "埼玉", "広島", "仙台", "千葉", "北九州", "堺", "新潟", "浜松", "熊本", "相模原"],
        "cities_zh": ["东京", "大阪", "京都", "名古屋", "札幌", "福冈", "神户", "横滨", "川崎", "埼玉", "广岛", "仙台", "千叶", "北九州", "堺", "新潟", "滨松", "熊本", "相模原"]
    },
    "중국": {
        "name": "중국",
        "greeting": "你好！",
        "popular": "인기 도시로는 베이징, 상하이, 광저우, 선전, 항저우, 청두, 시안, 난징 등이 있습니다.",
        "cities": ["베이징", "상하이", "광저우", "선전", "항저우", "청두", "시안", "난징", "우한", "충칭", "톈진", "칭다오", "다롄", "닝보", "푸저우", "하얼빈", "쿤밍", "란저우", "시닝", "우루무치"],
        "cities_en": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou", "Chengdu", "Xi'an", "Nanjing", "Wuhan", "Chongqing", "Tianjin", "Qingdao", "Dalian", "Ningbo", "Fuzhou", "Harbin", "Kunming", "Lanzhou", "Xining", "Urumqi"],
        "cities_ja": ["北京", "上海", "広州", "深セン", "杭州", "成都", "西安", "南京", "武漢", "重慶", "天津", "青島", "大連", "寧波", "福州", "ハルビン", "昆明", "蘭州", "西寧", "ウルムチ"],
        "cities_zh": ["北京", "上海", "广州", "深圳", "杭州", "成都", "西安", "南京", "武汉", "重庆", "天津", "青岛", "大连", "宁波", "福州", "哈尔滨", "昆明", "兰州", "西宁", "乌鲁木齐"]
    }
}

def is_country(text):
    """입력된 텍스트가 국가인지 확인"""
    countries = ["한국", "일본", "중국", "미국", "영국", "프랑스", "독일", "이탈리아", "스페인", "태국", "베트남", "싱가포르", "호주", "캐나다", "뉴질랜드", "Korea", "Japan", "China", "USA", "America", "United States", "UK", "United Kingdom", "France", "Germany", "Italy", "Spain", "Thailand", "Vietnam", "Singapore", "Australia", "Canada", "New Zealand", "韓国", "日本", "中国", "アメリカ", "イギリス", "フランス", "ドイツ", "イタリア", "スペイン", "タイ", "ベトナム", "シンガポール", "オーストラリア", "カナダ", "ニュージーランド", "韩国", "日本", "中国", "美国", "英国", "法国", "德国", "意大利", "西班牙", "泰国", "越南", "新加坡", "澳大利亚", "加拿大", "新西兰"]
    return text in countries

def get_country_info(country_name, lang="ko"):
    """국가 정보를 가져오는 함수"""
    # 국가명 매핑
    country_mapping = {
        "korea": "한국", "south korea": "한국", "japan": "일본", "china": "중국",
        "usa": "미국", "america": "미국", "united states": "미국",
        "uk": "영국", "united kingdom": "영국", "france": "프랑스",
        "germany": "독일", "italy": "이탈리아", "spain": "스페인",
        "thailand": "태국", "vietnam": "베트남", "singapore": "싱가포르",
        "malaysia": "말레이시아", "australia": "호주", "canada": "캐나다",
        "new zealand": "뉴질랜드",
        "韓国": "한국", "日本": "일본", "中国": "중국", "アメリカ": "미국",
        "イギリス": "영국", "フランス": "프랑스", "ドイツ": "독일",
        "イタリア": "이탈리아", "スペイン": "스페인", "タイ": "태국",
        "ベトナム": "베트남", "シンガポール": "싱가포르", "オーストラリア": "호주",
        "カナダ": "캐나다", "ニュージーランド": "뉴질랜드",
        "韩国": "한국", "日本": "일본", "中国": "중국", "美国": "미국",
        "英国": "영국", "法国": "프랑스", "德国": "독일",
        "意大利": "이탈리아", "西班牙": "스페인", "泰国": "태국",
        "越南": "베트남", "新加坡": "싱가포르", "澳大利亚": "호주",
        "加拿大": "캐나다", "新西兰": "뉴질랜드"
    }
    
    # 매핑된 국가명으로 변환
    for mapped_name, kor_name in country_mapping.items():
        if mapped_name.lower() in country_name.lower():
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

    # 세션에서 대화 상태 불러오기
    user_state = session.get("user_state", {})

    # --- 언어 감지 및 설정 ---
    detected_lang = detect_language_request(message)
    if detected_lang != "ko":
        session['preferred_language'] = detected_lang
        print(f"[DEBUG] Language change detected: {detected_lang}")
        
        # user_state에 정보가 있으면 해당 언어로 LLM에 질문
        if user_state and any(user_state.values()):
            print(f"[DEBUG] User state exists, generating LLM response in {detected_lang}")
            
            # 목적지 정보 구성
            destination_info = user_state.get("destination", "")
            if "destination_city" in user_state and user_state["destination_city"]:
                if user_state["destination"] != user_state["destination_city"]:
                    destination_info = f"{user_state['destination']} {user_state['destination_city']}"
                else:
                    destination_info = user_state["destination"]
            
            # 언어별 프롬프트 생성
            if detected_lang == "en":
                prompt = f"""You are a travel expert. Please answer ONLY in English.

Travel Information:
Destination: {destination_info}
Interest: {user_state.get('interest', '')}
Duration: {user_state.get('duration', '')}

Please create a detailed travel itinerary for {destination_info} focusing on {user_state.get('interest', 'general tourism')} for {user_state.get('duration', 'a few days')}. Include specific places, restaurants, and activities for each day."""
            
            elif detected_lang == "ja":
                prompt = f"""あなたは旅行の専門家です。必ず日本語で答えてください。

旅行情報：
目的地：{destination_info}
興味：{user_state.get('interest', '')}
期間：{user_state.get('duration', '')}

{destination_info}の{user_state.get('interest', '一般的な観光')}に焦点を当てた{user_state.get('duration', '数日間')}の詳細な旅行計画を作成してください。各日の具体的な場所、レストラン、アクティビティを含めてください。"""
            
            elif detected_lang == "zh":
                prompt = f"""你是旅游专家。请只用中文回答。

旅游信息：
目的地：{destination_info}
兴趣：{user_state.get('interest', '')}
行程：{user_state.get('duration', '')}

请为{destination_info}创建一个详细的旅游行程，重点关注{user_state.get('interest', '一般旅游')}，行程{user_state.get('duration', '几天')}。请包含每天的具体地点、餐厅和活动。"""
            
            try:
                if use_ollama():
                    result = get_ollama_response(prompt)
                else:
                    result = get_hf_response(prompt)
                
                # 언어 변경 확인 메시지 추가
                lang_confirmation = {
                    "en": "I'll respond in English from now on.\n\n",
                    "ja": "これから日本語でお答えします。\n\n",
                    "zh": "从现在开始我将用中文回答。\n\n"
                }
                
                return jsonify({"response": lang_confirmation[detected_lang] + result})
                
            except Exception as e:
                print(f"LLM request error during language change: {e}")
                # LLM 요청 실패 시 기본 응답
                if detected_lang == "en":
                    return jsonify({"response": "I'll respond in English from now on. How can I help you with your travel plans?"})
                elif detected_lang == "ja":
                    return jsonify({"response": "これから日本語でお答えします。旅行のご相談は何でしょうか？"})
                elif detected_lang == "zh":
                    return jsonify({"response": "从现在开始我将用中文回答。您有什么旅行计划需要帮助吗？"})
        
        # user_state가 비어있으면 기본 응답
        else:
            if detected_lang == "en":
                return jsonify({"response": "I'll respond in English from now on. Which city or country would you like to travel to?"})
            elif detected_lang == "ja":
                return jsonify({"response": "これから日本語でお答えします。どの都市や国に行きたいですか？"})
            elif detected_lang == "zh":
                return jsonify({"response": "从现在开始我将用中文回答。您想去哪个城市或国家？"})
    
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

    # --- 기존 로직 계속 ---
    # 여기에 기존의 나머지 로직을 추가하세요...

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000) 