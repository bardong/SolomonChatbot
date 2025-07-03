#!/usr/bin/env python3
"""
Ollama 성능 최적화 및 타임아웃 문제 해결 스크립트
"""

import subprocess
import requests
import time
import json
import os

def check_ollama_status():
    """Ollama 서버 상태 확인"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return True, "Ollama 서버가 정상적으로 실행 중입니다."
        else:
            return False, f"Ollama 서버 응답 오류: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Ollama 서버에 연결할 수 없습니다."
    except Exception as e:
        return False, f"Ollama 서버 확인 중 오류: {str(e)}"

def get_ollama_models():
    """설치된 Ollama 모델 목록 확인"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        return []
    except:
        return []

def optimize_ollama_config():
    """Ollama 설정 최적화"""
    print("=== Ollama 성능 최적화 ===")
    
    # 1. 모델 정보 확인
    models = get_ollama_models()
    print(f"설치된 모델: {models}")
    
    # 2. 시스템 리소스 확인
    print("\n=== 시스템 리소스 확인 ===")
    try:
        # CPU 정보
        cpu_info = subprocess.check_output("wmic cpu get name", shell=True).decode()
        print(f"CPU: {cpu_info.split('\\n')[1].strip()}")
        
        # 메모리 정보
        memory_info = subprocess.check_output("wmic computersystem get TotalPhysicalMemory", shell=True).decode()
        memory_gb = int(memory_info.split('\\n')[1].strip()) / (1024**3)
        print(f"총 메모리: {memory_gb:.1f} GB")
        
        # 디스크 정보
        disk_info = subprocess.check_output("wmic logicaldisk get size,freespace,caption", shell=True).decode()
        print(f"디스크 정보:\n{disk_info}")
        
    except Exception as e:
        print(f"시스템 정보 확인 중 오류: {e}")
    
    # 3. Ollama 최적화 권장사항
    print("\n=== Ollama 최적화 권장사항 ===")
    print("1. 모델 크기 최적화:")
    print("   - gemma3:1b (현재 사용 중) - 좋은 선택")
    print("   - 더 빠른 응답을 원한다면: gemma3:1b-instruct")
    print("   - 더 정확한 응답을 원한다면: llama3.2:3b")
    
    print("\n2. 시스템 최적화:")
    print("   - 다른 프로그램 종료 (메모리 확보)")
    print("   - SSD 사용 권장")
    print("   - 충분한 냉각 (CPU 온도 관리)")
    
    print("\n3. Ollama 설정 최적화:")
    print("   - num_predict: 300 (응답 길이 제한)")
    print("   - temperature: 0.7 (적당한 창의성)")
    print("   - top_k: 40 (응답 품질과 속도 조절)")
    print("   - repeat_penalty: 1.1 (반복 방지)")
    
    print("\n4. 네트워크 최적화:")
    print("   - localhost 연결 사용 (현재 설정)")
    print("   - 방화벽 설정 확인")
    print("   - 프록시 설정 확인")

def test_ollama_performance():
    """Ollama 성능 테스트"""
    print("\n=== Ollama 성능 테스트 ===")
    
    test_prompts = [
        "안녕하세요",
        "서울 여행 추천해주세요",
        "일본 도쿄 3일 여행 계획 세워주세요"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n테스트 {i}: {prompt}")
        start_time = time.time()
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "gemma3:1b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 300,
                        "top_k": 40,
                        "repeat_penalty": 1.1
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                elapsed_time = time.time() - start_time
                result = response.json()
                response_text = result.get("response", "")
                print(f"응답 시간: {elapsed_time:.2f}초")
                print(f"응답 길이: {len(response_text)} 문자")
                print(f"응답 미리보기: {response_text[:100]}...")
                
                if elapsed_time > 20:
                    print("⚠️  응답 시간이 너무 깁니다!")
                elif elapsed_time > 10:
                    print("⚠️  응답 시간이 다소 깁니다.")
                else:
                    print("✅ 응답 시간이 적절합니다.")
            else:
                print(f"❌ 오류: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("❌ 타임아웃 발생")
        except Exception as e:
            print(f"❌ 오류: {e}")

def restart_ollama():
    """Ollama 재시작"""
    print("\n=== Ollama 재시작 ===")
    
    try:
        # Windows에서 Ollama 프로세스 종료
        subprocess.run("taskkill /f /im ollama.exe", shell=True, capture_output=True)
        print("Ollama 프로세스 종료됨")
        
        time.sleep(2)
        
        # Ollama 재시작
        subprocess.Popen("ollama serve", shell=True)
        print("Ollama 서버 재시작 중...")
        
        # 서버 시작 대기
        for i in range(10):
            time.sleep(1)
            if check_ollama_status()[0]:
                print("✅ Ollama 서버가 정상적으로 시작되었습니다.")
                return True
            print(f"서버 시작 대기 중... ({i+1}/10)")
        
        print("❌ Ollama 서버 시작 실패")
        return False
        
    except Exception as e:
        print(f"❌ Ollama 재시작 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 Ollama 성능 최적화 도구")
    print("=" * 50)
    
    # 1. Ollama 상태 확인
    is_running, status_msg = check_ollama_status()
    print(f"Ollama 상태: {status_msg}")
    
    if not is_running:
        print("\nOllama가 실행되지 않고 있습니다.")
        print("다음 명령어로 Ollama를 시작하세요:")
        print("ollama serve")
        return
    
    # 2. 성능 최적화 정보
    optimize_ollama_config()
    
    # 3. 성능 테스트
    test_ollama_performance()
    
    # 4. 재시작 옵션
    print("\n" + "=" * 50)
    restart_choice = input("\nOllama를 재시작하시겠습니까? (y/n): ").lower().strip()
    
    if restart_choice == 'y':
        if restart_ollama():
            print("\n재시작 후 성능 테스트를 다시 실행하세요.")
        else:
            print("\n재시작에 실패했습니다. 수동으로 ollama serve를 실행하세요.")
    
    print("\n최적화 완료!")

if __name__ == "__main__":
    main() 