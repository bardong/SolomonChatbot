import re
import random
from datetime import datetime, timedelta
import os
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import json
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

# === API 키 직접 하드코딩 (실제 서비스키로 교체 필요) ===
load_dotenv()
BUS_API_KEY = os.getenv('BUS_API_KEY') or ''
SUBWAY_API_KEY = os.getenv('SUBWAY_API_KEY') or ''
KYX_API_KEY = os.getenv('KYX_API_KEY') or ''

# 주요 터미널명→코드 변환 예시 (실제 필요시 확장)
TERMINAL_CODE_MAP = {
    "서울고속터미널": "NAEK010",
    "서울터미널": "NAEK010",
    "서울고속버스터미널": "NAEK010",
    "동서울터미널": "NAEK020",
    "동서울고속터미널": "NAEK020",
    "센트럴시티터미널": "NAEK030",
    "부산종합터미널": "NAEK400",
    "부산고속터미널": "NAEK400",
    "부산고속버스터미널": "NAEK400",
    "동대구터미널": "NAEK300",
    "동대구고속터미널": "NAEK300",
    "대전복합터미널": "NAEK050",
    "광주유스퀘어": "NAEK160",
    "광주고속터미널": "NAEK160",
    "울산터미널": "NAEK430",
    "울산고속터미널": "NAEK430",
    "강릉고속버스터미널": "NAEK550",
    "전주고속버스터미널": "NAEK340",
    "진주고속버스터미널": "NAEK520",
    "마산고속버스터미널": "NAEK480",
    "창원고속버스터미널": "NAEK490",
    "창원": "NAEK490",
    "창원터미널": "NAEK490",
    "포항고속버스터미널": "NAEK370",
    "순천종합버스터미널": "NAEK620",
    "여수종합버스터미널": "NAEK630",
    "원주고속버스터미널": "NAEK570",
    "춘천고속버스터미널": "NAEK590",
    "속초고속버스터미널": "NAEK600",
    "인천종합터미널": "NAEK070",
    "군산고속버스터미널": "NAEK350",
    "목포종합버스터미널": "NAEK660",
    "해운대고속버스터미널": "NAEK410",
    "김해여객터미널": "NAEK470",
    "구미고속버스터미널": "NAEK320",
    "안동터미널": "NAEK310",
    "영주고속버스터미널": "NAEK330",
    "경주고속버스터미널": "NAEK360",
    "통영종합버스터미널": "NAEK530",
    "거제고속버스터미널": "NAEK540",
    "사천고속버스터미널": "NAEK510",
    "남원고속버스터미널": "NAEK610",
    "정읍고속버스터미널": "NAEK380",
    "익산고속버스터미널": "NAEK390",
    "공주고속버스터미널": "NAEK240",
    "천안고속버스터미널": "NAEK220",
    "청주고속버스터미널": "NAEK210",
    "제천고속버스터미널": "NAEK250",
    "충주고속버스터미널": "NAEK260",
    "태백고속버스터미널": "NAEK580",
    "동해고속버스터미널": "NAEK560",
    "삼척고속버스터미널": "NAEK610",
    "영덕고속버스터미널": "NAEK350",
    "영광고속버스터미널": "NAEK670",
    "고흥고속버스터미널": "NAEK680",
    "광양고속버스터미널": "NAEK690",
    "보성고속버스터미널": "NAEK700",
    "담양고속버스터미널": "NAEK710",
    "화순고속버스터미널": "NAEK720",
    "나주고속버스터미널": "NAEK730",
    "무안고속버스터미널": "NAEK740",
    "신안고속버스터미널": "NAEK750",
    "고성고속버스터미널": "NAEK760",
    "양양고속버스터미널": "NAEK770",
    "홍천고속버스터미널": "NAEK780",
    "횡성고속버스터미널": "NAEK790",
    "평창고속버스터미널": "NAEK800",
    "정선고속버스터미널": "NAEK810",
    "영월고속버스터미널": "NAEK820",
    "동두천고속버스터미널": "NAEK830",
    "의정부고속버스터미널": "NAEK840",
    "파주고속버스터미널": "NAEK850",
    "고양고속버스터미널": "NAEK860",
    "김포고속버스터미널": "NAEK870",
    "부천고속버스터미널": "NAEK880",
    "안산고속버스터미널": "NAEK890",
    "시흥고속버스터미널": "NAEK900",
    "수원고속버스터미널": "NAEK910",
    "용인고속버스터미널": "NAEK920",
    "성남고속버스터미널": "NAEK930",
    "안양고속버스터미널": "NAEK940",
    "과천고속버스터미널": "NAEK950",
    "군포고속버스터미널": "NAEK960",
    "의왕고속버스터미널": "NAEK970",
    "오산고속버스터미널": "NAEK980",
    "평택고속버스터미널": "NAEK990",
    "이천고속버스터미널": "NAEK1000",
    "여주고속버스터미널": "NAEK1010",
    "양평고속버스터미널": "NAEK1020",
    "하남고속버스터미널": "NAEK1030",
    "구리고속버스터미널": "NAEK1040",
    "남양주고속버스터미널": "NAEK1050",
    "포천고속버스터미널": "NAEK1060",
    "가평고속버스터미널": "NAEK1070",
    "연천고속버스터미널": "NAEK1080",
    "강화고속버스터미널": "NAEK1090",
    "옹진고속버스터미널": "NAEK1100",
    # ... 필요시 추가 ...
}

# 주요 지하철역명→코드 변환 예시 (실제 필요시 확장)
SUBWAY_STATION_CODE_MAP = {
    "서울역": "0150",
    "강남역": "0222",
    "홍대입구역": "0263",
    "잠실역": "0242",
    "신촌역": "0213",
    "시청역": "0151",
    "종로3가역": "0195",
    "고속터미널역": "0233",
    "교대역": "0221",
    "건대입구역": "0217",
    "사당역": "0226",
    "왕십리역": "0240",
    "서울대입구역": "0229",
    "합정역": "0262",
    "신림역": "0231",
    "신도림역": "0238",
    "구로디지털단지역": "0236",
    "노량진역": "0219",
    "신설동역": "0192",
    "동대문역사문화공원역": "0216",
    # ... 필요시 추가 ...
}

# 주요 공항명→코드 변환 예시 (실제 필요시 확장)
AIRPORT_CODE_MAP = {
    "인천국제공항": "ICN",
    "김포국제공항": "GMP",
    "김해국제공항": "PUS",
    "제주국제공항": "CJU",
    # ... 필요시 추가 ...
}

# 대표 도시명→대표 터미널명 매핑 (확장 가능)
CITY_TO_TERMINAL = {
    "부산": "부산종합터미널",
    "부산터미널": "부산종합터미널",
    "부산고속버스터미널": "부산종합터미널",
    "서울": "서울고속터미널",
    "서울터미널": "서울고속터미널",
    "서울고속버스터미널": "서울고속터미널",
    "센트럴시티": "센트럴시티터미널",
    "동서울": "동서울터미널",
    "동서울터미널": "동서울터미널",
    "대구": "동대구터미널",
    "대구터미널": "동대구터미널",
    "동대구": "동대구터미널",
    "광주": "광주유스퀘어",
    "광주터미널": "광주유스퀘어",
    "광주유스퀘어": "광주유스퀘어",
    "울산": "울산터미널",
    "울산터미널": "울산터미널",
    "대전": "대전복합터미널",
    "대전터미널": "대전복합터미널",
    "대전고속버스터미널": "대전복합터미널",
    "창원": "창원고속버스터미널",
    "창원터미널": "창원고속버스터미널",
    "전주": "전주고속버스터미널",
    "전주터미널": "전주고속버스터미널",
    "전주고속버스터미널": "전주고속버스터미널",
    # ... 필요시 추가 ...
}

