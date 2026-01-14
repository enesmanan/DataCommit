// DataCommit RAG Chat Application
const API_BASE = '';

const HOST = {
    name: 'Enes Fehmi Manan',
    image: 'enes_fehmi_manan.jpg'
};

const GUESTS = {
    1: { name: 'Kaan Bıçakçı', image: 'kaan_bicakci.jpg' },
    2: { name: 'Bilge Yücel', image: 'bilge_yucel.jpg' },
    3: { name: 'Alara Dirik', image: 'alara_dirik.jpg' },
    4: { name: 'Olgun Aydın', image: 'olgun_aydin.jpg' },
    5: { name: 'Eren Akbaba', image: 'eren_akbaba.jpg' },
    6: { name: 'Taner Şekmen', image: 'taner_sekmen.jpg' },
    7: { name: 'Murat Şahin', image: 'murat_sahin.jpg' },
    8: { name: 'Göker Güner', image: 'goker_guner.jpg' }
};

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const statusDot = document.querySelector('.status-dot');
const statusText = document.querySelector('.status-text');
const guestGrid = document.getElementById('guestGrid');
const loadingTemplate = document.getElementById('loadingTemplate');

// Configure marked for safe HTML rendering
marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: false,
    mangle: false
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkStatus();
    renderGuestGrid();
    setupEventListeners();
});

function setupEventListeners() {
    userInput.addEventListener('input', handleInputChange);
    userInput.addEventListener('keydown', handleKeyDown);
    sendBtn.addEventListener('click', sendMessage);
}

function handleInputChange() {
    // Auto-resize textarea
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 150) + 'px';
    
    // Enable/disable send button
    sendBtn.disabled = !userInput.value.trim();
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (userInput.value.trim()) {
            sendMessage();
        }
    }
}

async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();
        
        if (data.status === 'ok' && data.documents > 0) {
            statusDot.classList.add('online');
            statusText.textContent = `${data.documents} chunks loaded`;
        } else {
            statusText.textContent = 'No data loaded';
        }
    } catch (error) {
        statusText.textContent = 'Connection error';
        console.error('Status check failed:', error);
    }
}

function renderGuestGrid() {
    const hostHtml = `
        <div class="guest-item">
            <img src="/static/images/${HOST.image}" 
                 alt="${HOST.name}"
                 onerror="this.src='https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(HOST.name)}&backgroundColor=216e39'">
            <span class="guest-episode">Sunucu</span>
            <span>${HOST.name}</span>
        </div>
    `;
    
    const guestsHtml = Object.entries(GUESTS).map(([ep, guest]) => `
        <div class="guest-item">
            <img src="/static/images/${guest.image}" 
                 alt="${guest.name}"
                 onerror="this.src='https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(guest.name)}&backgroundColor=216e39'">
            <span class="guest-episode">Bölüm ${ep}</span>
            <span>${guest.name}</span>
        </div>
    `).join('');
    
    guestGrid.innerHTML = hostHtml + guestsHtml;
}

function addUserMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `
        <div class="message-avatar emoji-avatar">
            <span>🥷</span>
        </div>
        <div class="message-content">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addLoadingMessage() {
    const clone = loadingTemplate.content.cloneNode(true);
    chatMessages.appendChild(clone);
    scrollToBottom();
}

function removeLoadingMessage() {
    const loading = chatMessages.querySelector('.loading-message');
    if (loading) loading.remove();
}

function addAssistantMessage(response, sources) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    
    // Render markdown
    const htmlContent = marked.parse(response);
    
    // Build sources HTML
    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `
            <div class="sources-container">
                <div class="sources-title">Kaynaklar</div>
                <div class="source-chips">
                    ${sources.map(src => `
                        <div class="source-chip">
                            <img src="/static/images/${src.image}" 
                                 alt="${src.guest}"
                                 onerror="this.src='https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(src.guest)}&backgroundColor=216e39'">
                            <span class="source-episode">Bölüm ${src.episode}</span>
                            <span class="source-guest">${src.guest}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    messageDiv.innerHTML = `
        <div class="message-avatar emoji-avatar">
            <span>🤖</span>
        </div>
        <div class="message-content">
            ${htmlContent}
            ${sourcesHtml}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addErrorMessage(error) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <img src="https://api.dicebear.com/7.x/bottts/svg?seed=error&backgroundColor=8b0000" alt="Error">
        </div>
        <div class="message-content" style="border-color: #f85149;">
            <p style="color: #f85149;">⚠️ Bir hata oluştu: ${escapeHtml(error)}</p>
        </div>
    `;
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

async function sendMessage() {
    const query = userInput.value.trim();
    if (!query) return;
    
    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    sendBtn.disabled = true;
    
    // Add user message
    addUserMessage(query);
    
    // Show loading
    addLoadingMessage();
    
    try {
        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        
        removeLoadingMessage();
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        addAssistantMessage(data.response, data.sources);
        
    } catch (error) {
        removeLoadingMessage();
        addErrorMessage(error.message);
        console.error('Chat error:', error);
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
