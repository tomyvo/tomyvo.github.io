document.addEventListener("DOMContentLoaded", () => {
  // ===============================
  // SESSION
  // ===============================
  let sessionId = localStorage.getItem("chat_session_id");
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem("chat_session_id", sessionId);
  }

  // ===============================
  // CONFIG
  // ===============================
  const webhookUrl = "https://christianduren.app.n8n.cloud/webhook/8715b2dc-ff23-4a61-bb7c-2be1c7c0bc91";
  const messages = document.getElementById("chat-messages");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");
  const typingIndicator = document.getElementById("typing-indicator");
  const bubble = document.getElementById("chat-bubble");
  const widget = document.getElementById("chat-widget");
  const closeBtn = document.getElementById("chat-close");

  // ===============================
  // UI HELPERS
  // ===============================
  function addMessage(text, sender) {
    const div = document.createElement("div");
    div.className = "message " + sender;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    typingIndicator.classList.remove("hidden");
    messages.appendChild(typingIndicator);
    messages.scrollTop = messages.scrollHeight;
  }

  function hideTyping() {
    typingIndicator.classList.add("hidden");
  }

  // ===============================
  // SEND MESSAGE
  // ===============================
  async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;

    addMessage(msg, "user");
    input.value = "";
    showTyping();

    try {
      const res = await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, sessionId })
      });

      const data = await res.json();
      hideTyping();
      addMessage(data.reply || "Keine Antwort erhalten", "bot");

    } catch {
      hideTyping();
      addMessage("⚠️ Verbindungsfehler", "bot");
    }
  }

  // ===============================
  // EVENTS
  // ===============================
  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", e => { if (e.key === "Enter") sendMessage(); });

  bubble.addEventListener("click", () => {
    widget.classList.add("open");
    bubble.style.display = "none";
  });

  closeBtn.addEventListener("click", () => {
    widget.classList.remove("open");
    bubble.style.display = "flex";
  });
});