# TERMINAL_CODE_MAP의 모든 key를 CITY_TO_TERMINAL에 추가
for _k, _v in TERMINAL_CODE_MAP.items():
    if _k not in CITY_TO_TERMINAL:
        CITY_TO_TERMINAL[_k] = _k

# KTX 역명 매핑 (사용자 입력 → 공식명)
KTX_STATION_NAME_MAP = {
    "상봉역": "상봉",
    "상봉": "상봉",
    "서빙고역": "서빙고",
    "서빙고": "서빙고",
    "옥수역": "옥수",
    "옥수": "옥수",
    "왕십리역": "왕십리",
    "왕십리": "왕십리",
    "청량리역": "청량리",
    "청량리": "청량리",
    "광운대역": "광운대",
    "광운대": "광운대",
    "서울역": "서울",
    "서울": "서울",
    "용산역": "용산",
    "용산": "용산",
    "노량진역": "노량진",
    "노량진": "노량진",
    "영등포역": "영등포",
    "영등포": "영등포",
    "부강역": "부강",
    "부강": "부강",
    "조치원역": "조치원",
    "조치원": "조치원",
    "소정리역": "소정리",
    "소정리": "소정리",
    "전의역": "전의",
    "전의": "전의",
    "화명역": "화명",
    "화명": "화명",
    "구포역": "구포",
    "구포": "구포",
    "사상역": "사상",
    "사상": "사상",
    "부산역": "부산",
    "부산": "부산",
    "부전역": "부전",
    "부전": "부전",
    "동래역": "동래",
    "동래": "동래",
    "센텀역": "센텀",
    "센텀": "센텀",
    "신해운대역": "신해운대",
    "신해운대": "신해운대",
    "송정역": "송정",
    "송정": "송정",
    "기장역": "기장",
    "기장": "기장",
    "대구역": "대구",
    "대구": "대구",
    "동대구역": "동대구",
    "동대구": "동대구",
    "서대구역": "서대구",
    "서대구": "서대구",
    "주안역": "주안",
    "주안": "주안",
    "인천공항T2역": "인천공항T2",
    "인천공항T2": "인천공항T2",
    "검암역": "검암",
    "검암": "검암",
    "인천공항T1역": "인천공항T1",
    "인천공항T1": "인천공항T1",
    "광주송정역": "광주송정",
    "광주송정": "광주송정",
    "효천역": "효천",
    "효천": "효천",
    "서광주역": "서광주",
    "서광주": "서광주",
    "광주역": "광주",
    "광주": "광주",
    "극락강역": "극락강",
    "극락강": "극락강",
    "대전역": "대전",
    "대전": "대전",
    "서대전역": "서대전",
    "서대전": "서대전",
    "흑석리역": "흑석리",
    "흑석리": "흑석리",
    "신탄진역": "신탄진",
    "신탄진": "신탄진",
    "북울산역": "북울산",
    "북울산": "북울산",
    "울산(통도사)역": "울산(통도사)",
    "울산(통도사)": "울산(통도사)",
    "남창역": "남창",
    "남창": "남창",
    "덕하역": "덕하",
    "덕하": "덕하",
    "태화강역": "태화강",
    "태화강": "태화강",
    "효문역": "효문",
    "효문": "효문",
    "덕소역": "덕소",
    "덕소": "덕소",
    "아신역": "아신",
    "아신": "아신",
    "양평역": "양평",
    "양평": "양평",
    "용문역": "용문",
    "용문": "용문",
    "지평역": "지평",
    "지평": "지평",
    "석불역": "석불",
    "석불": "석불",
    "일신역": "일신",
    "일신": "일신",
    "매곡역": "매곡",
    "매곡": "매곡",
    "양동역": "양동",
    "양동": "양동",
    "삼산역": "삼산",
    "삼산": "삼산",
    "동화역": "동화",
    "동화": "동화",
    "만종역": "만종",
    "만종": "만종",
    "반곡역": "반곡",
    "반곡": "반곡",
    "신림역": "신림",
    "신림": "신림",
    "서원주역": "서원주",
    "서원주": "서원주",
    "원주역": "원주",
    "원주": "원주",
    "백마고지역": "백마고지",
    "백마고지": "백마고지",
    "백양리역": "백양리",
    "백양리": "백양리",
    "강촌역": "강촌",
    "강촌": "강촌",
    "옥천역": "옥천",
    "옥천": "옥천",
    "이원역": "이원",
    "이원": "이원",
    "지탄역": "지탄",
    "지탄": "지탄",
    "심천역": "심천",
    "심천": "심천",
    "각계역": "각계",
    "각계": "각계",
    "영동역": "영동",
    "영동": "영동",
    "황간역": "황간",
    "황간": "황간",
    "추풍령역": "추풍령",
    "추풍령": "추풍령",
    "봉양역": "봉양",
    "봉양": "봉양",
    "제천역": "제천",
    "제천": "제천",
    "계룡역": "계룡",
    "계룡": "계룡",
    "연산역": "연산",
    "연산": "연산",
    "논산역": "논산",
    "논산": "논산",
    "강경역": "강경",
    "강경": "강경",
    "아산역": "아산",
    "아산": "아산",
    "온양온천역": "온양온천",
    "온양온천": "온양온천",
    "신창역": "신창",
    "신창": "신창",
    "도고온천역": "도고온천",
    "도고온천": "도고온천",
    "신례원역": "신례원",
    "신례원": "신례원",
    "예산역": "예산",
    "예산": "예산",
    "용동역": "용동",
    "용동": "용동",
    "함열역": "함열",
    "함열": "함열",
    "익산역": "익산",
    "익산": "익산",
    "김제역": "김제",
    "김제": "김제",
    "신태인역": "신태인",
    "신태인": "신태인",
    "정읍역": "정읍",
    "정읍": "정읍",
    "삼례역": "삼례",
    "삼례": "삼례",
    "동산역": "동산",
    "동산": "동산",
    "전주역": "전주",
    "전주": "전주",
    "신리역": "신리",
    "신리": "신리",
    "백양사역": "백양사",
    "백양사": "백양사",
    "장성역": "장성",
    "장성": "장성",
    "나주역": "나주",
    "나주": "나주",
    "다시역": "다시",
    "다시": "다시",
    "무안역": "무안",
    "무안": "무안",
    "몽탄역": "몽탄",
    "몽탄": "몽탄",
    "일로역": "일로",
    "일로": "일로",
    "임성리역": "임성리",
    "임성리": "임성리",
    "목포역": "목포",
    "목포": "목포",
    "곡성역": "곡성",
    "곡성": "곡성",
    "김천역": "김천",
    "김천": "김천",
    "아포역": "아포",
    "아포": "아포",
    "구미역": "구미",
    "구미": "구미",
    "사곡역": "사곡",
    "사곡": "사곡",
    "약목역": "약목",
    "약목": "약목",
    "왜관역": "왜관",
    "왜관": "왜관",
    "신동역": "신동",
    "신동": "신동",
    "경산역": "경산",
    "경산": "경산",
    "남성현역": "남성현",
    "남성현": "남성현",
    "청도역": "청도",
    "청도": "청도",
    "상동역": "상동",
    "상동": "상동",
    "밀양역": "밀양",
    "밀양": "밀양",
    "삼랑진역": "삼랑진",
    "삼랑진": "삼랑진",
    "원동역": "원동",
    "원동": "원동",
    "물금역": "물금",
    "물금": "물금",
    "한림정역": "한림정",
    "한림정": "한림정",
    "진영역": "진영",
    "진영": "진영",
    "진례역": "진례",
    "진례": "진례",
    "창원중앙역": "창원중앙",
    "창원중앙": "창원중앙",
    "창원역": "창원",
    "창원": "창원",
    # ... 추가 가능 ...
}
# KTX 역 코드 매핑 (공식명 → nodeid)
KTX_STATION_CODE_MAP = {
    "상봉": "NAT020040",
    "서빙고": "NAT130036",
    "옥수": "NAT130070",
    "왕십리": "NAT130104",
    "청량리": "NAT130126",
    "광운대": "NAT130182",
    "서울": "NAT010000",
    "용산": "NAT010032",
    "노량진": "NAT010058",
    "영등포": "NAT010091",
    "부강": "NAT011403",
    "조치원": "NAT011298",
    "소정리": "NAT011079",
    "전의": "NAT011154",
    "화명": "NAT014244",
    "구포": "NAT014281",
    "사상": "NAT014331",
    "부산": "NAT014445",
    "부전": "NAT750046",
    "동래": "NAT750106",
    "센텀": "NAT750161",
    "신해운대": "NAT750189",
    "송정": "NAT750254",
    "기장": "NAT750329",
    "대구": "NAT013239",
    "동대구": "NAT013271",
    "서대구": "NAT013189",
    "주안": "NAT060231",
    "인천공항T2": "NATC30058",
    "검암": "NATC10325",
    "인천공항T1": "NATC10580",
    "광주송정": "NAT031857",
    "효천": "NAT882904",
    "서광주": "NAT882936",
    "광주": "NAT883012",
    "극락강": "NAT883086",
    "대전": "NAT011668",
    "서대전": "NAT030057",
    "흑석리": "NAT030173",
    "신탄진": "NAT011524",
    "북울산": "NAT750781",
    "울산(통도사)": "NATH13717",
    "남창": "NAT750560",
    "덕하": "NAT750653",
    "태화강": "NAT750726",
    "효문": "NAT750760",
    "덕소": "NAT020178",
    "아신": "NAT020471",
    "양평": "NAT020524",
    "용문": "NAT020641",
    "지평": "NAT020677",
    "석불": "NAT020717",
    "일신": "NAT020760",
    "매곡": "NAT020803",
    "양동": "NAT020845",
    "삼산": "NAT020884",
    "동화": "NAT020986",
    "만종": "NAT021033",
    "반곡": "NAT021175",
    "신림": "NAT021357",
    "서원주": "NAT020864",
    "원주": "NAT020947",
    "백마고지": "NAT130944",
    "백양리": "NAT140681",
    "강촌": "NAT140701",
    "옥천": "NAT011833",
    "이원": "NAT011916",
    "지탄": "NAT011972",
    "심천": "NAT012016",
    "각계": "NAT012054",
    "영동": "NAT012124",
    "황간": "NAT012270",
    "추풍령": "NAT012355",
    "봉양": "NAT021478",
    "제천": "NAT021549",
    "계룡": "NAT030254",
    "연산": "NAT030396",
    "논산": "NAT030508",
    "강경": "NAT030607",
    "아산": "NAT080045",
    "온양온천": "NAT080147",
    "신창": "NAT080216",
    "도고온천": "NAT080309",
    "신례원": "NAT080353",
    "예산": "NAT080402",
    "용동": "NAT030667",
    "함열": "NAT030718",
    "익산": "NAT030879",
    "김제": "NAT031056",
    "신태인": "NAT031179",
    "정읍": "NAT031314",
    "삼례": "NAT040133",
    "동산": "NAT040173",
    "전주": "NAT040257",
    "신리": "NAT040352",
    "백양사": "NAT031486",
    "장성": "NAT031638",
    "나주": "NAT031998",
    "다시": "NAT032099",
    "무안": "NAT032273",
    "몽탄": "NAT032313",
    "일로": "NAT032422",
    "임성리": "NAT032489",
    "목포": "NAT032563",
    "곡성": "NAT041072",
    "김천": "NAT012546",
    "아포": "NAT012700",
    "구미": "NAT012775",
    "사곡": "NAT012821",
    "약목": "NAT012903",
    "왜관": "NAT012968",
    "신동": "NAT013067",
    "경산": "NAT013395",
    "남성현": "NAT013542",
    "청도": "NAT013629",
    "상동": "NAT013747",
    "밀양": "NAT013841",
    "삼랑진": "NAT013967",
    "원동": "NAT014058",
    "물금": "NAT014150",
    "한림정": "NAT880099",
    "진영": "NAT880177",
    "진례": "NAT880179",
    "창원중앙": "NAT880281",
    "창원": "NAT880310",
    # ... 추가 가능 ...
}

