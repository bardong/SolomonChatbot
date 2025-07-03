from langdetect import detect
import os
import requests
import time
import random

def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

def get_system_prompt(lang):
    prompts = {
        "ko": (
            "여행 전문가입니다. 간결하고 실용적인 여행 일정을 추천해주세요.\n"
            "Day 1/2/3 형식으로 일정을 제시하고, 교통편과 비자 정보를 포함해주세요.\n"
            "국내 교통의 경우 예상 가격만 안내하고 공식 사이트 확인을 권장해주세요.\n"
        ),
        "en": (
            "You are a travel expert. Provide concise and practical travel itineraries.\n"
            "Present schedules in Day 1/2/3 format, including transportation and visa information.\n"
            "For domestic transportation, only provide estimated prices and recommend checking official sites.\n"
        ),
        "ja": (
            "旅行専門家です。簡潔で実用的な旅行スケジュールを提案してください。\n"
            "Day 1/2/3形式でスケジュールを提示し、交通手段とビザ情報を含めてください。\n"
            "国内交通の場合は予想価格のみ案内し、公式サイトでの確認を推奨してください。\n"
        )
    }
    return prompts.get(lang, prompts["en"])

def check_ollama_status():
    """Ollama 서버 상태를 확인합니다."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True, "Ollama 서버가 정상적으로 실행 중입니다."
        else:
            return False, f"Ollama 서버 응답 오류: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인해주세요."
    except requests.exceptions.Timeout:
        return False, "Ollama 서버 응답이 너무 느립니다."
    except Exception as e:
        return False, f"Ollama 서버 확인 중 오류: {str(e)}"

def use_ollama():
    return os.getenv("USE_OLLAMA", "true").lower() == "true"

def get_ollama_response(prompt, max_retries=2, timeout=120):
    """Ollama 응답을 가져오는 함수 (재시도 로직 포함)"""
    
    # 타임아웃 메시지 변형
    timeout_messages = [
        "죄송합니다. 응답이 너무 오래 걸리고 있습니다. 잠시 후 다시 시도해주세요.",
        "서버가 바쁜 상태입니다. 잠시 후 다시 시도해주세요.",
        "응답 생성에 시간이 걸리고 있습니다. 다시 시도해주세요.",
        "일시적으로 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
    ]
    
    for attempt in range(max_retries + 1):
        try:
            print(f"Ollama 요청 시도 {attempt + 1}/{max_retries + 1}")
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": os.getenv("OLLAMA_MODEL", "gemma3:1b"),
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 2000,  # 응답 길이 대폭 증가
                        "top_k": 40,  # 추가 옵션으로 응답 품질과 속도 조절
                        "repeat_penalty": 1.1  # 반복 방지
                    }
                },
                timeout=timeout
            )
            
            resp_json = response.json()
            print(f"Ollama 응답 (시도 {attempt + 1}):", resp_json)
            
            result = None
            if "response" in resp_json and resp_json["response"]:
                result = resp_json["response"]
            elif "message" in resp_json and "content" in resp_json["message"] and resp_json["message"]["content"]:
                result = resp_json["message"]["content"]
            elif "content" in resp_json and resp_json["content"]:
                result = resp_json["content"]
            else:
                result = str(resp_json)
            
            # 응답 검증
            if result and result.strip() and not result.strip().startswith("죄송합니다"):
                return result
            else:
                print(f"빈 응답 또는 오류 응답 (시도 {attempt + 1})")
                if attempt < max_retries:
                    time.sleep(1)  # 1초 대기 후 재시도
                    continue
                else:
                    return random.choice(timeout_messages)
                    
        except requests.exceptions.Timeout:
            print(f"타임아웃 발생 (시도 {attempt + 1})")
            if attempt < max_retries:
                time.sleep(2)  # 2초 대기 후 재시도
                continue
            else:
                return random.choice(timeout_messages)
                
        except requests.exceptions.ConnectionError:
            return "Ollama 서버에 연결할 수 없습니다. Ollama가 실행 중인지 확인해주세요."
            
        except Exception as e:
            print(f"Ollama 오류 (시도 {attempt + 1}): {str(e)}")
            if attempt < max_retries:
                time.sleep(1)
                continue
            else:
                return f"Ollama 응답 처리 중 오류가 발생했습니다: {str(e)}"
    
    return random.choice(timeout_messages)

def get_hf_response(prompt, max_retries=2, timeout=60):
    """HuggingFace 응답을 가져오는 함수 (재시도 로직 포함)"""
    
    timeout_messages = [
        "죄송합니다. 응답이 너무 오래 걸리고 있습니다. 잠시 후 다시 시도해주세요.",
        "서버가 바쁜 상태입니다. 잠시 후 다시 시도해주세요.",
        "응답 생성에 시간이 걸리고 있습니다. 다시 시도해주세요.",
        "일시적으로 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
    ]
    
    for attempt in range(max_retries + 1):
        try:
            print(f"HuggingFace 요청 시도 {attempt + 1}/{max_retries + 1}")
            
            headers = {"Authorization": f"Bearer {os.getenv('HF_API_KEY')}"}
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{os.getenv('HF_MODEL_ID')}",
                headers=headers,
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 1500,  # 응답 길이 대폭 증가
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=timeout
            )
            
            resp_json = response.json()
            print(f"HuggingFace 응답 (시도 {attempt + 1}):", resp_json)
            
            if isinstance(resp_json, list) and len(resp_json) > 0:
                result = resp_json[0].get("generated_text", "")
            elif isinstance(resp_json, dict):
                result = resp_json.get("generated_text", "")
            else:
                result = str(resp_json)
            
            if result and result.strip() and not result.strip().startswith("죄송합니다"):
                return result
            else:
                print(f"빈 응답 또는 오류 응답 (시도 {attempt + 1})")
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    return random.choice(timeout_messages)
                    
        except requests.exceptions.Timeout:
            print(f"타임아웃 발생 (시도 {attempt + 1})")
            if attempt < max_retries:
                time.sleep(2)
                continue
            else:
                return random.choice(timeout_messages)
                
        except requests.exceptions.ConnectionError:
            return "HuggingFace 서버에 연결할 수 없습니다. 인터넷 연결을 확인해주세요."
            
        except Exception as e:
            print(f"HuggingFace 오류 (시도 {attempt + 1}): {str(e)}")
            if attempt < max_retries:
                time.sleep(1)
                continue
            else:
                return f"HuggingFace 응답 처리 중 오류가 발생했습니다: {str(e)}"
    
    return random.choice(timeout_messages)

def ollama_pull_koalpaca():
    os.system("ollama pull koalpaca")

def ollama_run_koalpaca():
    os.system("ollama run koalpaca") 