from flask import Flask, request, jsonify, render_template_string
import os
import json
from datetime import datetime
import re
from subway import get_subway_info, get_station_info, get_line_info, get_congestion_info, get_delay_info
from llm import get_llm_response, ollama_llm

app = Flask(__name__)

# 채팅 기록 저장 파일
CHAT_HISTORY_FILE = "subway_chat_history.json"

def load_chat_history():
    """채팅 기록 로드"""
    try:
        if os.path.exists(CHAT_HISTORY_FILE):
            with open(CHAT_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"채팅 기록 로드 오류: {e}")
    return []

def save_chat_history(history):
    """채팅 기록 저장"""
    try:
        with open(CHAT_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"채팅 기록 저장 오류: {e}")

def extract_subway_info(user_input):
    """사용자 입력에서 지하철 정보 추출"""
    # 노선 패턴 매칭
    line_patterns = [
        r"(\d+호선)", r"(분당선)", r"(신분당선)", r"(경의중앙선)", r"(공항철도)"
    ]
    
    line = None
    for pattern in line_patterns:
        match = re.search(pattern, user_input)
        if match:
            line = match.group(1)
            break
    
    # 역명 패턴 매칭 (노선 다음에 오는 역명)
    station = None
    if line:
        # 노선 다음에 오는 역명 찾기
        line_index = user_input.find(line)
        remaining_text = user_input[line_index + len(line):]
        
        # 일반적인 역명 패턴
        station_patterns = [
            r"(\w+역)", r"(\w+정)", r"(\w+동)", r"(\w+구)"
        ]
        
        for pattern in station_patterns:
            match = re.search(pattern, remaining_text)
            if match:
                station = match.group(1)
                break
    
    # 목적지 추출
    destination = None
    if "에서" in user_input and "까지" in user_input:
        parts = user_input.split("에서")
        if len(parts) > 1:
            destination_part = parts[1].split("까지")[0]
            # 목적지에서 역명 추출
            for pattern in [r"(\w+역)", r"(\w+정)"]:
                match = re.search(pattern, destination_part)
                if match:
                    destination = match.group(1)
                    break
    
    return line, station, destination

def process_subway_query(user_input):
    """지하철 관련 쿼리 처리"""
    line, station, destination = extract_subway_info(user_input)
    # 출발역/도착역이 모두 없는 경우(경로 안내 요청 등)
    if (
        ("경로" in user_input or "길" in user_input or "가는 법" in user_input or "어떻게 가" in user_input)
        and (not station or not destination)
    ):
        return (
            "지하철 경로를 안내하려면 출발역과 도착역을 입력해 주세요! 🚇\n"
            "예시: '2호선 강남역에서 홍대입구역까지 경로 알려줘'\n"
            "또는 '서울역에서 강남역까지 어떻게 가나요?'\n"
            "출발역과 도착역을 입력해 주시면 빠르고 정확하게 안내해 드릴 수 있습니다."
        )
    # 기본 응답 템플릿
    if not line and not station:
        return "어떤 지하철 정보를 알고 싶으신가요? 노선이나 역명을 말씀해주세요! 🚇"
    # 노선 정보만 있는 경우
    if line and not station:
        line_info = get_line_info(line)
        if line_info.get("total_stations") != "정보 없음":
            return f"""
🚇 {line} 정보

📊 총 역 수: {line_info['total_stations']}개
📏 총 길이: {line_info['length']}
📝 설명: {line_info['description']}

어떤 역의 정보를 알고 싶으신가요?
"""
        else:
            return f"{line}에 대한 정보를 찾을 수 없습니다. 다른 노선을 시도해보세요."
    # 역 정보가 있는 경우
    if station:
        if line:
            # 노선과 역 정보 모두 있는 경우
            subway_info = get_subway_info(line, station, destination)
            return subway_info
        else:
            # 역 정보만 있는 경우
            station_info = get_station_info(station)
            if station_info.get("lines") != ["정보 없음"]:
                return f"""
🚇 {station}역 정보

🚉 환승 노선: {', '.join(station_info['lines'])}
🔄 환승 정보: {station_info['transfer']}
🏢 편의시설: {', '.join(station_info['facilities'])}
🚪 출구 정보: {', '.join(station_info['exits'])}

어떤 노선의 정보를 알고 싶으신가요?
"""
            else:
                return f"{station}에 대한 정보를 찾을 수 없습니다. 다른 역을 시도해보세요."
    return "지하철 정보를 찾을 수 없습니다. 노선과 역명을 정확히 입력해주세요."

