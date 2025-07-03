# AI 여행 추천 시스템 테스트 케이스

---

## 1. 통합 시나리오 테스트 (실제 대화 예시 기반)

### [SC-01] 정상 플로우: 한국-서울-음식-3일

```
🙋 한국여행추천해줄래
🤖 한국이요? 멋진 선택입니다! 한국에는 다음과 같은 도시들이 있습니다:
- 서울
- 부산
- 제주도
- 경주
- 전주
- 여수
- 강릉
- 춘천
- 대구
- 인천
이 중에서 여행하고 싶은 도시가 있으신가요?
🙋 서울
🤖 서울를 선택하셨군요! 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)
🙋 음식
🤖 몇 박 며칠 일정으로 계획하고 계신가요? (예: 3일, 1주일 등)
🙋 3일
🤖 ## 한국 서울 3일 음식 여행 일정 (개인 맞춤 가능)

안녕하세요! 한국 서울에서 맛있는 음식 탐방을 위한 3일 여행 일정을 준비했습니다. 개인적인 취향에 맞춰 맛집을 추천해 드릴 테니, 즐거운 여행 되시길 바랍니다.
```

### [SC-02] 에러/예외 플로우: 도시/관심사/기간 오류

```
🙋 한국여행 추천해줄래?
🤖 한국이요? 멋진 선택입니다! 한국에는 다음과 같은 도시들이 있습니다:
- 서울
- 부산
- 제주도
- 경주
- 전주
- 여수
- 강릉
- 춘천
- 대구
- 인천
이 중에서 여행하고 싶은 도시가 있으신가요?
🙋 시애틀
🤖 '시애틀'는(은) 한국의 도시가 아닙니다. 위 목록에서 유효한 도시를 입력해 주세요.
🙋 다람이
🤖 '다람이'는(은) 여행지로 지원하지 않습니다. 다시 입력해 주세요.

예시: 서울, 부산, 제주도 등
🙋 부산
🤖 부산를 선택하셨군요! 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)
🙋 비바박
🤖 '비바박'는(은) 관심사가 아닙니다. 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)
🙋 음식
🤖 몇 박 며칠 일정으로 계획하고 계신가요? (예: 3일, 1주일 등)
🙋 몰라
🤖 '몰라'는(은) 올바른 기간이 아닙니다. 몇 박 며칠 일정으로 계획하고 계신가요? (예: 3일, 1주일 등)
🙋 3일
```

### [SC-03] 고속버스 정보 질의
```
🙋 고속버스 정보를 알려줘
🤖 고속버스 정보를 안내해드리려면 출발지, 도착지, 터미널명 등 구체적인 정보를 입력해 주세요! 🚌
예시: '고속버스 서울고속터미널에서 부산종합터미널까지 경로 알려줘'
🙋 고속버스 서울고속터미널에서 부산종합터미널까지 경로 알려줘
🤖 출발지는 서울고속터미널, 도착지는 부산종합터미널 입니다.
🚌 서울고속터미널 → 부산종합터미널 실시간 시간표
출발시간  | 금액  | 출발지  | 도착지  | 등급
--------------------------------------------
13:00  | 17200  | 서울경부  | 청주(고속)  | 프리미엄
13:10  | 13300  | 서울경부  | 청주(고속)  | 우등
13:20  | 9100  | 서울경부  | 청주(고속)  | 고속
...
※ 실제 예매/좌석 현황은 고속버스 예매 사이트에서 확인하세요.
```

### [SC-04] 기차 정보 질의
```
🙋 기차 정보 알려줘
🤖 열차 정보를 안내해드리려면 아래 정보를 입력해 주세요! 🚄

예시 질문:
• '열차 서울역에서 부산역까지 시간표 알려줘'
• '기차 대전역에서 동대구역까지 요금 알려줘'
🙋 열차 서울역에서 부산역까지 시간표 알려줘
🤖 출발지는 서울역, 도착지는 부산역 입니다.
🚄 서울역 → 부산역 열차 시간표

번호 | 열차종류  | 열차번호 | 출발시각 | 도착시각 | 요금  
-------------------------------------------------------------------
1  | KTX  | 1  | 05:13  | 07:50  | 59,800원
2  | KTX  | 3  | 05:27  | 08:16  | 59,800원
3  | 무궁화호  | 1301  | 05:54  | 11:39  | 28,600원
4  | KTX  | 5  | 05:58  | 08:43  | 59,400원
5  | KTX-산천(A-type) | 75  | 06:03  | 08:49  | 59,800원
...
※ 실제 예매/좌석 현황은 코레일/레츠코레일 등에서 확인하세요.
```