def normalize_ktx_station_name(name):
    # 매핑 우선 적용
    if name in KTX_STATION_NAME_MAP:
        return KTX_STATION_NAME_MAP[name]
    # '역'으로 끝나면 '역' 제거
    if name.endswith("역"):
        return name[:-1]
    return name

def get_ktx_info(departure, arrival, date=None):
    api_key = KYX_API_KEY
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    # 사용자 입력 → 공식명 변환
    dep_official = normalize_ktx_station_name(departure)
    arr_official = normalize_ktx_station_name(arrival)
    # 공식명 → nodeid 변환 (없으면 공식명 그대로)
    dep_code = KTX_STATION_CODE_MAP.get(dep_official, dep_official)
    arr_code = KTX_STATION_CODE_MAP.get(arr_official, arr_official)
    url = (
        "http://apis.data.go.kr/1613000/TrainInfoService/getStrtpntAlocFndTrainInfo"
        f"?serviceKey={api_key}"
        f"&depPlaceId={dep_code}"
        f"&arrPlaceId={arr_code}"
        f"&depPlandTime={date}"
        f"&numOfRows=5"
        f"&_type=json"
    )
    print(f"[열차 출/도착지 기반 열차정보 API 호출 URL] {url}")
    def pad(s, width):
        import re
        length = 0
        for c in str(s):
            if re.match(r'[가-힣]', c):
                length += 2
            else:
                length += 1
        return str(s) + ' ' * (width - length)
    try:
        response = requests.get(url, verify=False)
        if response.status_code != 200:
            return f"열차 API 호출 오류: {response.status_code}"
        data = response.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if not items:
            return f"해당 구간의 실시간 열차 시간표를 찾을 수 없습니다."
        if isinstance(items, dict):
            items = [items]
        # 동적 열 너비 계산
        raw_rows = []
        for i, item in enumerate(items, 1):
            train_type = item.get("traingradename", "-")
            train_no = item.get("trainno", "-")
            dep_time = str(item.get("depplandtime", ""))
            arr_time = str(item.get("arrplandtime", ""))
            fare = item.get("adultcharge", "-")
            dep_fmt = f"{dep_time[8:10]}:{dep_time[10:12]}" if len(dep_time) >= 12 else dep_time
            arr_fmt = f"{arr_time[8:10]}:{arr_time[10:12]}" if len(arr_time) >= 12 else arr_time
            fare_fmt = f"{int(fare):,}원" if fare and fare != '-' and fare != 0 else "-"
            raw_rows.append([
                str(i), train_type, train_no, dep_fmt, arr_fmt, fare_fmt
            ])
        headers = ["번호", "열차종류", "열차번호", "출발시각", "도착시각", "요금"]
        # 각 열의 최대 길이 계산 (한글 2칸 처리)
        def get_width(s):
            import re
            length = 0
            for c in str(s):
                if re.match(r'[가-힣]', c):
                    length += 2
                else:
                    length += 1
            return length
        col_widths = [max([get_width(h)] + [get_width(row[i]) for row in raw_rows]) for i, h in enumerate(headers)]
        # 패딩 함수
        def pad(s, width):
            import re
            length = 0
            for c in str(s):
                if re.match(r'[가-힣]', c):
                    length += 2
                else:
                    length += 1
            return str(s) + ' ' * (width - length)
        # 헤더/구분선
        lines = []
        lines.append(' | '.join([pad(h, w) for h, w in zip(headers, col_widths)]))
        lines.append('-' * (sum(col_widths) + 3 * (len(headers)-1)))
        # 데이터
        for row in raw_rows:
            lines.append(' | '.join([pad(cell, w) for cell, w in zip(row, col_widths)]))
        return (
            f"🚄 {departure} → {arrival} 열차 시간표\n\n" +
            "```\n" +
            "\n".join(lines) +
            "\n```\n" +
            "\n※ 실제 예매/좌석 현황은 코레일/레츠코레일 등에서 확인하세요."
        )
    except Exception as e:
        return f"열차 API 호출 오류: {e}"

