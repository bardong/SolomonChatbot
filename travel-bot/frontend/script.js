let history = [];
let editingChatIdx = null;

async function sendMessage() {
  const input = document.getElementById("input");
  const message = input.value;
  const chatbox = document.getElementById("chatbox");
  const loading = document.getElementById("loading");
  const progressbar = document.getElementById("progressbar");
  let progress = 0;
  let progressInterval;

  if (!message.trim()) return;
  chatbox.innerHTML += `<div class="user">🙋 ${message}</div>`;
  input.value = "";

  // 대화 히스토리 추가
  history.push({ role: "user", content: message });

  // 로딩바 표시 및 애니메이션 시작
  loading.style.display = "block";
  progress = 0;
  progressbar.style.width = "0%";
  progressInterval = setInterval(() => {
    progress = Math.min(progress + Math.random() * 15, 95);
    progressbar.style.width = progress + "%";
  }, 400);

  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  const data = await res.json();
  // 로딩바 숨기기
  clearInterval(progressInterval);
  progressbar.style.width = "100%";
  setTimeout(() => { loading.style.display = "none"; }, 300);

  if (data.response) {
    // 텍스트가 잘리지 않도록 안전하게 처리
    const safeResponse = data.response
      .replace(/\n/g, '<br>')
      .replace(/\s{2,}/g, '&nbsp;&nbsp;') // 연속된 공백을 보존
      .replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;'); // 탭을 공백으로 변환
    
    chatbox.innerHTML += `<div class="bot">🤖 ${safeResponse}</div>`;
  } else if (data.days) {
    data.days.forEach(day => {
      const safeDay = day
        .replace(/\n/g, '<br>')
        .replace(/\s{2,}/g, '&nbsp;&nbsp;')
        .replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
      chatbox.innerHTML += `<div class="bot">🤖 ${safeDay}</div>`;
    });
  }
  // 히스토리에 assistant 응답 추가
  history.push({ role: "assistant", content: data.response || (data.days ? data.days.join("\n\n") : "") });
  
  // 응답이 완전히 렌더링된 후 스크롤
  setTimeout(() => {
    chatbox.scrollTop = chatbox.scrollHeight;
  }, 100);
}

async function loadHistory() {
  const chatbox = document.getElementById("chatbox");
  const res = await fetch("/history");
  const data = await res.json();
  data.forEach(entry => {
    chatbox.innerHTML += `<div class="user">🙋 ${entry.message}</div>`;
    chatbox.innerHTML += `<div class="bot">🤖 ${entry.response}</div>`;
  });
}

// 대화 저장 구조 예시
function saveChatHistoryToLocal(chatMeta, messages) {
  const historyKey = "chat-history";
  let chatHistory = [];
  try {
    chatHistory = JSON.parse(localStorage.getItem(historyKey)) || [];
  } catch (e) {
    chatHistory = [];
  }
  chatHistory.push({
    ...chatMeta,
    messages
  });
  localStorage.setItem(historyKey, JSON.stringify(chatHistory));
}

function formatDateTime(iso) {
  const d = new Date(iso);
  return d.getFullYear() + '-' +
    String(d.getMonth()+1).padStart(2,'0') + '-' +
    String(d.getDate()).padStart(2,'0') + ' ' +
    String(d.getHours()).padStart(2,'0') + ':' +
    String(d.getMinutes()).padStart(2,'0');
}

