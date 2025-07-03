from fpdf import FPDF
import json
import os
import re
import warnings

warnings.filterwarnings("ignore", message="cmap value too big/small*")
warnings.filterwarnings("ignore", message="missing glyph.*")

HISTORY_FILE = "chat_history.json"

# 1. 대화 히스토리 저장/불러오기

def save_chat_history(user, message, response):
    data = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = []
    data.append({"user": user, "message": message, "response": response})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_chat_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

# 2. 일정 PDF로 저장하기
def remove_emoji_and_symbols(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002600-\U000026FF"  # Misc symbols
        "\U00002B50-\U00002B55"  # Stars etc
        "]+",
        flags=re.UNICODE
    )
    # 이모지 및 특수문자만 제거 (한글, 한자, 가타카나, 히라가나 등은 남김)
    text = emoji_pattern.sub('', text)
    # 기타 제어문자, 특수문자 추가 제거(원하면 확장 가능)
    text = re.sub(r'[\u200d\u200c\ufe0f]', '', text)  # zero-width joiner 등
    return text

class PDFGenerator:
    def __init__(self, title="여행 일정표", font_path=None, font_name="NanumGothic"):
        self.pdf = FPDF()
        self.pdf.add_page()
        if font_path is None:
            font_path = os.path.join(os.path.dirname(__file__), "NanumGothic-Regular.ttf")
        self.pdf.add_font(font_name, "", font_path, uni=True)
        self.pdf.set_font(font_name, size=12)
        self.pdf.cell(200, 10, remove_emoji_and_symbols(title), ln=True, align="C")

    def add_schedule(self, schedule_text):
       print("=== PDF에 들어가는 원본 ===")
       print(schedule_text)
       self.pdf.set_font(self.pdf.font_family, size=12)
       for line in schedule_text.split("\n"):
           clean_line = remove_emoji_and_symbols(line)
           self.pdf.multi_cell(0, 10, clean_line)

    def output(self, filename="travel_schedule.pdf"):
        self.pdf.output(filename)
        return filename

# 3. 여행지에 지도 링크 포함시키기

def extract_place(line):
    # 1. **굵은 글씨** 패턴
    bold_match = re.search(r"\*\*(.+?)\*\*", line)
    if bold_match:
        return bold_match.group(1).strip()
    # 2. at/Visit/to 패턴
    at_match = re.search(r"(?:at|to|Visit|Head to|Go to) ([A-Za-z가-힣0-9·\-\(\) ]+)", line)
    if at_match:
        return at_match.group(1).strip()
    # 3. 괄호 안 장소
    paren_match = re.search(r"\(([^)]+)\)", line)
    if paren_match and len(paren_match.group(1)) > 2:
        return paren_match.group(1).strip()
    # 4. * 뒤 텍스트
    star_match = re.search(r"\*\s*([A-Za-z가-힣0-9·\-\(\) ]+)", line)
    if star_match:
        return star_match.group(1).strip()
    return None

def format_schedule_places(schedule_text):
    # 빈 응답 처리
    if not schedule_text or schedule_text.strip() == "":
        return "여행 일정을 생성할 수 없습니다. 다시 시도해주세요."
    
    # Day별로 장소만 추출해서 1번: 장소, 2번: 장소, ... 형식으로 반환
    lines = schedule_text.split("\n")
    places = []
    for line in lines:
        place = extract_place(line)
        if place:
            places.append(place)
    
    # 장소가 추출되지 않은 경우 원본 텍스트 반환
    if not places:
        return schedule_text
    
    return "\n".join([f"{i+1}번: {p}" for i, p in enumerate(places)])

def generate_map_links(schedule_text):
    lines = schedule_text.split("\n")
    map_lines = []
    for line in lines:
        place = extract_place(line)
        if place:
            url = f"https://www.google.com/maps/search/{place.replace(' ', '+')}"
            map_lines.append(f"{line}\n📍 지도보기: {url}")
        else:
            map_lines.append(line)
    return "\n".join(map_lines)

# 사용 예시 (Flask 연동)
# response = result
# mapped = generate_map_links(response)
# save_chat_history(message, mapped, response)
# pdf = PDFGenerator()
# pdf.add_schedule(mapped)
# pdf.output("my_trip.pdf") 