class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def extract_date_from_message(message):
    """
    사용자 입력에서 날짜(YYYYMMDD, '오늘', '지금', '내일', '31일', '6월 10일' 등)를 추출하는 함수
    """
    today = datetime.now()
    # '지금', '오늘' → 오늘 날짜
    if re.search(r"지금|오늘", message):
        return today.strftime("%Y%m%d")
    # '내일' → 내일 날짜
    if "내일" in message:
        return (today + timedelta(days=1)).strftime("%Y%m%d")
    # '31일', '6월 10일' 등
    m = re.search(r"(\d{1,2})월\s*(\d{1,2})일", message)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = today.year
        # 이미 지난 달/일이면 내년으로 처리
        try:
            dt = datetime(year, month, day)
            if dt < today:
                dt = datetime(year+1, month, day)
            return dt.strftime("%Y%m%d")
        except:
            return None
    m = re.search(r"(\d{1,2})일", message)
    if m:
        day = int(m.group(1))
        month = today.month
        year = today.year
        try:
            dt = datetime(year, month, day)
            if dt < today:
                dt = datetime(year, month+1, day)
            return dt.strftime("%Y%m%d")
        except:
            return None
    # YYYYMMDD 직접 입력
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", message)
    if m:
        return m.group(0)
    return None

def normalize_terminal_name(name):
    # CITY_TO_TERMINAL로 먼저 변환
    for key in CITY_TO_TERMINAL:
        if key in name:
            name = CITY_TO_TERMINAL[key]
            break
    # TERMINAL_CODE_MAP 부분 일치 우선
    for key in TERMINAL_CODE_MAP:
        if key in name:
            return TERMINAL_CODE_MAP[key]
    # 정확 일치 fallback
    return TERMINAL_CODE_MAP.get(name, name)

def extract_bus_info(user_input):
    """
    사용자 입력에서 고속버스 정보 추출 (도시명만 입력해도 대표 터미널로 자동 변환)
    """
    # '고속버스 [출발지]에서 [도착지]까지' 패턴 우선 추출
    m = re.search(r"고속버스\s*([\w가-힣]+)에서\s*([\w가-힣]+)까지", user_input)
    if m:
        dep_city = m.group(1)
        arr_city = m.group(2)
        dep_terminal = CITY_TO_TERMINAL.get(dep_city, dep_city)
        arr_terminal = CITY_TO_TERMINAL.get(arr_city, arr_city)
        return "고속버스", dep_terminal, arr_terminal
    # '[출발지]에서 [도착지]까지.*고속버스' 패턴 (문장 내 고속버스)
    m = re.search(r"([\w가-힣]+)에서\s*([\w가-힣]+)까지.*고속버스", user_input)
    if m:
        dep_city = m.group(1)
        arr_city = m.group(2)
        dep_terminal = CITY_TO_TERMINAL.get(dep_city, dep_city)
        arr_terminal = CITY_TO_TERMINAL.get(arr_city, arr_city)
        return "고속버스", dep_terminal, arr_terminal
    # 기존 로직 유지
    bus_patterns = [
        r"(고속버스)", r"(시외버스)", r"(\d+번 고속버스)"
    ]
    bus_line = None
    for pattern in bus_patterns:
        match = re.search(pattern, user_input)
        if match:
            bus_line = match.group(1)
            break
    # 터미널 패턴 매칭
    station = None
    if bus_line:
        bus_index = user_input.find(bus_line)
        remaining_text = user_input[bus_index + len(bus_line):]
        station_patterns = [
            r"(\w+고속터미널)", r"(\w+종합터미널)", r"(\w+터미널)", r"(\w+역)"
        ]
        for pattern in station_patterns:
            match = re.search(pattern, remaining_text)
            if match:
                station = match.group(1)
                break
        # 터미널명이 없고 도시명이 있으면 대표 터미널로 변환
        if not station:
            for city, terminal in CITY_TO_TERMINAL.items():
                if city in remaining_text:
                    station = terminal
                    break
    # 목적지 추출
    destination = None
    if "에서" in user_input and "까지" in user_input:
        parts = user_input.split("에서")
        if len(parts) > 1:
            destination_part = parts[1].split("까지")[0]
            for pattern in [r"(\w+고속터미널)", r"(\w+종합터미널)", r"(\w+터미널)", r"(\w+역)"]:
                match = re.search(pattern, destination_part)
                if match:
                    destination = match.group(1)
                    break
            # 목적지 터미널명이 없고 도시명이 있으면 대표 터미널로 변환
            if not destination:
                for city, terminal in CITY_TO_TERMINAL.items():
                    if city in destination_part:
                        destination = terminal
                        break
    # '고속버스' 키워드 없이 터미널명만 있는 경우
    m = re.search(r"([가-힣]+고속터미널|[가-힣]+터미널)", user_input)
    if m:
        station = m.group(1)
        station = CITY_TO_TERMINAL.get(station, station)
        return None, station, None
    return bus_line, station, destination

