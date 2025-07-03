import re

def extract_city_from_message(text):
    print(f"[DEBUG] extract_city_from_message called with: {text}")
    
    # 국가 목록 (도시보다 우선)
    countries = [
        "한국", "대한민국", "korea", "south korea", "japan", "일본", "china", "중국", 
        "usa", "미국", "united states", "america", "uk", "영국", "united kingdom", 
        "france", "프랑스", "germany", "독일", "italy", "이탈리아", "spain", "스페인",
        "thailand", "태국", "vietnam", "베트남", "singapore", "싱가포르", "malaysia", "말레이시아",
        "australia", "호주", "canada", "캐나다", "new zealand", "뉴질랜드"
    ]
    
    # 메시지에서 국가명 찾기 (도시보다 우선)
    for country in countries:
        if country.lower() in text.lower():
            print(f"[DEBUG] Found country: {country} in text: {text}")
            return country
    
    print(f"[DEBUG] No country found in text: {text}")
    
    # 한국 주요 도시 목록
    korean_cities = [
        "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
        "수원", "고양", "용인", "창원", "포항", "부천", "안산", "안양",
        "남양주", "평택", "시흥", "김포", "하남", "오산", "구리", "군포",
        "의왕", "과천", "의정부", "동두천", "가평", "양평", "여주", "이천",
        "안성", "평창", "정선", "철원", "화천", "양구", "인제", "고성",
        "속초", "양양", "강릉", "동해", "삼척", "태백", "횡성", "원주",
        "영월", "정선", "단양", "제천", "청주", "보은", "옥천", "영동",
        "증평", "진천", "괴산", "음성", "단양", "충주", "제천", "청주",
        "보은", "옥천", "영동", "증평", "진천", "괴산", "음성", "단양",
        "전주", "군산", "익산", "정읍", "남원", "김제", "완주", "진안",
        "무주", "장수", "임실", "순창", "고창", "부안", "여수", "순천",
        "광양", "담양", "곡성", "구례", "고흥", "보성", "화순", "장흥",
        "강진", "해남", "영암", "무안", "함평", "영광", "장성", "완도",
        "진도", "신안", "마산", "창원", "진주", "통영", "사천", "김해",
        "밀양", "거제", "양산", "의령", "함안", "창녕", "고성", "남해",
        "하동", "산청", "함양", "거창", "합천", "제주", "서귀포"
    ]
    
    # 메시지에서 도시명 찾기
    for city in korean_cities:
        if city in text:
            return city
    
    # 도시명을 찾지 못한 경우 기존 로직 사용
    city_pattern = r"([가-힣]{2,}|[A-Za-z]{2,})"
    candidates = re.findall(city_pattern, text)
    
    # 일반적인 영어 단어들 제외
    common_words = ["want", "travel", "to", "from", "with", "and", "or", "the", "a", "an", "in", "on", "at", "for", "of", "by", "with", "about", "like", "go", "visit", "see", "visit", "explore", "tour", "trip", "vacation", "holiday"]
    
    print(f"[DEBUG] City candidates: {candidates}")
    
    for i, word in enumerate(candidates):
        if word.lower() in common_words:
            print(f"[DEBUG] Skipping common word: {word}")
            continue
        if word in ["여행", "일정"] and i > 0:
            print(f"[DEBUG] Found travel keyword, returning previous: {candidates[i-1]}")
            return candidates[i-1]
    
    # 유효한 도시명만 반환
    for candidate in candidates:
        if candidate.lower() not in common_words:
            print(f"[DEBUG] Returning valid city: {candidate}")
            return candidate
    
    print(f"[DEBUG] No valid city found")
    return None 