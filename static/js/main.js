document.addEventListener("DOMContentLoaded", function () {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatMessages = document.getElementById('chat-messages');

    function appendMessage(sender, text) {
        if (!chatMessages) return;
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-bubble ${sender === 'user' ? 'user-msg' : 'ai-msg'}`;
        msgDiv.innerHTML = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage(textToSend) {
        const text = textToSend || chatInput.value.trim();
        if (!text) return;

        appendMessage('user', text);
        if (chatInput) chatInput.value = '';

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-bubble ai-msg';
        loadingDiv.innerText = 'جاري التفكير والتحليل... ⏳';
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            if (chatMessages.contains(loadingDiv)) chatMessages.removeChild(loadingDiv);
            appendMessage('ai', data.response || 'حدث خطأ في الاستجابة.');
        } catch (err) {
            if (chatMessages.contains(loadingDiv)) chatMessages.removeChild(loadingDiv);
            appendMessage('ai', '⚠️ تعذر الاتصال بالسيرفر.');
        }
    }

    if (sendBtn) sendBtn.addEventListener('click', () => sendMessage());
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); sendMessage(); }
        });
    }

    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const txt = this.getAttribute('data-msg') || this.innerText;
            sendMessage(txt);
        });
    });
});