def get_bus_info(bus_line, station, destination=None):
    api_key = BUS_API_KEY
    # 입력값 정규화: 터미널명/도시명에 부분 일치하는 키가 있으면 코드로 변환
    def normalize_terminal_name(name):
        for key in TERMINAL_CODE_MAP:
            if key in name:
                return TERMINAL_CODE_MAP[key]
        return TERMINAL_CODE_MAP.get(name, name)
    dep_terminal = normalize_terminal_name(station or "")
    arr_terminal = normalize_terminal_name(destination or "")
    dep_date = datetime.now().strftime("%Y%m%d")
    # busGradeId=2 (우등)로 고정
    bus_grade_id = 2
    url = (
        "http://apis.data.go.kr/1613000/ExpBusInfoService/getExpBusTrminlSchdulList"
        f"?serviceKey={api_key}"
        f"&depTerminalId={dep_terminal}"
        f"&arrTerminalId={arr_terminal}"
        f"&depPlandTime={dep_date}"
        f"&busGradeId={bus_grade_id}"
        f"&numOfRows=5"
        f"&_type=json"
    )
    print(f"[고속버스 API 호출 URL] {url}")
    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        response = session.get(url, verify=False)
        if response.status_code == 200:
            data = response.json()
            items = data.get("response", {}).get("body", {}).get("items", {})
            # 실제 API는 items['item'] 구조이므로, dict이고 'item' 키가 있으면 리스트로 변환
            if isinstance(items, dict) and "item" in items:
                items = items["item"]
            if not items or items == "":
                return "해당 구간의 실시간 고속버스 시간표를 찾을 수 없습니다."
            if isinstance(items, dict):
                items = [items]
            # 현재 시간 이후의 버스만 필터링 (30분 여유 포함)
            now = datetime.now()
            # 30분 전 시간 계산
            thirty_min_ago = now - timedelta(minutes=30)
            now_str = now.strftime("%Y%m%d%H%M")
            thirty_min_ago_str = thirty_min_ago.strftime("%Y%m%d%H%M")
            print(f"[DEBUG] 현재 시간: {now_str}, 30분 전: {thirty_min_ago_str}")
            filtered_items = []
            for item in items:
                dep_time = str(item.get("depPlandTime", ""))
                # API 응답 시간 형식: YYYYMMDDHHMM (12자리)
                if len(dep_time) == 12:
                    # 30분 전 이후의 버스만 포함 (이미 출발한 버스 제외)
                    if dep_time >= thirty_min_ago_str:
                        filtered_items.append(item)
                else:
                    # 시간 형식이 맞지 않으면 일단 포함
                    filtered_items.append(item)
            print(f"[DEBUG] 필터링 후 버스 수: {len(filtered_items)}")
            filtered_items = filtered_items[:20]  # 최대 20건만 출력
            lines = ["출발시간   | 금액    | 출발지       | 도착지       | 등급"]
            lines.append("-"*44)
            for item in filtered_items:
                dep_time = str(item.get("depPlandTime", ""))
                arr_time = str(item.get("arrPlandTime", ""))
                charge = str(item.get("charge", "정보없음"))
                dep_place = item.get("depPlaceNm", "")
                arr_place = item.get("arrPlaceNm", "")
                bus_grade = item.get("gradeNm", "등급정보없음")
                # 시간 포맷팅
                dep_fmt = f"{dep_time[8:10]}:{dep_time[10:12]}" if len(dep_time) >= 12 else dep_time
                arr_fmt = f"{arr_time[8:10]}:{arr_time[10:12]}" if len(arr_time) >= 12 else arr_time
                lines.append(f"{dep_fmt: <7} | {charge: <7} | {dep_place: <10} | {arr_place: <10} | {bus_grade}")
            if len(filtered_items) == 0:
                lines.append("(현재 이후 출발/도착 버스가 없습니다)")
            return {
                "response": (
                    f"🚌 {station} → {destination} 실시간 시간표\n" +
                    "\n".join(lines) +
                    "\n\n※ 실제 예매/좌석 현황은 고속버스 예매 사이트에서 확인하세요."
                )
            }
        else:
            return f"고속버스 RESTful API 오류: {response.status_code}"
    except Exception as e:
        return f"고속버스 RESTful API 호출 오류: {e}"

def get_bus_route_info(start_station, end_station, bus_line):
    raise NotImplementedError("get_bus_route_info는 아직 구현되지 않았습니다.")

def extract_subway_info(user_input):
    """
    사용자 입력에서 지하철 정보 추출
    """
    # 노선 패턴 매칭
    line_patterns = [
        r"(\d+호선)", r"(분당선)", r"(신분당선)", r"(경의중앙선)", r"(공항철도)"
    ]
    line = None
    for pattern in line_patterns:
        match = re.search(pattern, user_input)
        if match:
            line = match.group(1)
            break
    # 역명 추출: 노선명 있으면 기존 방식, 없으면 전체에서 '역' 또는 '터미널' 패턴 추출
    station = None
    if line:
        line_index = user_input.find(line)
        remaining_text = user_input[line_index + len(line):]
        station_patterns = [
            r"([가-힣0-9]+역)", r"([가-힣0-9]+터미널)"
        ]
        for pattern in station_patterns:
            match = re.search(pattern, remaining_text)
            if match:
                station = match.group(1)
                break
    else:
        # 노선명 없이도 '역' 또는 '터미널'이 있으면 추출
        match = re.search(r"([가-힣0-9]+역|[가-힣0-9]+터미널)", user_input)
        if match:
            station = match.group(1)
    # 목적지 추출
    destination = None
    if "에서" in user_input and "까지" in user_input:
        parts = user_input.split("에서")
        if len(parts) > 1:
            destination_part = parts[1].split("까지")[0]
            for pattern in [r"(\w+역)", r"(\w+정)"]:
                match = re.search(pattern, destination_part)
                if match:
                    destination = match.group(1)
                    break
    return line, station, destination

def get_subway_info(line, station, destination=None):
    print(f"=== THIS IS THE REAL get_subway_info ===, __file__={os.path.abspath(__file__)}")
    api_key = SUBWAY_API_KEY
    station_code = SUBWAY_STATION_CODE_MAP.get(station, station)
    url = (
        f"https://apis.data.go.kr/1613000/subwayRealtimeArrival/getSubwayRealtimeArrivalList"
        f"?serviceKey={api_key}"
        f"&stationName={station}"
        f"&_type=json"
    )
    print(f"[지하철 API 호출 URL] {url}")  # 실제 호출되는 URL을 출력
    return url  # 실제 API 호출 대신 URL만 반환

def get_station_info(station_name):
    raise NotImplementedError("get_station_info는 아직 구현되지 않았습니다.")

def get_line_info(line_name):
    raise NotImplementedError("get_line_info는 아직 구현되지 않았습니다.")

def get_route_info(start_station, end_station, current_line):
    raise NotImplementedError("get_route_info는 아직 구현되지 않았습니다.")

def get_congestion_info(line, station, direction="상행"):
    raise NotImplementedError("get_congestion_info는 아직 구현되지 않았습니다.")

def get_delay_info(line):
    raise NotImplementedError("get_delay_info는 아직 구현되지 않았습니다.")

def get_train_station_list_by_city(city_code, num_of_rows=10, page_no=1, data_type="json"):
    api_key = KYX_API_KEY
    url = (
        "https://apis.data.go.kr/1613000/TrainInfoService/getCtyAcctoTrainSttnList"
        f"?serviceKey={api_key}"
        f"&cityCode={city_code}"
        f"&numOfRows={num_of_rows}"
        f"&pageNo={page_no}"
        f"&_type={data_type}"
    )
    print(f"[KTX 시/도별 기차역 목록 API 호출 URL] {url}")
    return url

def get_train_vehicle_kind_list(data_type="json"):
    api_key = KYX_API_KEY
    url = (
        "https://apis.data.go.kr/1613000/TrainInfoService/getVhcleKndList"
        f"?serviceKey={api_key}"
        f"&_type={data_type}"
    )
    print(f"[KTX 차량종류 목록 API 호출 URL] {url}")
    return url

def get_train_city_code_list(data_type="json"):
    api_key = KYX_API_KEY
    url = (
        "https://apis.data.go.kr/1613000/TrainInfoService/getCtyCodeList"
        f"?serviceKey={api_key}"
        f"&_type={data_type}"
    )
    print(f"[KTX 도시코드 목록 API 호출 URL] {url}")
    return url

