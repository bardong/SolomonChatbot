"""
Colab을 통한 한국 여행 모델 다운로드 및 파인튜닝 가이드

이 스크립트는 Google Colab에서 한국어 모델을 다운로드하고,
로컬에서 파인튜닝할 수 있도록 도와줍니다.
"""

COLAB_DOWNLOAD_CODE = '''
# Colab에서 실행할 코드 - 모델 다운로드
!pip install transformers torch accelerate bitsandbytes peft datasets

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json

# 1. 베이스 모델 다운로드 (llama3.2:1b 대신 사용할 한국어 모델)
model_name = "beomi/Llama-3-Open-Ko-8B"
print(f"모델 다운로드 중: {model_name}")

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_8bit=True,
    device_map="auto",
    torch_dtype=torch.float16
)

# 2. 모델 테스트
test_prompt = "서울 3일 여행 추천해줘"
inputs = tokenizer(test_prompt, return_tensors="pt")
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_length=200,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"질문: {test_prompt}")
print(f"답변: {response}")

# 3. 모델 저장
print("모델 저장 중...")
model.save_pretrained("./llama3-korean-base")
tokenizer.save_pretrained("./llama3-korean-base")

# 4. 압축 파일로 다운로드
!zip -r llama3-korean-base.zip ./llama3-korean-base/
from google.colab import files
files.download('llama3-korean-base.zip')
print("다운로드 완료! llama3-korean-base.zip 파일을 로컬로 복사하세요.")
'''

COLAB_FINETUNE_CODE = '''
# Colab에서 실행할 코드 - 파인튜닝 (선택사항)
!pip install transformers torch accelerate bitsandbytes peft datasets

from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import LoraConfig, get_peft_model, TaskType
import torch
import json

# 1. 한국 여행 데이터셋 생성
travel_data = [
    {"input": "서울 3일 여행 추천해줘", "output": "서울 3일 여행 일정을 추천해드리겠습니다!\\n\\n### Day 1 - 전통과 현대의 조화\\n08:00 아침: 인천공항 도착 및 호텔 체크인\\n10:00 경복궁 관람 (입장료 3,000원)\\n12:00 점심: 광장시장 진주집 순대국밥 (8,000원)\\n14:00 창덕궁과 후원 관람 (입장료 3,000원)\\n16:00 북촌한옥마을 산책\\n18:00 저녁: 을지면옥 평양냉면 (12,000원)\\n20:00 남산타워 야경 (입장료 16,000원)\\n\\n### Day 2 - 쇼핑과 문화\\n09:00 아침: 명동 쇼핑거리\\n12:00 점심: 명동교자 칼국수 (9,000원)\\n14:00 홍대 거리 쇼핑과 카페투어\\n16:00 이태원 거리 관광\\n18:00 저녁: 한남동 맛집 투어\\n20:00 한강공원 야경 산책\\n\\n### Day 3 - 자연과 휴식\\n09:00 아침: 한강공원 자전거 타기 (대여 3,000원/시간)\\n12:00 점심: 강남 우래옥 한우구이 (25,000원)\\n14:00 강남역 쇼핑\\n16:00 코엑스몰과 스타필드\\n18:00 저녁: 강남역 맛집\\n\\n교통편: 지하철 1일권 4,500원, 교통카드 충전 권장"},
    {"input": "부산 맛집 추천해줘", "output": "부산의 대표 맛집들을 추천해드리겠습니다!\\n\\n### 해산물 맛집\\n1. 자갈치시장 횟집 - 신선한 회와 해산물 (25,000원)\\n2. 해운대 해물탕 - 해산물 전문 (15,000원)\\n3. 부산 회센터 - 다양한 해산물 (20,000원)\\n4. 송도 해수욕장 맛집 - 바다 전망 (18,000원)\\n5. 민락수변포차 - 야경과 함께 (12,000원)\\n\\n### 부산 특산물\\n1. 부산 돼지국밥 - 부산의 대표 음식 (8,000원)\\n2. 서면 밀면 - 부산 특산물 (7,000원)\\n3. 감천 맛집 - 감천문화마을 맛집 (10,000원)\\n4. 남포동 맛집 - 남포동 BIFF광장 근처 (12,000원)\\n5. 부산역 맛집 - 부산역 근처 맛집 (9,000원)\\n\\n### 특징\\n- 부산의 현지 맛집들입니다\\n- 해산물과 부산 특산물을 맛볼 수 있습니다\\n- 각각 다른 분야의 음식을 맛볼 수 있습니다"}
]

# 데이터셋 저장
with open('korean_travel_dataset.jsonl', 'w', encoding='utf-8') as f:
    for item in travel_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\\n')

# 2. 모델 로드
model_name = "beomi/Llama-3-Open-Ko-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_8bit=True,
    device_map="auto",
    torch_dtype=torch.float16
)

# 3. LoRA 설정
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj"]
)

model = get_peft_model(model, lora_config)

# 4. 데이터셋 준비
def prepare_data():
    data = []
    with open('korean_travel_dataset.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            prompt = f"질문: {item['input']}\\n답변: {item['output']}"
            data.append({"text": prompt})
    return data

dataset = prepare_data()

# 5. 학습 설정
training_args = TrainingArguments(
    output_dir="./lora_korean_travel",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_steps=100,
    logging_steps=10,
    save_steps=100,
    evaluation_strategy="no",
    save_total_limit=2,
)

# 6. 학습 실행
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=lambda data: {'input_ids': torch.stack([torch.tensor(item) for item in data])}
)

print("파인튜닝 시작...")
trainer.train()

# 7. 모델 저장
model.save_pretrained("./lora_korean_travel_final")
tokenizer.save_pretrained("./lora_korean_travel_final")

# 8. 압축 및 다운로드
!zip -r lora_korean_travel_final.zip ./lora_korean_travel_final/
from google.colab import files
files.download('lora_korean_travel_final.zip')
print("파인튜닝 완료! lora_korean_travel_final.zip 파일을 로컬로 복사하세요.")
'''