function renderChatHistoryList() {
  const modal = document.getElementById('chat-history-modal');
  const listDiv = document.getElementById('chat-history-list');
  const chatHistory = JSON.parse(localStorage.getItem('chat-history') || '[]');
  listDiv.innerHTML = '<h3>저장된 대화</h3>' + chatHistory.map((item, idx) => `
    <div style="border:1px solid #eee; border-radius:8px; margin:12px 0; padding:12px; background:#fafbfc;">
      <div style="font-size:1.1em; font-weight:bold;">📌 ${item.title}</div>
      <div>📅 ${formatDateTime(item.timestamp)}</div>
      <div>🗺️ 도시: ${item.city} &nbsp; 🍱 관심사: ${item.interest} &nbsp; 📆 일정: ${item.duration}</div>
      <div>👀 ${item.summary}</div>
      <div>💬 총 메시지: ${item.messageCount}</div>
      <div style="margin-top:8px;">
        <button onclick="loadChatFromHistory(${idx})">🔘 불러오기</button>
        <button onclick="deleteChatFromHistory(${idx})">🗑️ 삭제</button>
      </div>
    </div>
  `).join('') + '<button onclick="closeHistoryModal()">닫기</button>';
  modal.style.display = 'block';
}

function closeHistoryModal() {
  document.getElementById('chat-history-modal').style.display = 'none';
}

function loadChatFromHistory(idx) {
  const chatHistory = JSON.parse(localStorage.getItem('chat-history') || '[]');
  const chat = chatHistory[idx];
  if (!chat) return;
  clearChatUI();
  chat.messages.forEach(msg => addMessageToUI(msg.role, msg.content));
  history = chat.messages.slice(); // history 동기화
  // user_state에 불러온 정보 저장
  const userState = {
    destination: chat.city || '',
    destination_city: chat.city || '',
    interest: chat.interest || '',
    duration: chat.duration || ''
  };
  fetch('/user_state', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userState)
  });
  editingChatIdx = idx; // 수정모드 진입
  closeHistoryModal();
}

function deleteChatFromHistory(idx) {
  let chatHistory = JSON.parse(localStorage.getItem('chat-history') || '[]');
  chatHistory.splice(idx, 1);
  localStorage.setItem('chat-history', JSON.stringify(chatHistory));
  renderChatHistoryList();
}

function clearChatUI() {
  document.getElementById('chatbox').innerHTML = '';
  history = [];
}
function addMessageToUI(role, content) {
  const chatbox = document.getElementById('chatbox');
  const safeContent = content
    .replace(/\n/g, '<br>')
    .replace(/\s{2,}/g, '&nbsp;&nbsp;')
    .replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
  chatbox.innerHTML += `<div class="${role}">${role === 'user' ? '🙋' : '🤖'} ${safeContent}</div>`;
}