def get_flight_info(dep_airport, arr_airport, date=None):
    api_key = KYX_API_KEY  # 실제 항공 API 키로 교체 필요
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    dep_code = AIRPORT_CODE_MAP.get(dep_airport, dep_airport)
    arr_code = AIRPORT_CODE_MAP.get(arr_airport, arr_airport)
    # 1. 여객편 실시간 정보 (공공데이터포털 항공운항정보 API 예시)
    flight_url = (
        f"https://apis.data.go.kr/1613000/DmstcFlightNvgInfoService/getFlightOpratInfoList"
        f"?serviceKey={api_key}"
        f"&depAirportId={dep_code}"
        f"&arrAirportId={arr_code}"
        f"&depPlandTime={date}"
        f"&numOfRows=5"
        f"&_type=json"
    )
    # 2. 출발/도착 공항 기상 정보 (공공데이터포털 공항기상 API 예시)
    weather_url = (
        f"https://apis.data.go.kr/1360000/AirportWeatherInfoService/getAirportWeatherInfo"
        f"?serviceKey={api_key}"
        f"&airport={dep_code},{arr_code}"
        f"&_type=json"
    )
    print(f"[항공편 API 호출 URL] {flight_url}")
    print(f"[공항기상 API 호출 URL] {weather_url}")
    try:
        flight_resp = requests.get(flight_url)
        weather_resp = requests.get(weather_url)
        dep_weather, arr_weather = "", ""
        if weather_resp.status_code == 200:
            wdata = weather_resp.json()
            items = wdata.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            for item in items:
                if item.get("airport", "") == dep_code:
                    dep_weather = item.get("weather", "")
                if item.get("airport", "") == arr_code:
                    arr_weather = item.get("weather", "")
        if flight_resp.status_code == 200:
            fdata = flight_resp.json()
            flights = fdata.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if not flights:
                return "해당 구간의 실시간 항공편 정보를 찾을 수 없습니다."
            lines = []
            for i, item in enumerate(flights):
                dep_time = item.get("depPlandTime", "")[8:12]
                arr_time = item.get("arrPlandTime", "")[8:12]
                airline = item.get("airlineKorean", "항공사없음")
                flight_no = item.get("vihicleId", "편명없음")
                lines.append(
                    f"{i+1}. {airline} {flight_no} | {dep_time[:2]}:{dep_time[2:]} 출발 → {arr_time[:2]}:{arr_time[2:]} 도착"
                )
            return (
                f"✈️ {dep_airport} → {arr_airport} 실시간 항공편 정보\n" +
                "\n".join(lines) +
                f"\n\n출발지({dep_airport}) 기상: {dep_weather}\n도착지({arr_airport}) 기상: {arr_weather}"
            )
        else:
            return "항공편 실시간 정보를 불러올 수 없습니다."
    except Exception as e:
        return f"항공편/기상 API 호출 오류: {e}"

def get_terminal_code_from_name(terminal_name):
    """
    터미널명 또는 도시명으로 고속버스 터미널 코드를 조회하는 함수 (REST API 활용)
    도시명만 입력된 경우 대표 터미널명으로 변환 후 코드 조회
    """
    # 도시명만 입력된 경우 대표 터미널명으로 변환
    if terminal_name in CITY_TO_TERMINAL:
        terminal_name = CITY_TO_TERMINAL[terminal_name]
    api_key = BUS_API_KEY
    url = "http://apis.data.go.kr/1613000/ExpBusInfoService/getExpBusTrminlList"
    params = {
        "serviceKey": quote(api_key, safe=''),
        "terminalNm": terminal_name,
        "numOfRows": 10,
        "pageNo": 1,
        "_type": "json"
    }
    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        response = session.get(url, params=params)
        data = response.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if items is None:
            return None
        if isinstance(items, dict):
            items = [items]
        if not isinstance(items, list) or not items:
            return None
        first_item = items[0] if len(items) > 0 else None
        if isinstance(first_item, dict) and "terminalId" in first_item:
            terminal_id = first_item["terminalId"]
            if terminal_id is not None:
                return terminal_id
        return None
    except Exception as e:
        return None

def clean_station_name(name):
    # 역 이름에서 '까지', '에서', '부터', '으로', '로', 공백 등 불필요한 접미사만 제거
    return re.sub(r"(까지|에서|부터|으로|로|\s)+$", "", name.strip())