@app.route('/')
def index():
    """메인 페이지"""
    html_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>서울 지하철 실시간 어시스턴트</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .chat-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 800px;
            height: 80vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            position: relative;
        }
        
        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .chat-header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .status-indicator {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4CAF50;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            white-space: pre-wrap;
            line-height: 1.4;
        }
        
        .message.bot .message-content {
            background: white;
            color: #333;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message-time {
            font-size: 11px;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .chat-input-form {
            display: flex;
            gap: 10px;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .chat-input:focus {
            border-color: #667eea;
        }
        
        .send-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            width: 45px;
            height: 45px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s;
        }
        
        .send-button:hover {
            transform: scale(1.05);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .loading.show {
            display: block;
        }
        
        .example-queries {
            margin-top: 15px;
            padding: 15px;
            background: #f0f2f5;
            border-radius: 10px;
        }
        
        .example-queries h4 {
            margin-bottom: 10px;
            color: #333;
            font-size: 14px;
        }
        
        .example-query {
            display: inline-block;
            background: white;
            padding: 8px 12px;
            margin: 5px;
            border-radius: 15px;
            font-size: 12px;
            color: #667eea;
            cursor: pointer;
            border: 1px solid #e0e0e0;
            transition: all 0.2s;
        }
        
        .example-query:hover {
            background: #667eea;
            color: white;
            transform: translateY(-1px);
        }
        
        .typing-indicator {
            display: none;
            padding: 12px 16px;
            background: white;
            border-radius: 18px;
            border: 1px solid #e0e0e0;
            margin-bottom: 15px;
        }
        
        .typing-indicator.show {
            display: block;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <div class="status-indicator"></div>
            <h1>🚇 서울 지하철 실시간 어시스턴트</h1>
            <p>실시간 지하철 정보와 친절한 안내를 제공합니다</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                <div class="message-content">
                    안녕하세요! 서울 지하철 실시간 어시스턴트입니다. 🚇<br><br>
                    어떤 지하철 정보를 알고 싶으신가요?<br>
                    • 실시간 열차 정보<br>
                    • 혼잡도 확인<br>
                    • 경로 안내<br>
                    • 역 정보 조회
                </div>
                <div class="message-time" id="currentTime"></div>
            </div>
            
            <div class="example-queries">
                <h4>💡 예시 질문</h4>
                <div class="example-query" onclick="sendMessage('2호선 강남역 정보 알려줘')">2호선 강남역 정보 알려줘</div>
                <div class="example-query" onclick="sendMessage('1호선 서울역에서 2호선 강남역까지 경로')">1호선 서울역에서 2호선 강남역까지 경로</div>
                <div class="example-query" onclick="sendMessage('3호선 혼잡도 확인')">3호선 혼잡도 확인</div>
                <div class="example-query" onclick="sendMessage('홍대입구역 정보')">홍대입구역 정보</div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        
        <div class="chat-input-container">
            <form class="chat-input-form" id="chatForm">
                <input type="text" class="chat-input" id="messageInput" placeholder="지하철 정보를 물어보세요..." autocomplete="off">
                <button type="submit" class="send-button" id="sendButton">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="22" y1="2" x2="11" y2="13"></line>
                        <polygon points="22,2 15,22 11,13 2,9"></polygon>
                    </svg>
                </button>
            </form>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const chatForm = document.getElementById('chatForm');
        const typingIndicator = document.getElementById('typingIndicator');
        
        // 현재 시간 표시
        function updateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('ko-KR', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            document.getElementById('currentTime').textContent = timeString;
        }
        updateTime();
        setInterval(updateTime, 1000);
        
        // 메시지 전송
        async function sendMessage(message) {
            if (!message.trim()) return;
            
            // 사용자 메시지 추가
            addMessage(message, 'user');
            messageInput.value = '';
            
            // 타이핑 표시
            showTyping();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                hideTyping();
                
                if (data.success) {
                    addMessage(data.response, 'bot');
                } else {
                    addMessage('죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.', 'bot');
                }
            } catch (error) {
                hideTyping();
                addMessage('서버 연결에 실패했습니다. 잠시 후 다시 시도해주세요.', 'bot');
                console.error('Error:', error);
            }
        }
        
        // 메시지 추가
        function addMessage(content, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date().toLocaleTimeString('ko-KR', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timeDiv);
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        // 타이핑 표시/숨김
        function showTyping() {
            typingIndicator.classList.add('show');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function hideTyping() {
            typingIndicator.classList.remove('show');
        }
        
        // 폼 제출 이벤트
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        });
        
        // Enter 키 이벤트
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const message = messageInput.value.trim();
                if (message) {
                    sendMessage(message);
                }
            }
        });
        
        // 입력 필드 포커스
        messageInput.focus();
    </script>