// 대화 저장 버튼 이벤트
window.addEventListener("DOMContentLoaded", () => {
  // 페이지 로드 시 user_state 초기화
  fetch("/reset_user_state", { method: "POST" });

  const input = document.getElementById("input");
  input.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // 대화 저장 버튼 이벤트
  document.getElementById("save-chat-btn").onclick = async function() {
    // user_state 정보 가져오기
    let userState = {};
    try {
      const res = await fetch("/user_state");
      if (res.ok) userState = await res.json();
    } catch (e) {}
    // 수정모드 여부 판단
    let chatHistory = JSON.parse(localStorage.getItem('chat-history') || '[]');
    let editingChat = (editingChatIdx !== null && chatHistory[editingChatIdx]) ? chatHistory[editingChatIdx] : null;
    // 제목 자동 생성
    let autoTitle = '여행 일정 대화';
    const city = userState.destination_city || userState.destination || '';
    const interest = userState.interest || '';
    const duration = userState.duration || '';
    if (city && interest && duration) {
      autoTitle = `${city}의 ${interest} ${duration} 여행`;
    } else if (city && interest) {
      autoTitle = `${city}의 ${interest} 여행`;
    } else if (city && duration) {
      autoTitle = `${city} ${duration} 여행`;
    } else if (city) {
      autoTitle = `${city} 여행`;
    }
    // 모달 생성
    const modal = document.createElement('div');
    modal.id = 'save-chat-modal';
    modal.style.position = 'fixed';
    modal.style.left = '0';
    modal.style.top = '0';
    modal.style.width = '100vw';
    modal.style.height = '100vh';
    modal.style.background = 'rgba(0,0,0,0.3)';
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    modal.innerHTML = `
      <div style=\"background:#fff; padding:32px 24px; border-radius:12px; min-width:480px; box-shadow:0 2px 16px #0002;\">
        <h3 style=\"margin-top:0;\">대화 ${editingChat ? '수정' : '저장'}</h3>
        <div style=\"margin-bottom:8px;\">
          <label>제목<br><input id=\"chat-title\" type=\"text\" style=\"width:80%;display:block;margin:0 auto;height:28px;padding:4px;\" value=\"${editingChat ? editingChat.title : autoTitle}\"></label>
        </div>
        <div style=\"margin-bottom:8px;\">
          <label>도시명<br><input id=\"chat-city\" type=\"text\" style=\"width:80%;display:block;margin:0 auto;height:28px;padding:4px;\" value=\"${editingChat ? editingChat.city : (userState.destination_city || userState.destination || '')}\"></label>
        </div>
        <div style=\"margin-bottom:8px;\">
          <label>관심사<br><input id=\"chat-interest\" type=\"text\" style=\"width:80%;display:block;margin:0 auto;height:28px;padding:4px;\" value=\"${editingChat ? editingChat.interest : (userState.interest || '')}\"></label>
        </div>
        <div style=\"margin-bottom:8px;\">
          <label>일정<br><input id=\"chat-duration\" type=\"text\" style=\"width:80%;display:block;margin:0 auto;height:28px;padding:4px;\" value=\"${editingChat ? editingChat.duration : (userState.duration || '')}\"></label>
        </div>
        <div style=\"margin-bottom:8px;\">
          <label>대화 요약<br><textarea id=\"chat-summary\" style=\"width:80%;display:block;margin:0 auto;height:40px;padding:4px;resize:vertical;\">${editingChat ? editingChat.summary : ''}</textarea></label>
        </div>
        <div style=\"text-align:right;\">
          <button id=\"save-chat-confirm\">${editingChat ? '수정' : '저장'}</button>
          <button id=\"save-chat-cancel\">취소</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    // 취소 버튼 이벤트
    document.getElementById('save-chat-cancel').onclick = function() {
      alert('취소하였습니다');
      document.body.removeChild(modal);
      editingChatIdx = null;
    };
    // 저장/수정 버튼 이벤트
    document.getElementById('save-chat-confirm').onclick = function() {
      const chatMeta = {
        id: editingChat ? editingChat.id : ("chat_" + Date.now()),
        title: document.getElementById('chat-title').value,
        timestamp: new Date().toISOString(),
        city: document.getElementById('chat-city').value,
        interest: document.getElementById('chat-interest').value,
        duration: document.getElementById('chat-duration').value,
        summary: document.getElementById('chat-summary').value,
        messageCount: history.length
      };
      let chatHistory = JSON.parse(localStorage.getItem('chat-history') || '[]');
      if (editingChatIdx !== null && chatHistory[editingChatIdx]) {
        // 수정 모드: 해당 idx에 덮어쓰기
        chatHistory[editingChatIdx] = { ...chatMeta, messages: history };
      } else {
        // 새로 저장
        chatHistory.push({ ...chatMeta, messages: history });
      }
      localStorage.setItem('chat-history', JSON.stringify(chatHistory));
      alert(editingChat ? "대화가 수정되었습니다!" : "대화가 저장되었습니다!");
      document.body.removeChild(modal);
      editingChatIdx = null;
    };
  };
  // 대화 불러오기 버튼 이벤트
  document.getElementById('open-history-btn').onclick = renderChatHistoryList;

  // 초기화 버튼 이벤트
  document.getElementById("reset-btn").onclick = async function() {
    if (!confirm("정말로 모든 대화와 상태를 초기화할까요?")) return;
    clearChatUI();
    // history 배열도 초기화
    history = [];
    // 백엔드 user_state 초기화
    await fetch("/reset_user_state", { method: "POST" });
    alert("대화와 상태가 모두 초기화되었습니다.");
  };
}); 