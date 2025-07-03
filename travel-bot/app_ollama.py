from flask import Flask, request, jsonify
import requests
import time
import random

app = Flask(__name__)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"  # gemma3:1b 모델로 변경

def get_ollama_response_with_retry(prompt, max_retries=2, timeout=20):
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
            
            body = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 200,  # 응답 길이를 줄여서 속도 향상
                    "top_k": 40,  # 추가 옵션으로 응답 품질과 속도 조절
                    "repeat_penalty": 1.1  # 반복 방지
                }
            }

            res = requests.post(OLLAMA_URL, json=body, timeout=timeout)
            res.raise_for_status()
            
            resp_json = res.json()
            print(f"Ollama 응답 (시도 {attempt + 1}):", resp_json)
            
            content = ""
            if resp_json is not None and isinstance(resp_json, dict):
                content = resp_json.get("response", "")
            elif resp_json is not None:
                content = str(resp_json)
            
            # 응답 검증
            if content and content.strip() and not content.strip().startswith("죄송합니다"):
                return content
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

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    prompt = data.get("message")
    
    if not prompt:
        return jsonify({"error": "No message provided"}), 400

    try:
        content = get_ollama_response_with_retry(prompt)
        return jsonify({"response": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True) 