def show_enhanced_colab_guide():
    """향상된 Colab 다운로드 가이드 출력"""
    print("🚀 Colab을 통한 한국 여행 모델 다운로드 및 파인튜닝 가이드")
    print("=" * 70)
    print()
    
    print("📋 단계별 진행 방법:")
    print("1. Google Colab에서 모델 다운로드")
    print("2. 로컬로 파일 복사")
    print("3. 로컬에서 파인튜닝 또는 Ollama 등록")
    print()
    
    print("1️⃣ Google Colab에서 모델 다운로드:")
    print("-" * 50)
    print("1. https://colab.research.google.com 접속")
    print("2. 새 노트북 생성")
    print("3. 아래 코드를 복사하여 실행:")
    print()
    print("📝 다운로드 코드:")
    print(COLAB_DOWNLOAD_CODE)
    print()
    
    print("2️⃣ 파인튜닝 (선택사항):")
    print("-" * 50)
    print("다운로드 후 추가로 파인튜닝을 원한다면:")
    print()
    print("📝 파인튜닝 코드:")
    print(COLAB_FINETUNE_CODE)
    print()
    
    print("3️⃣ 로컬에서 사용하는 방법:")
    print("-" * 50)
    print("""
# 1. Colab에서 다운로드한 zip 파일을 로컬로 복사
# 2. 압축 해제: llama3-korean-base.zip → llama3-korean-base 폴더
# 3. 로컬에서 모델 로드:

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 로컬 모델 로드
model = AutoModelForCausalLM.from_pretrained(
    "./llama3-korean-base",
    load_in_8bit=True,
    device_map="auto",
    torch_dtype=torch.float16
)
tokenizer = AutoTokenizer.from_pretrained("./llama3-korean-base")

# 테스트
prompt = "서울 3일 여행 추천해줘"
inputs = tokenizer(prompt, return_tensors="pt")
with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_length=200,
        temperature=0.7,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(f"답변: {response}")
""")
    print()
    
    print("4️⃣ Ollama에 등록하는 방법:")
    print("-" * 50)
    print("""
# Modelfile 생성 (backend 폴더에)
FROM ./llama3-korean-base
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER max_tokens 500

# Ollama에 등록
ollama create llama3-korean-travel -f Modelfile

# 사용
ollama run llama3-korean-travel
""")
    print()
    
    print("5️⃣ 백엔드에서 사용하는 방법:")
    print("-" * 50)
    print("""
# app.py에서 모델명 변경
OLLAMA_MODEL = "llama3-korean-travel"  # 또는 환경변수에서 설정

# 서버 재시작
python app.py
""")
    print()
    
    print("⚠️  주의사항:")
    print("- Colab은 무료 버전에서 세션 시간이 제한됩니다")
    print("- 대용량 모델 다운로드는 시간이 오래 걸릴 수 있습니다")
    print("- GPU 메모리 부족 시 8bit 양자화를 사용합니다")
    print()
    
    print("🎯 권장사항:")
    print("- 먼저 다운로드만 진행하고, 성공하면 파인튜닝을 시도하세요")
    print("- 다운로드 중 네트워크 오류가 발생하면 다시 시도하세요")
    print("- 로컬에서 테스트 후 Ollama에 등록하세요")

if __name__ == "__main__":
    show_enhanced_colab_guide() 