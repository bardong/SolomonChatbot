def detect_language(text):
    # 더 정확한 언어 감지
    import re
    
    # 한글 문자 감지
    korean_chars = len(re.findall(r'[가-힣]', text))
    # 영어 단어 감지
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    # 중국어 문자 감지
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 일본어 문자 감지
    japanese_chars = len(re.findall(r'[\u3040-\u30ff]', text))
    
    print(f"[DEBUG] Language detection - Korean: {korean_chars}, English words: {english_words}, Chinese: {chinese_chars}, Japanese: {japanese_chars}")
    
    # 순수 영어 문장인 경우 (영어 단어만 있고 다른 언어 문자가 없음)
    if english_words > 0 and korean_chars == 0 and chinese_chars == 0 and japanese_chars == 0:
        print(f"[DEBUG] Detected as English (pure English text)")
        return 'en'
    
    # 가장 많은 문자를 가진 언어로 판단
    char_counts = {
        'ko': korean_chars,
        'en': english_words,
        'zh': chinese_chars,
        'ja': japanese_chars
    }
    
    # 가장 많은 문자를 가진 언어 반환
    max_lang = max(char_counts.items(), key=lambda x: x[1])[0]
    
    # 문자가 없으면 기본값
    if char_counts[max_lang] == 0:
        return 'ko'
    
    print(f"[DEBUG] Detected as {max_lang} (most characters)")
    return max_lang

def wants_language_reply(message):
    lower = message.lower()
    print(f"[DEBUG] Checking language request for: {message}")
    
    # 한국어 요청 패턴들
    korean_patterns = [
        "한국어로 대답해줘", "한국어로 말해줘", "한국어로 안내해줘", "한국어로 설명해줘",
        "한글로 대답해줘", "한글로 말해줘", "한글로 안내해줘", "한글로 설명해줘",
        "한국어로", "한글로"
    ]
    
    # 영어 요청 패턴들
    english_patterns = [
        "영어로 대답해줘", "영어로 말해줘", "영어로 안내해줘", "영어로 설명해줘",
        "영어로", "please answer in english", "answer in english"
    ]
    
    # 중국어 요청 패턴들
    chinese_patterns = [
        "중국어로 대답해줘", "중국어로 말해줘", "중국어로 안내해줘", "중국어로 설명해줘",
        "중국어로", "please answer in chinese", "answer in chinese"
    ]
    
    # 일본어 요청 패턴들
    japanese_patterns = [
        "일본어로 대답해줘", "일본어로 말해줘", "일본어로 안내해줘", "일본어로 설명해줘",
        "일본어로", "please answer in japanese", "answer in japanese"
    ]
    
    # 패턴 매칭
    for pattern in korean_patterns:
        if pattern in message:
            print(f"[DEBUG] Korean language request detected: {pattern}")
            return 'ko'
    
    for pattern in english_patterns:
        if pattern.lower() in lower:
            print(f"[DEBUG] English language request detected: {pattern}")
            return 'en'
    
    for pattern in chinese_patterns:
        if pattern in message:
            print(f"[DEBUG] Chinese language request detected: {pattern}")
            return 'zh'
    
    for pattern in japanese_patterns:
        if pattern in message:
            print(f"[DEBUG] Japanese language request detected: {pattern}")
            return 'ja'
    
    print(f"[DEBUG] No language request detected")
    return None

def get_interest_question(lang):
    if lang == 'en':
        return "What are you most interested in for your trip? (e.g., food, nature, culture, shopping, etc.)"
    if lang == 'zh':
        return "您对旅行最感兴趣的是什么？（例如：美食、自然、文化、购物等）"
    if lang == 'ja':
        return "ご旅行で最も興味があることは何ですか？（例：グルメ、自然、文化、ショッピングなど）"
    return "여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)" 