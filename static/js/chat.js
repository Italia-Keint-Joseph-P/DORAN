document.addEventListener('DOMContentLoaded', () => {
    // Generate or retrieve session_id
    let currentSessionId = sessionStorage.getItem('chat_session_id');
    if (!currentSessionId) {
        currentSessionId = crypto.randomUUID();
        sessionStorage.setItem('chat_session_id', currentSessionId);
    }

    const dayHeaders = document.querySelectorAll('.history-day-header');
    dayHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const historyList = header.nextElementSibling;
            if (historyList) historyList.classList.toggle('show');
        });
    });

    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatWelcome = document.querySelector('.chat-welcome');
    const suggestionButtons = document.querySelectorAll('.suggestion-btn');

    // Sidebar elements
    const sidebar = document.getElementById('chat-sidebar');
    const sidebarMinimize = document.getElementById('sidebar-minimize');
    const historyList = document.getElementById('history-list');

    // Load chat history if sidebar exists
    if (sidebar) {
        loadChatHistory();
    }

    // Minimize sidebar
    if (sidebarMinimize) {
        sidebarMinimize.addEventListener('click', () => {
            sidebar.classList.toggle('minimized');
            const icon = sidebarMinimize.querySelector('i');
            if (sidebar.classList.contains('minimized')) {
                icon.className = 'fas fa-chevron-right';
            } else {
                icon.className = 'fas fa-chevron-left';
            }
        });
    }

    async function loadChatHistory() {
        try {
            const response = await fetch('/get_chat_sessions_summary');
            if (response.ok) {
                const sessions = await response.json();
                displaySessions(sessions);
            }
        } catch (error) {
            console.error('Error loading chat sessions:', error);
        }
    }

    function displaySessions(sessions) {
        if (!historyList) return;

        historyList.innerHTML = '';

        sessions.forEach(session => {
            const sessionDiv = document.createElement('div');
            sessionDiv.className = 'history-session';

        const titleBtn = document.createElement('button');
        titleBtn.className = 'btn btn-outline-secondary w-100 text-start history-session-title d-flex justify-content-between align-items-center';
        titleBtn.addEventListener('click', (e) => {
            // Only load session if not clicking on delete button
            if (!e.target.closest('.history-session-delete')) {
                loadHistoryForSession(session.id);
            }
        });

        const titleText = document.createElement('span');
        titleText.textContent = session.title;

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn btn-sm btn-outline-danger ms-2 history-session-delete';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.title = 'Delete session';
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering the title click
            if (confirm('Are you sure you want to delete this chat session?')) {
                deleteSession(session.id);
            }
        });

        titleBtn.appendChild(titleText);
        titleBtn.appendChild(deleteBtn);

        sessionDiv.appendChild(titleBtn);
        historyList.appendChild(sessionDiv);
        });
    }

    async function deleteSession(sessionId) {
        try {
            const response = await fetch(`/delete_chat_session/${sessionId}`, {
                method: 'DELETE',
            });
            if (response.ok) {
                // Reload the sessions list
                loadChatHistory();
            } else {
                alert('Failed to delete session');
            }
        } catch (error) {
            console.error('Error deleting session:', error);
            alert('Error deleting session');
        }
    }