def transport_chat_handler(message, session):
    """
    교통 관련 챗봇 분기 및 응답을 transport.py에서 직접 처리
    """
    transport_keywords = ["고속버스", "시외버스", "버스", "지하철", "전철", "터미널", "정류장", "KTX", "기차", "열차", "항공", "비행기", "공항"]
    # 지하철 노선명+역명+시간표 패턴도 분기
    subway_pattern = re.compile(r"(\d+호선|[가-힣]+선)\s*([가-힣0-9]+역).*(시간표|첫차|막차|도착|출발)")
    if any(keyword in message for keyword in transport_keywords) or subway_pattern.search(message):
        session["user_state"] = {}  # 교통 질문 시 상태 항상 초기화
        # 1. 지하철 분기 (REST 기반 역 목록/시간표 안내)
        if "지하철" in message or "전철" in message or subway_pattern.search(message):
            line, station, destination = extract_subway_info(message)
            if not station:
                return {
                    "response": (
                        "지하철 정보를 안내해드리려면 아래 정보를 입력해 주세요! 🚇\n\n"
                        "필요 정보:\n"
                        "• 노선명(예: 2호선, 분당선 등)\n"
                        "• 역명(예: 강남역, 서울역 등)\n"
                        "• (선택) 목적지 역명\n\n"
                        "예시 질문:\n"
                        "• '지하철 2호선 강남역 시간표 알려줘'\n"
                        "• '분당선 서울역 시간표 알려줘'"
                    )
                }
            result = get_subway_station_list(station)
            return {"response": result}
        # 2. 열차/기차 분기 (KTX → 열차로 명칭 통일)
        if "KTX" in message or "기차" in message or "열차" in message:
            parts = re.split(r"에서|->|→|부터|~|\s", message)
            departure = None
            arrival = None
            for i, part in enumerate(parts):
                if "KTX" in part or "기차" in part or "열차" in part:
                    if i+1 < len(parts):
                        departure = clean_station_name(parts[i+1])
                    if i+3 < len(parts):
                        arrival = clean_station_name(parts[i+3])
            if departure and arrival:
                print(f"[DEBUG] 출발지: {departure}, 도착지: {arrival}")
                prefix = f"출발지는 {departure}, 도착지는 {arrival} 입니다.\n"
            else:
                prefix = ""
            if not departure or not arrival:
                return {
                    "response": (
                        "열차 정보를 안내해드리려면 아래 정보를 입력해 주세요! 🚄\n\n"
                        "예시 질문:\n"
                        "• '열차 서울역에서 부산역까지 시간표 알려줘'\n"
                        "• '기차 대전역에서 동대구역까지 요금 알려줘'"
                    )
                }
            else:
                return {"response": prefix + get_ktx_info(departure, arrival)}
        # 3. 항공/비행기/공항 분기
        if "항공" in message or "비행기" in message or "공항" in message:
            parts = re.split(r"에서|->|→|부터|~|\s", message)
            dep_airport = None
            arr_airport = None
            for i, part in enumerate(parts):
                if "항공" in part or "비행기" in part or "공항" in part:
                    if i+1 < len(parts):
                        dep_airport = parts[i+1].strip()
                    if i+3 < len(parts):
                        arr_airport = parts[i+3].strip()
            if dep_airport and arr_airport:
                print(f"[DEBUG] 출발지: {dep_airport}, 도착지: {arr_airport}")
                prefix = f"출발지는 {dep_airport}, 도착지는 {arr_airport} 입니다.\n"
            else:
                prefix = ""
            if not dep_airport or not arr_airport:
                return {
                    "response": (
                        "항공편 정보를 안내해드리려면 아래 정보를 입력해 주세요! ✈️\n\n"
                        "필요 정보:\n"
                        "• 출발 공항명\n"
                        "• 도착 공항명\n"
                        "• (선택) 날짜\n\n"
                        "예시 질문:\n"
                        "• '항공 인천국제공항에서 김포국제공항까지 시간표 알려줘'\n"
                        "• '비행기 제주국제공항에서 김해국제공항까지 요금 알려줘'"
                    )
                }
            else:
                return {"response": prefix + get_flight_info(dep_airport, arr_airport)}
        # 4. 고속버스/버스 분기(기존 로직)
        bus_line, station, destination = extract_bus_info(message)
        print(f"[DEBUG] bus_line: {bus_line}, station: {station}, destination: {destination}")
        if station and destination:
            print(f"[DEBUG] 출발지: {station}, 도착지: {destination}")
            prefix = f"출발지는 {station}, 도착지는 {destination} 입니다.\n"
        dep_date = extract_date_from_message(message)
        if dep_date is None:
            dep_date = datetime.now().strftime("%Y%m%d")
        if dep_date < datetime.now().strftime("%Y%m%d"):
            return {"response": f"{prefix}과거의 날짜({dep_date})는 조회할 수 없습니다. 오늘 또는 미래 날짜를 입력해 주세요."}
            dep_terminal = TERMINAL_CODE_MAP.get(station or "", station or "")
            arr_terminal = TERMINAL_CODE_MAP.get(destination or "", destination or "")
            if not dep_terminal or len(dep_terminal) < 6:
                dep_terminal = get_terminal_code_from_name(station or "")
            if not arr_terminal or len(arr_terminal) < 6:
                arr_terminal = get_terminal_code_from_name(destination or "")
            if not dep_terminal or not arr_terminal:
                return {"response": f"{prefix}출발지 또는 도착지 터미널 코드를 찾을 수 없습니다.\n입력값: 출발={station}, 도착={destination}"}
            try:
                raw = get_expbusinfo_rest(
                    dep_terminal_id=dep_terminal,
                    arr_terminal_id=arr_terminal,
                    dep_pland_time=dep_date,
                    data_type="json"
                )
                data = json.loads(raw)
                items = data.get("response", {}).get("body", {}).get("items", {})
                # 실제 API는 items['item'] 구조이므로, dict이고 'item' 키가 있으면 리스트로 변환
                if isinstance(items, dict) and "item" in items:
                    items = items["item"]
                if not items or items == "":
                    return {"response": f"{prefix}해당 조건에 맞는 고속버스 운행 정보가 없습니다.\n(출발: {station}, 도착: {destination}, 날짜: {dep_date})"}
                if isinstance(items, dict):
                    items = [items]
                # 표 헤더 추가
                # 현재 시간 이후의 버스만 필터링 (30분 여유 포함)
                now = datetime.now()
                # 30분 전 시간 계산
                thirty_min_ago = now - timedelta(minutes=30)
                now_str = now.strftime("%Y%m%d%H%M")
                thirty_min_ago_str = thirty_min_ago.strftime("%Y%m%d%H%M")
                print(f"[DEBUG] 현재 시간: {now_str}, 30분 전: {thirty_min_ago_str}")
                filtered_items = []
                for item in items:
                    dep_time = str(item.get("depPlandTime", ""))
                    # API 응답 시간 형식: YYYYMMDDHHMM (12자리)
                    if len(dep_time) == 12:
                        # 30분 전 이후의 버스만 포함 (이미 출발한 버스 제외)
                        if dep_time >= thirty_min_ago_str:
                            filtered_items.append(item)
                    else:
                        # 시간 형식이 맞지 않으면 일단 포함
                        filtered_items.append(item)
                print(f"[DEBUG] 필터링 후 버스 수: {len(filtered_items)}")
                filtered_items = filtered_items[:20]  # 최대 20건만 출력
                lines = ["출발시간   | 금액    | 출발지       | 도착지       | 등급"]
                lines.append("-"*44)
                for item in filtered_items:
                    dep_time = str(item.get("depPlandTime", ""))
                    arr_time = str(item.get("arrPlandTime", ""))
                    charge = str(item.get("charge", "정보없음"))
                    dep_place = item.get("depPlaceNm", "")
                    arr_place = item.get("arrPlaceNm", "")
                    bus_grade = item.get("gradeNm", "등급정보없음")
                    # 시간 포맷팅
                    dep_fmt = f"{dep_time[8:10]}:{dep_time[10:12]}" if len(dep_time) >= 12 else dep_time
                    arr_fmt = f"{arr_time[8:10]}:{arr_time[10:12]}" if len(arr_time) >= 12 else arr_time
                    lines.append(f"{dep_fmt: <7} | {charge: <7} | {dep_place: <10} | {arr_place: <10} | {bus_grade}")
                if len(filtered_items) == 0:
                    lines.append("(현재 이후 출발/도착 버스가 없습니다)")
                return {
                    "response": (
                        f"{prefix}🚌 {station} → {destination} 실시간 시간표\n" +
                        "\n".join(lines) +
                        "\n\n※ 실제 예매/좌석 현황은 고속버스 예매 사이트에서 확인하세요."
                    )
                }
            except Exception as e:
                return {"response": f"{prefix}고속버스 REST API 파싱 오류: {e}\n원본 응답: {raw}"}
        elif station and not destination:
            print(f"[DEBUG] 출발지(only): {station}")
            dep_date = extract_date_from_message(message)
            if dep_date is None:
                dep_date = datetime.now().strftime("%Y%m%d")
            dep_terminal = TERMINAL_CODE_MAP.get(station or "", station or "")
            if not dep_terminal or len(dep_terminal) < 6:
                dep_terminal = get_terminal_code_from_name(station or "")
            if not dep_terminal:
                return {"response": f"출발지 터미널 코드를 찾을 수 없습니다.\n입력값: 출발={station}"}
            try:
                raw = get_expbusinfo_rest(
                    dep_terminal_id=dep_terminal,
                    arr_terminal_id="",
                    dep_pland_time=dep_date,
                    data_type="json"
                )
                data = json.loads(raw)
                items = data.get("response", {}).get("body", {}).get("items", {})
                if isinstance(items, dict) and "item" in items:
                    items = items["item"]
                if not items or items == "":
                    return {"response": f"{station} 출발의 실시간 고속버스 시간표가 없습니다. (날짜: {dep_date})"}
                if isinstance(items, dict):
                    items = [items]
                # 현재 시간 이후의 버스만 필터링 (30분 여유 포함)
                now = datetime.now()
                # 30분 전 시간 계산
                thirty_min_ago = now - timedelta(minutes=30)
                now_str = now.strftime("%Y%m%d%H%M")
                thirty_min_ago_str = thirty_min_ago.strftime("%Y%m%d%H%M")
                print(f"[DEBUG] 현재 시간: {now_str}, 30분 전: {thirty_min_ago_str}")
                filtered_items = []
                for item in items:
                    dep_time = str(item.get("depPlandTime", ""))
                    # API 응답 시간 형식: YYYYMMDDHHMM (12자리)
                    if len(dep_time) == 12:
                        # 30분 전 이후의 버스만 포함 (이미 출발한 버스 제외)
                        if dep_time >= thirty_min_ago_str:
                            filtered_items.append(item)
                    else:
                        # 시간 형식이 맞지 않으면 일단 포함
                        filtered_items.append(item)
                print(f"[DEBUG] 필터링 후 버스 수: {len(filtered_items)}")
                filtered_items = filtered_items[:20]  # 최대 20건만 출력
                lines = ["출발시간   | 금액    | 출발지       | 도착지       | 등급"]
                lines.append("-"*44)
                for item in filtered_items:
                    dep_time = str(item.get("depPlandTime", ""))
                    arr_time = str(item.get("arrPlandTime", ""))
                    charge = str(item.get("charge", "정보없음"))
                    dep_place = item.get("depPlaceNm", "")
                    arr_place = item.get("arrPlaceNm", "")
                    bus_grade = item.get("gradeNm", "등급정보없음")
                    dep_fmt = f"{dep_time[8:10]}:{dep_time[10:12]}" if len(dep_time) >= 12 else dep_time
                    arr_fmt = f"{arr_time[8:10]}:{arr_time[10:12]}" if len(arr_time) >= 12 else arr_time
                    lines.append(f"{dep_fmt: <7} | {charge: <7} | {dep_place: <10} | {arr_place: <10} | {bus_grade}")
                if len(filtered_items) == 0:
                    lines.append("(현재 이후 출발/도착 버스가 없습니다)")
                result = {
                    "response": (
                        f"🚌 {station} 출발 전체 실시간 시간표\n" +
                        "\n".join(lines) +
                        "\n\n※ 실제 예매/좌석 현황은 고속버스 예매 사이트에서 확인하세요."
                    )
                }
            except Exception as e:
                return {"response": f"{station} 출발 고속버스 REST API 파싱 오류: {e}\n원본 응답: {raw}"}
            return result
        elif not bus_line and not station:
            return {
                "response": (
                    "예시 질문:\n"
                    "• '고속버스 서울고속터미널에서 부산종합터미널까지 경로 알려줘'\n"
                    "• '서울고속터미널 시간표 알려줘'\n"
                    "• '부산에서 대구까지 고속버스 요금 알려줘'"
                )
            }
        return {
            "response": (
                f"고속버스 정보를 안내해드리려면 출발지, 도착지, 터미널명 등 구체적인 정보를 입력해 주세요! 🚌\n"
                "예시: '고속버스 서울고속터미널에서 부산종합터미널까지 경로 알려줘'"
            )
        }
    return None