### [SC-05] 장난/비현실 여행지 입력 시 유머러스한 응답
```
🙋 하늘여행 추천해줄래?
🤖 '하늘여행 추천해줄래?'라니! 저도 꼭 가보고 싶지만 아직은 현실적인 여행지만 안내할 수 있어요 😅

예시: 서울, 부산, 제주도 등

🙋 시간여행 추천해줄래?
🤖 '시간여행 추천해줄래?'라니! 저도 꼭 가보고 싶지만 아직은 현실적인 여행지만 안내할 수 있어요 😅

예시: 서울, 부산, 제주도 등
```

### [SC-06] 영어로 대답해줘 → 영어 여행 추천 및 일정 생성
```
🙋 영어로 대답해줘
🤖 앞으로 영어로 답변드릴게요!
🙋 한국여행 추천해줄래?
🤖 Korea? Great choice! Korea has the following cities:
- Seoul
- Busan
- Jeju Island
- Gyeongju
- Jeonju
- Yeosu
- Gangneung
- Chuncheon
- Daegu
- Incheon
Which city would you like to visit?
🙋 seoul
🤖 You selected SEOUL! What are you most interested in for your trip? (e.g., food, nature, culture, shopping, etc.)
🙋 food
🤖 How many days would you like to plan for? (e.g., 3 days, 1 week, etc.)
🙋 3 day
🤖 Okay, let's craft a fantastic 3-day food-focused itinerary for Seoul! Get ready for a delicious adventure. This itinerary balances iconic food experiences with local favorites, offering a taste of Seoul's vibrant culinary scene.

**Trip Theme:** A Culinary Journey Through Seoul

**Duration:** 3 Days

**Focus:** Food Exploration – Street Food, Traditional Korean Cuisine, Trendy Cafes, and Market Delights

**Accommodation Suggestion:** (Based on budget – adjust as needed) – Stay in Myeongdong or Gangnam for easy access to restaurants and transportation.

---

**Day 1: Myeongdong – Street Food & Trendy Bites**

* **Morning (9:00 AM):** Arrive in Seoul, check into your accommodation. Head straight to Myeongdong! This district is a food lover's paradise.
* **Lunch (12:00 PM):** **Gogung Myeongdong** – Start with *Bibimbap* – a classic Korean mixed rice dish. They're known for their fresh ingredients and beautiful presentation. (Budget: 15,000 - 25,000 KRW)
* **Afternoon (2:00 PM):** **Street Food Tour in Myeongdong:** Explore the numerous street stalls. Try *Tteokbokki* (spicy rice cakes), *Kkopyeong* (Korean fried chicken), and *Hotteok* (sweet pancakes). (Budget: 10,000 - 20,000 KRW)
* **Late Afternoon (4:00 PM):** **Gogi House Myeongdong:** A must-visit for *Korean BBQ*. Choose your meat and let the chefs grill it to perfection. (Budget: 25,000 - 40,000 KRW)
* **Dinner (7:00 PM):** **Bingsu House Myeongdong:** Enjoy a delicious and colorful *Bingsu* – Korean shaved ice dessert with various toppings – like fruit, condensed milk, and whipped cream. (Budget: 10,000 - 20,000 KRW)
* **Evening (8:30 PM):**  Enjoy a late-night *Korean Coffee* at a trendy cafe like **Coffee & Tea House Myeongdong**.

---

**Day 2: Traditional Korean & Hidden Gems**

* **Morning (9:00 AM):** **Bukchon Hanok Village:** Wander through the charming traditional Korean houses.  Grab a *Jeon* (Korean pancake) at a local bakery. (Budget: 8,000 - 15,000 KRW)
* **Lunch (12:00 PM):** **Tosokchon Tteokguk Restaurant:**  A beautiful restaurant in Bukchon, serving a delicious and unique *Tteokguk* (rice porridge) with a view of the Cheonggyeonggung Square. (Budget: 20,000 - 30,000 KRW)
* **Afternoon (2:00 PM):** **Gyeongsu Gate & Namdaemun Market:** Explore the historic Gyeongsu Gate and the bustling Namdaemun Market, a huge wholesale market where you can find everything from fruits and vegetables to Korean snacks and tea. Sample *Korean dumplings* (mandu) – a staple! (Budget: 10,000 - 20,000 KRW)
* **Dinner (7:00 PM):** **Han Plaza (Gangnam):** Experience a traditional Korean restaurant with a stunning, multi-story tiled design.  Try *Samgyeopsal* (grilled pork belly) – a popular Korean dish. (Budget: 30,000 - 50,000 KRW)
* **Evening (9:00 PM):**  Enjoy a traditional Korean tea ceremony at a tea house in the Gangnam area.

---

**Day 3:  Noryangjin Fish Market & Local Specialties**

* **Morning (9:00 AM):** **Noryangjin Fish Market:**  Head to the vibrant Noryangjin Fish Market.  Watch the fishermen bring in the daily catch and sample fresh seafood.  (Budget: 15,000 - 25,000 KRW – consider a small seafood lunch)
* **Lunch (12:00 PM):** **Gogung Noryangjin:**  A popular restaurant specializing in *Gogi-gui* (Korean-style grilled fish) – a flavorful and unique dish. (Budget: 20,000 - 35,000 KRW)
* **Afternoon (2:00 PM):** **Insadong Tea House:**  Explore the traditional tea houses in Insadong, known for their beautiful tea and sweets. Sample *Bingsu* (again!) and perhaps a traditional Korean tea. (Budget: 10,000 - 20,000 KRW)
* **Late Afternoon (4:00 PM):**  **Han River Cruise (Optional):**  Take a relaxing boat tour on the Han River for a different perspective of Seoul. (Budget: 20,000 - 30,000 KRW)
* **Dinner (7:00 PM):** **Donggung Market:**  Enjoy a final Korean feast at Donggung Market – a vibrant market with a wide variety of street food stalls. Try *Korean fried chicken* and *Korean noodles*. (Budget: 15,000 - 25,000 KRW)

---

**Food Recommendations Beyond the Itinerary:**

* **Korean Street Food:**  *Kimchi Jjigae* (kimchi stew), *Kalguksu* (knife-cut noodles), *Hotteok* (sweet pancakes)
* **Korean Bakery:**  Try *Bungeoppang* (Korean-style donuts)
* **Ice Cream:**  *Gelato* is popular in Seoul, try a local brand.
* **Donburi (Rice Bowl):** A popular and comforting dish.

**Notes:**

* **Transportation:** Seoul has an excellent subway system – purchase a T-money card for easy travel.
* **Korean Phrases:** Learn a few basic Korean phrases – it's appreciated!
* **Budget:** This itinerary can be adjusted to fit different budgets.

To help me refine this itinerary further and tailor it to your preferences, could you tell me:

*  What's your approximate budget per day for food?
*  Are there any specific types of Korean food you're particularly interested in (e.g., spicy food, seafood, traditional)?
```

