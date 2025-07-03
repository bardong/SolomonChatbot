#!/usr/bin/env python3
"""
한국어 여행 챗봇 모델 학습 실행 스크립트
"""

import os
import subprocess
import sys
import time

def check_requirements():
    """필요한 패키지 설치 확인"""
    required_packages = [
        "transformers",
        "torch", 
        "peft",
        "datasets",
        "accelerate",
        "bitsandbytes"
    ]
    
    print("📦 필요한 패키지 확인 중...")
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - 설치됨")
        except ImportError:
            print(f"❌ {package} - 설치 필요")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n🔧 다음 패키지들을 설치해주세요:")
        for package in missing_packages:
            print(f"pip install {package}")
        return False
    
    return True

def create_dataset():
    """데이터셋 생성"""
    print("\n📝 데이터셋 생성 중...")
    try:
        subprocess.run([sys.executable, "create_dataset.py"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ 데이터셋 생성 실패")
        return False

def run_training():
    """모델 학습 실행"""
    print("\n🚀 모델 학습 시작...")
    
    # 학습 파라미터 설정
    training_config = {
        "model_id": "meta-llama/Meta-Llama-3-1B",
        "output_dir": "./lora-travel-bot",
        "num_epochs": 3,
        "batch_size": 2,
        "learning_rate": 2e-4
    }
    
    print(f"📋 학습 설정:")
    print(f"  - 모델: {training_config['model_id']}")
    print(f"  - 출력 디렉토리: {training_config['output_dir']}")
    print(f"  - 에포크: {training_config['num_epochs']}")
    print(f"  - 배치 크기: {training_config['batch_size']}")
    print(f"  - 학습률: {training_config['learning_rate']}")
    
    try:
        # 학습 스크립트 실행
        subprocess.run([sys.executable, "../llama3_finetune_lora.py"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ 모델 학습 실패")
        return False

def convert_to_ollama():
    """학습된 모델을 Ollama 형식으로 변환"""
    print("\n🔄 Ollama 모델 변환 중...")
    
    try:
        # 모델 변환 스크립트 실행
        convert_script = """
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import os

# 학습된 모델 로드
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3-1B")
model = PeftModel.from_pretrained(base_model, "./lora-travel-bot")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-1B")

# 통합된 모델 저장
model.save_pretrained("./travel-bot-model")
tokenizer.save_pretrained("./travel-bot-model")

print("✅ 모델 변환 완료!")
"""
        
        with open("convert_model.py", "w", encoding="utf-8") as f:
            f.write(convert_script)
        
        subprocess.run([sys.executable, "convert_model.py"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ 모델 변환 실패")
        return False

def create_ollama_modelfile():
    """Ollama Modelfile 생성"""
    print("\n📄 Ollama Modelfile 생성 중...")
    
    modelfile_content = """FROM ./travel-bot-model

TEMPLATE """{{ if .System }}<|system|>
{{ .System }}<|end|>
{{ end }}{{ if .Prompt }}<|user|>
{{ .Prompt }}<|end|>
{{ end }}<|assistant|>
{{ .Response }}<|end|>"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_predict 200

SYSTEM """당신은 한국 여행 전문가입니다. 한국의 다양한 도시와 지역에 대한 여행 정보를 제공하고, 개인화된 여행 일정을 추천해주세요. 항상 친근하고 도움이 되는 톤으로 답변하세요."""
"""
    
    with open("Modelfile", "w", encoding="utf-8") as f:
        f.write(modelfile_content)
    
    print("✅ Modelfile 생성 완료!")

def main():
    """메인 함수"""
    print("🚀 한국어 여행 챗봇 모델 학습")
    print("=" * 50)
    
    # 1. 패키지 확인
    if not check_requirements():
        print("\n❌ 필요한 패키지가 설치되지 않았습니다.")
        print("위의 명령어들을 실행한 후 다시 시도해주세요.")
        return
    
    # 2. 데이터셋 생성
    if not create_dataset():
        print("\n❌ 데이터셋 생성에 실패했습니다.")
        return
    
    # 3. 모델 학습
    if not run_training():
        print("\n❌ 모델 학습에 실패했습니다.")
        return
    
    # 4. Ollama 모델 변환
    if not convert_to_ollama():
        print("\n❌ 모델 변환에 실패했습니다.")
        return
    
    # 5. Modelfile 생성
    create_ollama_modelfile()
    
    print("\n🎉 학습 완료!")
    print("\n📋 다음 단계:")
    print("1. Ollama 모델 생성:")
    print("   ollama create travel-bot -f Modelfile")
    print("\n2. 모델 테스트:")
    print("   ollama run travel-bot")
    print("\n3. 챗봇에서 사용:")
    print("   OLLAMA_MODEL=travel-bot 환경변수 설정")

if __name__ == "__main__":
    main() 