# === 고속버스 REST API 연동 함수 추가 ===
def get_expbusinfo_rest(dep_terminal_id, arr_terminal_id, dep_pland_time, bus_grade_id=None, num_of_rows=300, page_no=1, data_type="json"):
    """
    출/도착지 기반 고속버스정보 조회 (REST)
    """
    api_key = BUS_API_KEY
    # 터미널 코드로 변환(이중 체크)
    def normalize_terminal_name(name):
        for key in TERMINAL_CODE_MAP:
            if key in name:
                return TERMINAL_CODE_MAP[key]
        return TERMINAL_CODE_MAP.get(name, name)
    dep_terminal_id = normalize_terminal_name(dep_terminal_id)
    arr_terminal_id = normalize_terminal_name(arr_terminal_id)
    url = (
        "http://apis.data.go.kr/1613000/ExpBusInfoService/getStrtpntAlocFndExpbusInfo"
        f"?serviceKey={api_key}"
        f"&pageNo={page_no}"
        f"&numOfRows={num_of_rows}"
        f"&_type=json"
        f"&depTerminalId={dep_terminal_id}"
        f"&arrTerminalId={arr_terminal_id}"
        f"&depPlandTime={dep_pland_time}"
    )
    if bus_grade_id:
        url += f"&busGradeId={bus_grade_id}"
    print(f"[고속버스 출도착지 기반 정보 API 호출 URL] {url}")
    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        response = session.get(url, verify=False)
        return response.text
    except Exception as e:
        return f"고속버스 RESTful API 호출 오류: {e}"

def get_expbus_terminal_list(terminal_nm=None, num_of_rows=10, page_no=1, data_type="json"):
    api_key = BUS_API_KEY
    url = (
        "http://apis.data.go.kr/1613000/ExpBusInfoService/getExpBusTrminlList"
        f"?serviceKey={api_key}"
        f"&numOfRows={num_of_rows}"
        f"&pageNo={page_no}"
        f"&_type=json"
    )
    if terminal_nm:
        url += f"&terminalNm={terminal_nm}"
    print(f"[고속버스 터미널 목록 API 호출 URL] {url}")
    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        response = session.get(url, verify=False)
        return response.text
    except Exception as e:
        return f"고속버스 터미널 목록 API 호출 오류: {e}"

def get_expbus_grade_list(data_type="json"):
    api_key = BUS_API_KEY
    url = (
        "http://apis.data.go.kr/1613000/ExpBusInfoService/getExpBusGradList"
        f"?serviceKey={api_key}"
        f"&_type=json"
    )
    print(f"[고속버스 등급 목록 API 호출 URL] {url}")
    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        response = session.get(url, verify=False)
        return response.text
    except Exception as e:
        return f"고속버스 등급 목록 API 호출 오류: {e}"

def get_expbus_city_code_list(data_type="json"):
    api_key = BUS_API_KEY
    url = (
        "http://apis.data.go.kr/1613000/ExpBusInfoService/getCtyCodeList"
        f"?serviceKey={api_key}"
        f"&_type=json"
    )
    print(f"[고속버스 도시코드 목록 API 호출 URL] {url}")
    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        response = session.get(url, verify=False)
        return response.text
    except Exception as e:
        return f"고속버스 도시코드 목록 API 호출 오류: {e}"

# === 지하철정보 서비스 REST API 연동 함수 추가 ===
def get_subway_station_list(keyword, num_of_rows=10, page_no=1, data_type="xml"):
    api_key = SUBWAY_API_KEY
    encoded_keyword = quote(keyword)
    url = (
        "https://apis.data.go.kr/1613000/SubwayInfoService/getKwrdFndSubwaySttnList"
        f"?serviceKey={api_key}"
        f"&pageNo={page_no}"
        f"&numOfRows={num_of_rows}"
        f"&_type=xml"
        f"&subwayStationName={encoded_keyword}"
    )
    print(f"[지하철 역 조회 API 호출 URL] {url}")
    try:
        session = requests.Session()
        session.mount('https://', TLSAdapter())
        response = session.get(url, verify=False)
        return response.text  # XML 그대로 반환 (또는 필요시 파싱)
    except Exception as e:
        return f"지하철 역 목록 API 호출 오류: {e}"

def get_subway_exit_bus_routes(station_id, num_of_rows=10, page_no=1, data_type="json"):
    api_key = SUBWAY_API_KEY
    url = (
        "https://apis.data.go.kr/1613000/SubwayInfoService/getSubwaySttnExitAcctoBusRouteList"
        f"?serviceKey={api_key}"
        f"&subwayStationId={station_id}"
        f"&numOfRows={num_of_rows}"
        f"&pageNo={page_no}"
        f"&_type={data_type}"
    )
    print(f"[지하철 역 출구별 버스노선 API 호출 URL] {url}")
    return url

def get_subway_exit_facilities(station_id, num_of_rows=10, page_no=1, data_type="json"):
    api_key = SUBWAY_API_KEY
    url = (
        "https://apis.data.go.kr/1613000/SubwayInfoService/getSubwaySttnExitAcctoCfrFcltyList"
        f"?serviceKey={api_key}"
        f"&subwayStationId={station_id}"
        f"&numOfRows={num_of_rows}"
        f"&pageNo={page_no}"
        f"&_type={data_type}"
    )
    print(f"[지하철 역 출구별 주변 시설 API 호출 URL] {url}")
    return url

def get_subway_station_schedule(station_id, daily_type_code="01", up_down_type_code="D", num_of_rows=10, page_no=1, data_type="json"):
    api_key = SUBWAY_API_KEY
    url = (
        "https://apis.data.go.kr/1613000/SubwayInfoService/getSubwaySttnAcctoSchdulList"
        f"?serviceKey={api_key}"
        f"&subwayStationId={station_id}"
        f"&dailyTypeCode={daily_type_code}"
        f"&upDownTypeCode={up_down_type_code}"
        f"&numOfRows={num_of_rows}"
        f"&pageNo={page_no}"
        f"&_type={data_type}"
    )
    print(f"[지하철 역별 시간표 API 호출 URL] {url}")
    return url

def print_env_keys():
    """
    .env에서 주요 API 키를 불러와 마스킹하여 출력하는 유틸리티 함수
    """
    load_dotenv()
    bus_key = os.getenv("BUS_API_KEY")
    subway_key = os.getenv("SUBWAY_API_KEY")
    ktx_key = os.getenv("KYX_API_KEY")
    def mask(key):
        if not key:
            return "(없음)"
        if len(key) <= 8:
            return key[:2] + "***" + key[-2:]
        return key[:4] + "***" + key[-4:]
    print(f"BUS_API_KEY: {mask(bus_key)}")
    print(f"SUBWAY_API_KEY: {mask(subway_key)}")
    print(f"KYX_API_KEY: {mask(ktx_key)}") 