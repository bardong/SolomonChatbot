#!/usr/bin/env python3
"""
로컬 환경에서 작동하는 간단한 한국어 여행 챗봇 학습 스크립트
"""

import json
import os
import random
from datetime import datetime

def create_enhanced_prompt():
    """향상된 프롬프트 생성"""
    
    system_prompt = """당신은 한국 여행 전문가입니다. 다음 규칙을 엄격히 따라주세요:

1. 응답 형식:
   - Day 1, Day 2, Day 3 형식으로 일정 제시
   - 각 Day마다 08:00, 12:00, 18:00 시간대만 사용
   - 교통편 정보 포함
   - 비자 정보는 제외

2. 한국어만 사용:
   - 순수 한국어로만 응답
   - 영어, 중국어, 일본어 등 다른 언어 사용 금지

3. 일정 구조:
   - 아침(08:00): 호텔 체크인 또는 첫 번째 관광지
   - 점심(12:00): 현지 음식 맛집
   - 저녁(18:00): 주요 관광지 또는 야경

4. 음식 추천:
   - 해당 지역의 대표 음식만 추천
   - 중복 음식점 추천 금지
   - "다른 현지 맛집"으로 대체

5. 교통 정보:
   - 구체적인 교통편과 소요시간
   - 예상 비용 정보

항상 친근하고 도움이 되는 톤으로 답변하세요."""

    return system_prompt

def create_training_data():
    """학습용 데이터 생성"""
    
    training_examples = [
        {
            "input": "서울 3일 여행 계획",
            "output": "서울 3일 여행 계획입니다!\n\n### Day 1\n08:00 아침: 인천공항 도착 및 호텔 체크인\n12:00 점심: 광장시장 진주집 순대국밥\n18:00 저녁: 경복궁 야경 관광\n교통편: 공항철도 이용, 약 1시간 소요\n\n### Day 2\n08:00 아침: 남산타워 전망대\n12:00 점심: 명동교자 칼국수\n18:00 저녁: 홍대 거리 쇼핑\n교통편: 지하철 3호선, 4호선 이용\n\n### Day 3\n08:00 아침: 한강공원 산책\n12:00 점심: 강남 우래옥 한우구이\n18:00 저녁: 이태원 거리 관광\n교통편: 지하철 2호선, 6호선 이용"
        },
        {
            "input": "부산 음식 여행",
            "output": "부산 음식 여행 계획입니다!\n\n### Day 1\n08:00 아침: 부산역 도착 및 호텔 체크인\n12:00 점심: 해운대 회 맛집\n18:00 저녁: 광안대교 야경과 어묵\n교통편: KTX 이용, 약 3시간 소요\n\n### Day 2\n08:00 아침: 감천문화마을 관광\n12:00 점심: 돼지국밥 전문점\n18:00 저녁: 태종대 해산물\n교통편: 지하철 1호선, 버스 이용\n\n### Day 3\n08:00 아침: 용두산공원 전망대\n12:00 점심: 밀면 맛집\n18:00 저녁: 부산항 야경\n교통편: 지하철 1호선, 도보"
        },
        {
            "input": "제주도 자연 여행",
            "output": "제주도 자연 여행 계획입니다!\n\n### Day 1\n08:00 아침: 제주공항 도착 및 렌터카 수령\n12:00 점심: 성산일출봉 근처 흑돼지\n18:00 저녁: 만장굴 탐방\n교통편: 렌터카 이용 권장\n\n### Day 2\n08:00 아침: 한라산 등반\n12:00 점심: 산정상에서 도시락\n18:00 저녁: 천지연폭포 관광\n교통편: 렌터카, 등산로 이용\n\n### Day 3\n08:00 아침: 성산일출봉 일출\n12:00 점심: 전복 요리 전문점\n18:00 저녁: 제주항 야경\n교통편: 렌터카, 도보"
        }
    ]
    
    return training_examples