</body>
</html>
"""
    return render_template_string(html_template)

@app.route('/chat', methods=['POST'])
def chat():
    """채팅 API 엔드포인트"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'response': '메시지를 입력해주세요.'})
        
        # 채팅 기록 로드
        chat_history = load_chat_history()
        
        # 지하철 정보 처리
        subway_response = process_subway_query(user_message)
        
        # LLM을 사용한 응답 생성
        try:
            llm_response = get_llm_response(user_message, subway_response)
            
            # LLM 응답이 기본 메시지인 경우 지하철 정보만 반환
            if "Ollama 서버가 실행되지 않고 있습니다" in llm_response or "응답을 생성할 수 없습니다" in llm_response:
                response = subway_response
            else:
                response = llm_response
                
        except Exception as e:
            print(f"LLM 응답 생성 오류: {e}")
            response = subway_response
        
        # 응답이 비어있는 경우 기본 응답 제공
        if not response or response.strip() == "":
            response = "죄송합니다. 해당 정보를 찾을 수 없습니다. 다른 방법으로 질문해주세요."
        
        # 채팅 기록에 추가
        chat_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'bot_response': response
        })
        
        # 최근 50개 메시지만 유지
        if len(chat_history) > 50:
            chat_history = chat_history[-50:]
        
        # 채팅 기록 저장
        save_chat_history(chat_history)
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        print(f"채팅 처리 오류: {e}")
        return jsonify({
            'success': False,
            'response': '죄송합니다. 처리 중 오류가 발생했습니다.'
        })

@app.route('/history', methods=['GET'])
def get_history():
    """채팅 기록 조회"""
    try:
        history = load_chat_history()
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """채팅 기록 삭제"""
    try:
        save_chat_history([])
        return jsonify({'success': True, 'message': '채팅 기록이 삭제되었습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/status', methods=['GET'])
def status():
    """서버 상태 확인"""
    try:
        ollama_status = ollama_llm.check_server_status()
        return jsonify({
            'success': True,
            'ollama_status': ollama_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("🚇 서울 지하철 실시간 어시스턴트 서버를 시작합니다...")
    print("📍 서버 주소: http://localhost:5000")
    print("🔧 Ollama 서버 상태 확인 중...")
    
    if ollama_llm.check_server_status():
        print("✅ Ollama 서버가 정상 작동 중입니다.")
    else:
        print("⚠️  Ollama 서버가 실행되지 않고 있습니다.")
        print("   LLM 기능을 사용하려면 Ollama를 설치하고 실행해주세요.")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 