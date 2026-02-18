/* ===============================
   PulseGuard AI Chatbot Logic
================================ */

const CHATBOT_API = "https://lifesquad-pulseguard1.onrender.com/api/chatbot/ask";

let chatOpen = false;

function toggleChat() {
    chatOpen = !chatOpen;

    const cb = document.getElementById("chatbot");
    const btn = document.getElementById("chatBtn");

    if (chatOpen) {
        cb.classList.add("on");
        btn.innerHTML = "✖";
    } else {
        cb.classList.remove("on");
        btn.innerHTML = "💬";
    }
}

function sendChatMsg() {

    const inp = document.getElementById("chatInput");
    const txt = inp.value.trim();

    if (!txt) return;

    const msgs = document.getElementById("chatMsgs");

    // User message
    const userMsg = document.createElement("div");
    userMsg.className = "chat-msg user";
    userMsg.innerHTML =
        `<div class="chat-bubble user-bubble">${escapeHtml(txt)}</div>`;

    msgs.appendChild(userMsg);
    inp.value = "";
    scrollChat();

    showTyping();

    // Send to backend
    fetch(CHATBOT_API, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ question: txt })
    })
        .then(res => {
            if (!res.ok) {
                throw new Error(`Server Error: ${res.status} ${res.statusText}`);
            }
            return res.json();
        })
        .then(data => {
            removeTyping();
            if (data.response) {
                showBotMsg(data.response);
            } else if (data.advice) {
                showBotMsg(data.advice);
            } else if (data.reply) {
                showBotMsg(data.reply);
            } else {
                showBotMsg("⚠️ No response content.");
            }
        })
        .catch(err => {
            console.error(err);
            removeTyping();
            showBotMsg(`❌ Error: ${err.message}`);
        });
}

/* ===============================
   UI Helpers
================================ */

function showBotMsg(text) {

    const msgs = document.getElementById("chatMsgs");

    const botMsg = document.createElement("div");
    botMsg.className = "chat-msg bot";

    botMsg.innerHTML =
        `<div class="chat-avatar">🤖</div>
     <div class="chat-bubble bot-bubble">${text}</div>`;

    msgs.appendChild(botMsg);
    scrollChat();
}

function showTyping() {

    const msgs = document.getElementById("chatMsgs");

    const typing = document.createElement("div");
    typing.className = "chat-msg bot";
    typing.id = "typing";

    typing.innerHTML =
        `<div class="chat-avatar">🤖</div>
     <div class="chat-bubble bot-bubble typing-bubble">
       <div class="typing-dot"></div>
       <div class="typing-dot"></div>
       <div class="typing-dot"></div>
     </div>`;

    msgs.appendChild(typing);
    scrollChat();
}

function removeTyping() {
    document.getElementById("typing")?.remove();
}

function scrollChat() {
    const msgs = document.getElementById("chatMsgs");
    msgs.scrollTop = msgs.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