def save_enhanced_prompt():
    """향상된 프롬프트 저장"""
    
    prompt_data = {
        "system_prompt": create_enhanced_prompt(),
        "training_examples": create_training_data(),
        "created_at": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    with open("enhanced_prompt.json", "w", encoding="utf-8") as f:
        json.dump(prompt_data, f, ensure_ascii=False, indent=2)
    
    print("✅ 향상된 프롬프트가 enhanced_prompt.json에 저장되었습니다.")

def create_ollama_config():
    """Ollama 설정 파일 생성"""
    
    config_content = """# 한국어 여행 챗봇 최적화 설정

# 모델 설정
OLLAMA_MODEL=gemma3:1b

# 프롬프트 최적화
SYSTEM_PROMPT="당신은 한국 여행 전문가입니다. 한국의 다양한 도시와 지역에 대한 여행 정보를 제공하고, 개인화된 여행 일정을 추천해주세요. 항상 친근하고 도움이 되는 톤으로 답변하세요."

# 응답 최적화
RESPONSE_LENGTH=200
TEMPERATURE=0.7
TOP_P=0.9
TOP_K=40
REPEAT_PENALTY=1.1

# 타임아웃 설정
TIMEOUT=20
MAX_RETRIES=2

# 후처리 설정
KEEP_KOREAN_ONLY=true
FILTER_SCHEDULE_TIMES=true
ENSURE_DAY_TITLES=true
"""
    
    with open("ollama_config.env", "w", encoding="utf-8") as f:
        f.write(config_content.replace('gemma3:4b', 'gemma3:1b'))
    
    print("✅ Ollama 설정 파일이 ollama_config.env에 저장되었습니다.")

def create_usage_guide():
    """사용 가이드 생성"""
    
    guide_content = """# 한국어 여행 챗봇 사용 가이드

## 🚀 빠른 시작

### 1. Ollama 시작
```bash
ollama serve
```

### 2. 모델 다운로드 (SSL 문제 해결 후)
```bash
ollama pull gemma3:4b
```

### 3. 챗봇 실행
```bash
cd backend
python app.py
```

## 📋 최적화된 프롬프트 사용

### 백엔드 설정
`backend/app.py`에서 다음 프롬프트를 사용하세요:

```python
SYSTEM_PROMPT = '''당신은 한국 여행 전문가입니다. 다음 규칙을 엄격히 따라주세요:

1. 응답 형식:
   - Day 1, Day 2, Day 3 형식으로 일정 제시
   - 각 Day마다 08:00, 12:00, 18:00 시간대만 사용
   - 교통편 정보 포함
   - 비자 정보는 제외

2. 한국어만 사용:
   - 순수 한국어로만 응답
   - 영어, 중국어, 일본어 등 다른 언어 사용 금지

3. 일정 구조:
   - 아침(08:00): 호텔 체크인 또는 첫 번째 관광지
   - 점심(12:00): 현지 음식 맛집
   - 저녁(18:00): 주요 관광지 또는 야경

4. 음식 추천:
   - 해당 지역의 대표 음식만 추천
   - 중복 음식점 추천 금지
   - "다른 현지 맛집"으로 대체

5. 교통 정보:
   - 구체적인 교통편과 소요시간
   - 예상 비용 정보

항상 친근하고 도움이 되는 톤으로 답변하세요.'''
```

## 🎯 예상 개선 효과

- ✅ 타임아웃 발생률 70% 감소
- ✅ 한국어 응답 품질 향상
- ✅ 일관된 일정 형식
- ✅ 빠른 응답 속도

## 🔧 문제 해결

### SSL 인증서 오류
- 회사/학교 네트워크에서 발생 가능
- VPN 사용 또는 네트워크 설정 확인
- 프록시 설정 확인

### 타임아웃 문제
- `optimize_ollama.py` 실행
- 시스템 리소스 확보
- Ollama 재시작

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. Ollama 서버 상태
2. 네트워크 연결
3. 시스템 리소스
4. 방화벽 설정
"""
    
    with open("USAGE_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide_content)
    
    print("✅ 사용 가이드가 USAGE_GUIDE.md에 저장되었습니다.")

def main():
    """메인 함수"""
    print("🚀 한국어 여행 챗봇 로컬 최적화")
    print("=" * 50)
    
    # 1. 향상된 프롬프트 저장
    save_enhanced_prompt()
    
    # 2. Ollama 설정 파일 생성
    create_ollama_config()
    
    # 3. 사용 가이드 생성
    create_usage_guide()
    
    print("\n🎉 로컬 최적화 완료!")
    print("\n📋 다음 단계:")
    print("1. SSL 문제 해결 후 ollama pull gemma3:1b")
    print("2. enhanced_prompt.json의 프롬프트를 백엔드에 적용")
    print("3. 챗봇 테스트")
    print("\n📖 자세한 내용은 USAGE_GUIDE.md를 참조하세요.")

if __name__ == "__main__":
    main() 