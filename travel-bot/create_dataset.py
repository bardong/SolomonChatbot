#!/usr/bin/env python3
"""
한국어 여행 챗봇을 위한 데이터셋 생성 스크립트
"""

import json
import random

def create_travel_dataset():
    """여행 챗봇용 데이터셋 생성"""
    
    # 기본 여행 데이터
    travel_data = []
    
    # 1. 도시별 여행 일정 데이터
    cities = {
        "서울": {
            "attractions": ["경복궁", "남산타워", "홍대", "명동", "강남", "이태원", "한강공원"],
            "foods": ["김치찌개", "불고기", "삼겹살", "치킨", "떡볶이", "순대", "갈비"],
            "transport": ["지하철", "버스", "택시", "도보"]
        },
        "부산": {
            "attractions": ["해운대", "광안대교", "감천문화마을", "태종대", "용두산공원"],
            "foods": ["회", "밀면", "돼지국밥", "닭볶음탕", "고구마", "어묵"],
            "transport": ["지하철", "버스", "택시", "도보"]
        },
        "제주도": {
            "attractions": ["성산일출봉", "만장굴", "천지연폭포", "한라산", "성산일출봉"],
            "foods": ["흑돼지", "회", "갈치", "전복", "한라봉", "감귤"],
            "transport": ["렌터카", "버스", "택시", "도보"]
        },
        "경주": {
            "attractions": ["불국사", "석굴암", "첨성대", "안압지", "경주월드"],
            "foods": ["경주빵", "황남빵", "보문호수", "한우", "닭볶음탕"],
            "transport": ["버스", "택시", "도보"]
        },
        "전주": {
            "attractions": ["한옥마을", "전주성", "경기전", "전주향교", "덕진공원"],
            "foods": ["비빔밥", "콩나물국밥", "전주한옥마을", "막걸리", "전주빵"],
            "transport": ["버스", "택시", "도보"]
        }
    }
    
    # 2. 질문-답변 쌍 생성
    for city, info in cities.items():
        # 기본 여행 정보
        travel_data.append({
            "instruction": f"{city} 여행 추천해주세요",
            "output": f"{city} 여행 추천드립니다!\n\n### Day 1\n08:00 아침: {city} 도착 및 호텔 체크인\n12:00 점심: {random.choice(info['foods'])} 맛집 방문\n18:00 저녁: {random.choice(info['attractions'])} 관광\n\n### Day 2\n08:00 아침: {random.choice(info['attractions'])} 방문\n12:00 점심: {random.choice(info['foods'])} 체험\n18:00 저녁: {random.choice(info['attractions'])} 야경 감상\n\n교통편: {random.choice(info['transport'])} 이용을 권장합니다."
        })
        
        # 음식 특화 여행
        travel_data.append({
            "instruction": f"{city} 음식 여행 계획 세워주세요",
            "output": f"{city} 음식 여행 계획입니다!\n\n### Day 1\n08:00 아침: {random.choice(info['foods'])} 아침 식사\n12:00 점심: {random.choice(info['foods'])} 전문점\n18:00 저녁: {random.choice(info['foods'])} 맛집\n\n### Day 2\n08:00 아침: {random.choice(info['foods'])} 브런치\n12:00 점심: {random.choice(info['foods'])} 현지 맛집\n18:00 저녁: {random.choice(info['foods'])} 저녁 식사\n\n{city}의 대표 음식들을 체험할 수 있는 일정입니다."
        })
        
        # 문화 관광
        travel_data.append({
            "instruction": f"{city} 문화 관광 일정 추천해주세요",
            "output": f"{city} 문화 관광 일정입니다!\n\n### Day 1\n08:00 아침: {random.choice(info['attractions'])} 방문\n12:00 점심: 근처 {random.choice(info['foods'])} 맛집\n18:00 저녁: {random.choice(info['attractions'])} 야경\n\n### Day 2\n08:00 아침: {random.choice(info['attractions'])} 관광\n12:00 점심: {random.choice(info['foods'])} 체험\n18:00 저녁: {random.choice(info['attractions'])} 문화 체험\n\n{city}의 역사와 문화를 체험할 수 있는 일정입니다."
        })
    
    # 3. 일반적인 여행 질문들
    general_questions = [
        {
            "instruction": "한국 여행 추천해주세요",
            "output": "한국 여행 추천드립니다!\n\n### 인기 여행지\n1. 서울 - 현대와 전통이 공존하는 도시\n2. 부산 - 바다와 산이 어우러진 항구도시\n3. 제주도 - 아름다운 자연과 독특한 문화\n4. 경주 - 역사의 도시, 신라 문화 체험\n5. 전주 - 전통 한옥마을과 맛집\n\n### 추천 일정\n- 서울: 3-4일 (도시 관광, 쇼핑, 음식)\n- 부산: 2-3일 (해변, 해산물, 문화)\n- 제주도: 3-4일 (자연, 드라이브, 휴양)\n\n교통편: KTX, 항공편, 고속버스 이용을 권장합니다."
        },
        {
            "instruction": "한국 음식 여행 추천해주세요",
            "output": "한국 음식 여행 추천드립니다!\n\n### 지역별 대표 음식\n- 서울: 김치찌개, 불고기, 삼겹살\n- 부산: 회, 밀면, 돼지국밥\n- 제주도: 흑돼지, 회, 갈치\n- 경주: 경주빵, 황남빵, 한우\n- 전주: 비빔밥, 콩나물국밥, 막걸리\n\n### 추천 일정\nDay 1: 서울 - 전통 한식 체험\nDay 2: 부산 - 해산물 맛집 투어\nDay 3: 제주도 - 현지 특산물 체험\n\n각 지역의 대표 음식을 체험할 수 있는 일정입니다."
        },
        {
            "instruction": "한국 3일 여행 계획 세워주세요",
            "output": "한국 3일 여행 계획입니다!\n\n### Day 1: 서울\n08:00 아침: 인천공항 도착\n12:00 점심: 김치찌개 맛집\n18:00 저녁: 경복궁 야경\n\n### Day 2: 부산\n08:00 아침: KTX로 부산 이동\n12:00 점심: 해운대 회 맛집\n18:00 저녁: 광안대교 야경\n\n### Day 3: 제주도\n08:00 아침: 항공편으로 제주 이동\n12:00 점심: 흑돼지 맛집\n18:00 저녁: 성산일출봉\n\n교통편: KTX, 항공편, 렌터카 이용을 권장합니다."
        }
    ]
    
    travel_data.extend(general_questions)
    
    # 4. 특정 관심사별 질문들
    interests = ["음식", "문화", "자연", "쇼핑", "역사"]
    for interest in interests:
        travel_data.append({
            "instruction": f"한국 {interest} 여행 추천해주세요",
            "output": f"한국 {interest} 여행 추천드립니다!\n\n### {interest} 관련 추천지\n- 서울: {interest} 관련 명소들\n- 부산: {interest} 체험 장소\n- 제주도: {interest} 관광지\n\n### 추천 일정\nDay 1: 서울 {interest} 체험\nDay 2: 부산 {interest} 관광\nDay 3: 제주도 {interest} 탐방\n\n한국의 {interest}를 깊이 체험할 수 있는 일정입니다."
        })
    
    return travel_data

def save_dataset(data, filename="train.jsonl"):
    """데이터셋을 JSONL 형식으로 저장"""
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"데이터셋이 {filename}에 저장되었습니다. (총 {len(data)}개 항목)")

def main():
    """메인 함수"""
    print("🚀 한국어 여행 챗봇 데이터셋 생성")
    print("=" * 50)
    
    # 데이터셋 생성
    dataset = create_travel_dataset()
    
    # 저장
    save_dataset(dataset)
    
    # 샘플 출력
    print("\n📝 샘플 데이터:")
    for i, item in enumerate(dataset[:3]):
        print(f"\n--- 샘플 {i+1} ---")
        print(f"질문: {item['instruction']}")
        print(f"답변: {item['output'][:100]}...")
    
    print(f"\n✅ 총 {len(dataset)}개의 질문-답변 쌍이 생성되었습니다.")
    print("이제 llama3_finetune_lora.py를 실행하여 모델을 학습시킬 수 있습니다!")

if __name__ == "__main__":
    main() 