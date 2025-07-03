"""
Colab을 통한 한국어 모델 다운로드 가이드

1. Colab에서 실행할 코드:
"""

COLAB_CODE = '''
# Colab에서 실행할 코드
!pip install transformers torch accelerate bitsandbytes

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 1. 모델 다운로드
model_name = "beomi/Llama-3-Open-Ko-8B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    load_in_8bit=True,
    device_map="auto",
    torch_dtype=torch.float16
)

# 2. 테스트
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
model.save_pretrained("./llama3-korean-local")
tokenizer.save_pretrained("./llama3-korean-local")

# 4. 압축 파일로 다운로드
!zip -r llama3-korean-local.zip ./llama3-korean-local/
from google.colab import files
files.download('llama3-korean-local.zip')
'''

def show_colab_guide():
    """Colab 다운로드 가이드 출력"""
    print("🚀 Colab을 통한 한국어 모델 다운로드 가이드")
    print("=" * 60)
    print()
    print("1️⃣ Colab에서 실행할 코드:")
    print("-" * 40)
    print(COLAB_CODE)
    print()
    print("2️⃣ 로컬에서 사용하는 방법:")
    print("-" * 40)
    print("""
# 1. Colab에서 다운로드한 zip 파일을 로컬로 복사
# 2. 압축 해제: llama3-korean-local.zip → llama3-korean-local 폴더
# 3. 로컬에서 모델 로드:

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 로컬 모델 로드
model = AutoModelForCausalLM.from_pretrained(
    "./llama3-korean-local",
    load_in_8bit=True,
    device_map="auto",
    torch_dtype=torch.float16
)
tokenizer = AutoTokenizer.from_pretrained("./llama3-korean-local")

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
    print("3️⃣ Ollama에 등록하는 방법:")
    print("-" * 40)
    print("""
# Modelfile 생성 (backend 폴더에)
FROM ./llama3-korean-local
PARAMETER temperature 0.7
PARAMETER top_p 0.9

# Ollama에 등록
ollama create llama3-korean -f Modelfile

# 사용
ollama run llama3-korean
""")

if __name__ == "__main__":
    show_colab_guide() 