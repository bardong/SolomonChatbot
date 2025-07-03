import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def merge_lora_weights(
    base_model_name="beomi/Llama-3-Open-Ko-8B",
    lora_model_path="./korean_travel_lora",
    output_dir="./korean_travel_merged"
):
    """LoRA 가중치를 기본 모델과 병합"""
    
    logger.info("LoRA 가중치 병합 시작...")
    
    try:
        # 1. 기본 모델과 토크나이저 로드
        logger.info(f"기본 모델 로딩 중: {base_model_name}")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        base_tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            trust_remote_code=True,
            use_fast=False
        )
        
        # 2. LoRA 모델 로드
        logger.info(f"LoRA 모델 로딩 중: {lora_model_path}")
        model = PeftModel.from_pretrained(base_model, lora_model_path)
        
        # 3. LoRA 가중치 병합
        logger.info("LoRA 가중치 병합 중...")
        merged_model = model.merge_and_unload()
        
        # 4. 병합된 모델 저장
        logger.info(f"병합된 모델 저장 중: {output_dir}")
        merged_model.save_pretrained(output_dir)
        base_tokenizer.save_pretrained(output_dir)
        
        logger.info("✅ LoRA 가중치 병합 완료!")
        
        return merged_model, base_tokenizer
        
    except Exception as e:
        logger.error(f"병합 중 오류 발생: {e}")
        raise

def test_merged_model(model, tokenizer, test_questions):
    """병합된 모델 테스트"""
    logger.info("병합된 모델 테스트 중...")
    
    model.eval()
    
    for question in test_questions:
        prompt = f"### 질문:\n{question}\n\n### 답변:\n"
        
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response.replace(prompt, "").strip()
        
        print(f"\n질문: {question}")
        print(f"답변: {response}")
        print("-" * 50)

def create_ollama_modelfile(output_dir="./korean_travel_merged"):
    """Ollama용 Modelfile 생성"""
    modelfile_content = f"""FROM {output_dir}

# 한국어 여행 챗봇 모델
# beomi/Llama-3-Open-Ko-8B 기반으로 한국어 여행 정보에 특화된 모델

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

# 시스템 프롬프트 설정
SYSTEM """당신은 한국어 여행 전문가입니다. 한국의 다양한 도시와 지역에 대한 여행 정보, 맛집 추천, 관광지 안내를 제공합니다. 항상 한국어로 친절하고 정확한 정보를 제공해주세요."""
"""
    
    with open("Modelfile_korean_travel", "w", encoding="utf-8") as f:
        f.write(modelfile_content)
    
    logger.info("✅ Ollama용 Modelfile 생성 완료: Modelfile_korean_travel")

def main():
    """메인 실행 함수"""
    # 테스트 질문들
    test_questions = [
        "서울 2일 여행 추천해줘",
        "부산 맛집 알려줘",
        "한국어로 인사해줘",
        "제주도 자연 관광 추천해줘"
    ]
    
    try:
        # 1. LoRA 가중치 병합
        merged_model, tokenizer = merge_lora_weights()
        
        # 2. 병합된 모델 테스트
        test_merged_model(merged_model, tokenizer, test_questions)
        
        # 3. Ollama용 Modelfile 생성
        create_ollama_modelfile()
        
        print("\n🎉 모든 작업 완료!")
        print("📁 병합된 모델: ./korean_travel_merged")
        print("📁 Ollama Modelfile: Modelfile_korean_travel")
        print("\n다음 명령어로 Ollama에 모델을 등록할 수 있습니다:")
        print("ollama create korean-travel -f Modelfile_korean_travel")
        
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        raise

if __name__ == "__main__":
    main() 