### [SC-07] 일정 변경 플로우: 일본-도쿄-음식-3일→2일
```
🙋 일본여행을 추천해줘
🤖 일본이요? 멋진 선택입니다! 일본에는 다음과 같은 도시들이 있습니다:
- 도쿄
- 오사카
- 교토
- 후쿠오카
- 삿포로
- 나고야
- 요코하마
- 고베
- 히로시마
- 나라
이 중에서 여행하고 싶은 도시가 있으신가요?
🙋 도쿄
🤖 도쿄를 선택하셨군요! 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)
🙋 음식
🤖 몇 박 며칠 일정으로 계획하고 계신가요? (예: 3일, 1주일 등)
🙋 3일
🤖 ## 일본 도쿄 3일 음식 여행 일정 (미리보기)

**여행 컨셉:** 도쿄의 다채로운 음식 문화를 경험하고, 현지 맛집 탐방과 함께 즐거운 시간을 보내는 여행

**숙소:** 신주쿠 또는 시부야 지역 (교통 편리, 맛집 접근성 좋음)

---

**1일차: 도쿄의 전통과 현대의 맛을 만나는 날**

*  **오전:**
  *  **오코노미야키 맛집:** 도쿄의 명소인 '오코노미야키 맛집'에서 든든한 한 끼 식사를 즐기세요. (예: 츠키오노미야키, 츠키오노미야키 츠키오노미야키)
*  **점심:**
  *  **가츠동 맛집:** '가츠동 맛집'에서 든든한 가츠동을 맛보세요. (예: 츠키오노미야키 가츠동)
*  **오후:**
  *  **신주쿠 시장:** 도쿄 최대의 전통 시장인 신주쿠 시장에서 다양한 길거리 음식과 신선한 식재료를 구경하고, 맛있는 길거리 음식을 맛보세요. (예: 덴푸라, 모츠나베)
*  **저녁:**
  *  **시부야 맛집:** '시부야 맛집'에서 붉은 노포 분위기에서 맛있는 일본식 라멘을 즐기세요. (예: 겐토쿠 라멘, 츠키오노미야키 라멘)

**2일차: 도쿄의 트렌디한 음식과 힐링 식당 탐방**

*  **오전:**
  *  **스시 맛집:** '스시 맛집'에서 신선한 해산물과 롤을 맛보세요. (예: 츠키오노미야키 스시)
*  **점심:**
  *  **우동 맛집:** '우동 맛집'에서 든든한 우동을 즐기세요. (예: 겐토쿠 우동)
*  **오후:**
  *  **다이칸야마:** '다이칸야마'에서 일본 전통 료칸 분위기에서 정갈한 일본 요리를 맛보세요. (예: 덴푸라, 롤)
*  **저녁:**
  *  **오모테산도 맛집:** '오모테산도 맛집'에서 고급 디저트와 함께 맛있는 일본 디저트를 즐기세요. (예: 츠키오노미야키 케이크)

**3일차: 특별한 경험을 위한 음식 탐방 & 마무리**

*  **오전:**
  *  **일본식 빵 맛집:** '일본식 빵 맛집'에서 다양한 종류의 일본식 빵을 맛보세요. (예: 겐토쿠 빵)
*  **점심:**
  *  **미술관 근처 맛집:** '미술관 근처 맛집'에서 훌륭한 음식과 함께 미술관을 둘러보세요. (예: 츠키오노미야키, 겐토쿠)
*  **오후:**
  *  **쿠시카츠 맛집:** '쿠시카츠 맛집'에서 다양한 종류의 쿠시카츠를 맛보세요. (예: 츠키오노미야키 쿠시카츠)
*  **저녁:**
  *  **자유로운 식사:** 도쿄의 맛집을 둘러보며 자유롭게 식사하고, 기념품을 구입하세요.

---

**추가 팁:**

*  **맛집 검색 앱 활용:** Google Maps, Tabelog 등 맛집 검색 앱을 활용하여 원하는 메뉴를 미리 검색하고 방문 장소를 확인하세요.
*  **길거리 음식:** 도쿄는 길거리 음식 문화가 발달하여, 다양한 종류의 길거리 음식을 즐기세요. (예: 타코야키, 모츠나베, 덴푸라)
*  **현지인 추천:** 현지인에게 추천을 받아 맛집을 찾는 것도 좋은 방법입니다.
*  **일본어 회화:** 간단한 일본어 회화를 익혀두면 현지인과 더욱 즐거운 시간을 보낼 수 있습니다.

**참고:** 위에 제시된 맛집은 예시이며, 개인의 취향에 따라 변경 가능합니다. 즐거운 일본 여행 되세요!
🙋 일정을 2일로 변경하면 어떨까?
🤖 ## 일본 도쿄 2일 음식 여행 일정 (2박 3일)

**여행 컨셉:** 도쿄의 다양한 음식 문화를 경험하고, 맛있는 음식을 즐기는 2일 여행

**숙소:** 신주쿠 또는 시부야 지역 (교통 편리, 다양한 음식 접근성)

---

**1일차**

* **오전 (9:00 - 12:00):** **신주쿠 츠키지 시장 (Tsukiji Outer Market)** 방문. 활기 넘치는 시장 구경, 신선한 해산물 맛보기 (오코노미야키, 튀김 등).
* **점심 (12:00 - 14:00):** 신주쿠 츠키지 시장 근처 맛집: **'츠키지 텐푸' (Tsukiji Tenpa)** - 신선한 해산물을 맛볼 수 있는 츠키지 덮밥 전문점.
* **오후 (14:00 - 17:00):** **오모e리 (Omotesando)** - 고급스러운 분위기, 맛있는 일본식 디저트 (마카롱, 붕어빵 등)와 커피를 즐기며 여유로운 시간을 보내기.
* **저녁 (18:00 - 21:00):** **오모테리 (Omotesando)** - 런치 메뉴를 활용하여 다양한 종류의 일본 음식 맛보기 (스시, 덮밥 등).
* **팁:** 츠키지 시장 주변 길거리 음식 체험 (가상): 튀김, 꼬치 등

---

**2일차**

* **오전 (9:00 - 12:00):** **아사히시 (Asakusa)** - **센소지 (Senso-ji Temple)** 방문 후, **아사히시 시장 (Asakusa Market)**에서 전통적인 길거리 음식 (모츠나베, 덴푸라 등) 맛보기.
* **점심 (12:00 - 14:00):** 아사히시 시장 근처 맛집: **'아사히시 덴푸라' (Asakusa Denfuura)** - 든든한 덴푸라 맛보기.
* **오후 (14:00 - 17:00):** **시부야 (Shibuya)** - **시부야 스크램블 (Shibuya Scramble)**를 구경하며, **'테레사' (Terasu)** - 힙한 분위기, 퀄리티 좋은 덮밥 전문점.
* **저녁 (18:00 - 21:00):** **시부야 벼룩시장 (Shibuya Flea Market)** - 기념품, 음식, 옷 등을 구경하며 즐거운 시간을 보내기.
* **팁:** 시부야 벼룩시장에서 팝콘, 튀김 등을 맛보기

---

**추가적인 음식 및 활동 (선택 사항):**

* **스시 & 롤:** 츠키지 시장, 시부야, 도쿄 본토 (오다이바)
* **라멘 & 우동:** 도쿄 본토 (다양한 라멘 맛집)
* **가이세키 요리:** 고급스러운 일본 가정식
* **구경:** 도쿄 국립 박물관, 겐지 정원, 롯폰기 힐즈 등
* **현지인 맛집 탐방:**  '쿠시카츠' (치즈 튀김), '모츠나베' (새우 국물 덮밥) 등

**참고:**

* 도쿄는 다양한 음식 문화를 즐길 수 있는 곳이므로, 여행 중 취향에 따라 메뉴를 자유롭게 변경 가능합니다.
* 현지 음식점의 가격대는 다소 차이가 있을 수 있으니, 미리 확인하는 것이 좋습니다.
* 일본어 회화 정도가 없다면, 번역 앱을 활용하거나, 간단한 일본어 표현을 익히는 것이 좋습니다.

**여행 준비물:**

* 여행자 보험
* 비자 (해외여행 시)
* 편안한 신발
* 카메라
* 한국어 번역 앱

**즐거운 일본 음식 여행 되세요!**
```

