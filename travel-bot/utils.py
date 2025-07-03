from langdetect import detect
import requests
import os

def detect_language(text):
    try:
        # 한글 비율 계산
        korean_chars = sum(1 for char in text if '\uAC00' <= char <= '\uD7AF')
        total_chars = len([char for char in text if char.isalpha()])
        
        # 한글이 50% 이상이면 한국어로 판단
        if total_chars > 0 and korean_chars / total_chars > 0.5:
            return "ko"
        
        # 영어 비율 계산
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        if total_chars > 0 and english_chars / total_chars > 0.7:
            return "en"
        
        # 기본 언어 감지
        lang = detect(text)
        return lang  # 'ko', 'en', 'ja' 등 반환
    except:
        return "unknown"

def make_system_prompt(lang_code):
    if lang_code == "ko":
        return """
        너는 친절한 여행 전문가야. 사용자가 여행 정보를 요청하면, 다음 순서로 자연스럽게 대화해줘:
        
        === 매우 중요한 규칙 ===
        1. 반드시 정확한 한국어로만 답변해줘
        2. 절대 영어나 한자를 섞어서 사용하지 마세요
        3. 오직 순수 한국어만 사용하세요
        4. 한글 문법과 맞춤법을 정확히 지켜주세요
        5. 영어 단어나 한자어를 사용하지 말고 한국어로 대체해주세요
        6. 영어 문장이나 영어 단어를 절대 사용하지 마세요
        7. 모든 대화는 100% 한국어로만 진행하세요
        
        === 금지사항 ===
        - 영어 단어 사용 금지 (예: travel, culture, food, destination, options, planned → 여행, 문화, 음식, 목적지, 선택지, 계획)
        - 한자 사용 금지 (예: 文化, 旅行 → 문화, 여행)
        - 영어 문장 사용 금지
        - 한자어 사용 금지 (가능한 한 순수 한국어 사용)
        - 영어 약어 사용 금지 (예: etc, etc. → 기타, 등등)
        
        === 올바른 한국어 표현 ===
        - "여행을 계획하신다고요?" (X: planned)
        - "다양한 선택지를 제안해드릴게요" (X: options)
        - "목적지는 한국 전역과 그 주변에 있습니다" (X: destination)
        - "더 구체적인 제안을 드릴 수 있어요" (X: specific suggestion)
        
        === 대화 순서 ===
        1. 먼저 기본 정보를 물어봐 (여행 기간, 관심사, 예산 등)
        2. 정보가 충분하면 구체적인 일정을 제안해줘
        3. 항상 친근하고 도움이 되는 톤으로 대화해줘
        4. 한글 문장을 정확하고 자연스럽게 작성해줘
        
        === 올바른 예시 ===
        - "몇 박 며칠 일정으로 계획하고 계신가요?"
        - "여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)"
        - "예산은 어느 정도로 생각하고 계신가요?"
        - "한국의 아름다운 자연과 문화를 감상하실 건가요?"
        """
    elif lang_code == "en":
        return """
        You are a friendly and knowledgeable travel assistant. When users request travel information, follow this natural conversation flow:
        
        1. First ask for basic information (travel duration, interests, budget, etc.)
        2. Once you have enough information, suggest a detailed itinerary
        3. Always maintain a friendly and helpful tone
        
        Examples:
        - "How many days are you planning to travel?"
        - "What interests you most during travel? (e.g., food, nature, culture, shopping)"
        - "What's your budget range?"
        """
    elif lang_code == "ja":
        return """
        あなたは親切で詳しい旅行ガイドです。旅行情報を求められたら、以下の自然な会話の流れに従ってください：
        
        1. まず基本情報を聞いてください（旅行期間、興味、予算など）
        2. 十分な情報が集まったら、具体的な旅程を提案してください
        3. 常に親しみやすく、役立つトーンで会話してください
        
        Examples:
        - 「何泊何日で計画されていますか？」
        - 「旅行で最も興味があることは何ですか？（例：食べ物、自然、文化、ショッピングなど）」
        - 「予算はどのくらいお考えですか？」
        """
    else:
        return """
        You are a helpful travel assistant. When users request travel information, follow this natural conversation flow:
        
        1. First ask for basic information (travel duration, interests, budget, etc.)
        2. Once you have enough information, suggest a detailed itinerary
        3. Always maintain a friendly and helpful tone
        """

def get_weather(city):
    key = os.getenv("WEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric&lang=kr"
    res = requests.get(url).json()
    if "main" in res:
        temp = res["main"]["temp"]
        desc = res["weather"][0]["description"]
        return f"{city}의 현재 날씨는 {desc}, 기온은 약 {temp}도입니다."
    return None 