async function loadHistoryForSession(sessionId) {
    try {
        const response = await fetch(`/get_chat_session_history/${sessionId}`);
        if (response.ok) {
            const sessionData = await response.json();
            // Clear chat-messages
            chatMessages.innerHTML = '';
            // Hide welcome message if present
            if (chatWelcome) chatWelcome.style.display = 'none';
            // Show suggestion buttons to allow continuing chat
            const suggestionContainer = document.querySelector('.text-center');
            if (suggestionContainer) suggestionContainer.style.display = 'block';
            // Add messages
            sessionData.messages.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.classList.add('message', msg.sender === 'user' ? 'message-user' : 'message-bot');
                msgDiv.innerHTML = `
                    <div class="message-content">${msg.message}</div>
                    <div class="message-time"><i class="fas fa-${msg.sender === 'user' ? 'user' : 'robot'} me-1"></i>${new Date(msg.timestamp).toLocaleTimeString()}</div>
                `;
                chatMessages.appendChild(msgDiv);
            });
            scrollToBottom();
            // Update currentSessionId to this session
            currentSessionId = sessionId;
            sessionStorage.setItem('chat_session_id', currentSessionId);
        }
    } catch (error) {
        console.error('Error loading history for session:', error);
    }
}

    // New Chat button click handler
    const newChatBtn = document.getElementById('new-chat-btn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', () => {
            // Generate new session_id
            currentSessionId = crypto.randomUUID();
            sessionStorage.setItem('chat_session_id', currentSessionId);
            // Clear only message and typing indicator elements
            const elementsToRemove = chatMessages.querySelectorAll('.message, .typing-indicator');
            elementsToRemove.forEach(el => el.remove());
            // Show welcome message and suggestions
            if (chatWelcome) chatWelcome.style.display = 'block';
            const suggestionContainer = document.querySelector('.text-center');
            if (suggestionContainer) suggestionContainer.style.display = 'block';
            // Clear user input
            if (userInput) userInput.value = '';
            userInput.focus();
        });
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    if (chatWelcome) {
        const existingMessages = chatMessages.querySelectorAll('.message');
        if (existingMessages.length > 0) {
            chatWelcome.style.display = 'none';
            const suggestionContainer = document.querySelector('.text-center');
            if (suggestionContainer) suggestionContainer.style.display = 'none';
        }
    }

    async function sendMessage(message) {
        if (!message.trim()) return;

        if (chatWelcome && chatWelcome.style.display !== 'none') chatWelcome.style.display = 'none';
        const suggestionContainer = document.querySelector('.text-center');
        if (suggestionContainer && suggestionContainer.style.display !== 'none') suggestionContainer.style.display = 'none';

        const userMessageDiv = document.createElement('div');
        userMessageDiv.classList.add('message', 'message-user');
        userMessageDiv.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-time"><i class="fas fa-user me-1"></i>${new Date().toLocaleTimeString()}</div>
        `;
        chatMessages.appendChild(userMessageDiv);
        scrollToBottom();

        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('typing-indicator');
        typingIndicator.innerHTML = `
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        chatMessages.appendChild(typingIndicator);
        scrollToBottom();

        try {
            const response = await fetch('/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, session_id: currentSessionId }),
            });

            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();
            let botMessages = data.response;
            const timestamp = data.timestamp;

            setTimeout(() => {
                if (typingIndicator.parentNode) typingIndicator.remove();

                let responseText = '';
                if (Array.isArray(botMessages)) responseText = botMessages.join(' ');
                else responseText = botMessages || '';

                function isFallbackMessage(text) {
                    const fallbackMessages = [
                        "I'm sorry, I didn't quite get that.",
                        "Hmm, I'm not sure I understand.",
                        "Apologies, I couldn't find an answer."
                    ];
                    return fallbackMessages.some(msg => text.includes(msg));
                }

                if (responseText && responseText.trim() && !responseText.toLowerCase().includes('error') && !isFallbackMessage(responseText)) {
                    window.errorCounter = 0; // ✅ reset on success
                    botMessages = responseText;
                } else {
                    window.errorCounter = (window.errorCounter || 0) + 1;
                    if (window.errorCounter === 3) {
                        window.showEmailDirectoryFallback(responseText, window.errorCounter);
                        return; // ⛔ stop to avoid duplicate
                    } else {
                        botMessages = responseText;
                    }
                }

                const botMessageDiv = document.createElement('div');
                botMessageDiv.classList.add('message', 'message-bot');
                botMessageDiv.innerHTML = `
                    <div class="message-content">${botMessages}</div>
                    <div class="message-time"><i class="fas fa-robot me-1"></i>${new Date(timestamp).toLocaleTimeString()}</div>
                `;
                chatMessages.appendChild(botMessageDiv);

                scrollToBottom();
            }, 2000);
        } catch (error) {
            console.error('Error sending message:', error);
            if (typingIndicator.parentNode) typingIndicator.remove();
        }
    }

    chatForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;
        sendMessage(message);
        userInput.value = '';
        userInput.focus();
    });

    suggestionButtons.forEach(button => {
        button.addEventListener('click', () => {
            sendMessage(button.textContent.trim());
        });
    });

    // ✅ image modal code with carousel
    function initializeImageModal() {
        if (!document.querySelector('.image-modal')) {
            const modalHTML = `
                <div class="image-modal" id="imageModal">
                    <span class="close">&times;</span>
                    <button class="carousel-btn carousel-prev" id="prevBtn"><</button>
                    <img id="modalImage" src="" alt="Full size image">
                    <button class="carousel-btn carousel-next" id="nextBtn">></button>
                </div>
                <div class="gallery-modal" id="galleryModal">
                    <div class="gallery-content">
                        <span class="gallery-close">&times;</span>
                        <div class="gallery-images" id="galleryImages"></div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }

        const modal = document.getElementById('imageModal');
        const modalImg = document.getElementById('modalImage');
        const closeBtn = modal.querySelector('.close');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const galleryModal = document.getElementById('galleryModal');
        const galleryImages = document.getElementById('galleryImages');
        const galleryCloseBtn = galleryModal.querySelector('.gallery-close');

        let currentImages = [];
        let currentIndex = 0;

        function showImage(index) {
            if (currentImages.length > 0 && index >= 0 && index < currentImages.length) {
                currentIndex = index;
                modalImg.src = currentImages[currentIndex];
                updateButtons();
            }
        }

        function updateButtons() {
            if (currentImages.length <= 1) {
                prevBtn.style.display = 'none';
                nextBtn.style.display = 'none';
            } else {
                prevBtn.style.display = 'block';
                nextBtn.style.display = 'block';
            }
        }

        function nextImage() {
            if (currentImages.length > 1) {
                currentIndex = (currentIndex + 1) % currentImages.length;
                showImage(currentIndex);
            }
        }

        function prevImage() {
            if (currentImages.length > 1) {
                currentIndex = (currentIndex - 1 + currentImages.length) % currentImages.length;
                showImage(currentIndex);
            }
        }

        document.addEventListener('click', function(e) {
            if (e.target.closest('.image-gallery')) {
                const gallery = e.target.closest('.image-gallery');
                const imageUrls = gallery.getAttribute('data-images').split(',');
                currentImages = imageUrls;
                currentIndex = 0;
                showImage(0);
                modal.style.display = 'flex';
                modal.classList.add('show');
            } else if (e.target.classList.contains('message-image') && !e.target.classList.contains('gallery-image')) {
                const imageUrls = e.target.getAttribute('data-images')?.split(',') || [e.target.src];
                currentImages = imageUrls;
                currentIndex = 0;
                showImage(0);
                modal.style.display = 'flex';
                modal.classList.add('show');
            } else if (e.target.classList.contains('gallery-image')) {
                const gallery = e.target.closest('.gallery-modal');
                const imageUrls = gallery.querySelector('.gallery-images').children;
                const urls = Array.from(imageUrls).map(img => img.src);
                currentImages = urls;
                currentIndex = Array.from(imageUrls).indexOf(e.target);
                showImage(currentIndex);
                modal.style.display = 'flex';
                modal.classList.add('show');
            }
        });

        closeBtn.onclick = () => { modal.style.display = 'none'; modal.classList.remove('show'); currentImages = []; currentIndex = 0; };
        modal.onclick = e => { if (e.target === modal) { modal.style.display = 'none'; modal.classList.remove('show'); currentImages = []; currentIndex = 0; }};
        prevBtn.onclick = prevImage;
        nextBtn.onclick = nextImage;
        galleryCloseBtn.onclick = () => { galleryModal.style.display = 'none'; galleryModal.classList.remove('show'); };
        galleryModal.onclick = e => { if (e.target === galleryModal) { galleryModal.style.display = 'none'; galleryModal.classList.remove('show'); }};
        document.addEventListener('keydown', e => {
            if (modal.classList.contains('show')) {
                if (e.key === 'Escape') {
                    modal.style.display = 'none'; modal.classList.remove('show'); currentImages = []; currentIndex = 0;
                } else if (e.key === 'ArrowLeft') {
                    prevImage();
                } else if (e.key === 'ArrowRight') {
                    nextImage();
                }
            }
            if (galleryModal.classList.contains('show') && e.key === 'Escape') {
                galleryModal.style.display = 'none'; galleryModal.classList.remove('show');
            }
        });
    }

    initializeImageModal();
});