### [SC-08] 대화 저장

- 입력: 대화 진행 후 '대화 저장' 버튼 클릭
- 기대 결과: 대화가 저장됨, 저장 목록에 표시

### [SC-09] 대화 불러오기
- 입력: 저장된 대화 선택 후 '불러오기' 클릭
- 기대 결과: 해당 대화 내용과 상태가 복원됨

---

## 관심사 변경 시나리오 (도시 선택 후 관심사 변경)

🙋 한국여행 추천해줘
🤖 한국이요? 멋진 선택입니다! 한국에는 다음과 같은 도시들이 있습니다:
- 서울
- 부산
- 제주도
- 경주
- 전주
- 여수
- 강릉
- 춘천
- 대구
- 인천
이 중에서 여행하고 싶은 도시가 있으신가요?
🙋 서울
🤖 서울를 선택하셨군요! 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)
🙋 음식
🤖 몇 박 며칠 일정으로 계획하고 계신가요? (예: 3일, 1주일 등)
🙋 3일
🤖 (음식 중심의 서울 3일 여행 일정 생성)
🙋 관심사를 문화로 변경해줘
🤖 (문화 중심의 서울 3일 여행 일정 생성)

---

## 복합 입력(도시+일정+관심사) 시나리오

🙋 한국여행 서울로 3일 맛집추천해줄래?
🤖 서울 3일 맛집 여행 일정 (개인 취향에 따라 조정 가능)

(여기서 챗봇이 바로 맞춤형 3일 맛집 일정을 생성해줌)

---

## 도시 변경 시나리오

🙋 한국여행 추천해줘
🤖 한국이요? 멋진 선택입니다! 한국에는 다음과 같은 도시들이 있습니다:
- 서울
- 부산
- 제주도
- 경주
- 전주
- 여수
- 강릉
- 춘천
- 대구
- 인천
이 중에서 여행하고 싶은 도시가 있으신가요?
🙋 서울
🤖 서울를 선택하셨군요! 여행에서 가장 관심 있는 것은 무엇인가요? (예: 음식, 자연, 문화, 쇼핑 등)
🙋 음식
🤖 몇 박 며칠 일정으로 계획하고 계신가요? (예: 3일, 1주일 등)
🙋 3일
🤖 (서울 3일 음식 여행 일정 생성)
🙋 도시를 부산으로 변경해줘
🤖 (부산 3일 음식 여행 일정 생성)

---

> 이 파일은 AI 여행 추천 시스템의 주요 기능에 대한 테스트 케이스를 정리한 문서입니다.
> 신규 기능 추가/수정 시 테스트 케이스도 함께 업데이트하세요. 