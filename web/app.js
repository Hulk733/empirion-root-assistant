// Empirion AI Assistant Web Client
class EmpirionAssistant {
    constructor() {
        this.ws = null;
        this.clientId = null;
        this.isConnected = false;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        
        // Load settings from localStorage
        this.settings = this.loadSettings();
        
        // Initialize UI elements
        this.initializeElements();
        this.attachEventListeners();
        
        // Connect to WebSocket
        this.connect();
    }
    
    initializeElements() {
        this.elements = {
            connectionStatus: document.getElementById('connectionStatus'),
            chatMessages: document.getElementById('chatMessages'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            voiceBtn: document.getElementById('voiceBtn'),
            settingsBtn: document.getElementById('settingsBtn'),
            settingsModal: document.getElementById('settingsModal'),
            closeSettings: document.getElementById('closeSettings'),
            saveSettings: document.getElementById('saveSettings'),
            wsUrl: document.getElementById('wsUrl'),
            userId: document.getElementById('userId'),
            language: document.getElementById('language'),
            quickActions: document.querySelectorAll('.quick-action')
        };
        
        // Set initial values from settings
        this.elements.wsUrl.value = this.settings.wsUrl;
        this.elements.userId.value = this.settings.userId;
        this.elements.language.value = this.settings.language;
    }
    
    attachEventListeners() {
        // Send message
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Voice recording
        this.elements.voiceBtn.addEventListener('click', () => this.toggleVoiceRecording());
        
        // Settings
        this.elements.settingsBtn.addEventListener('click', () => this.showSettings());
        this.elements.closeSettings.addEventListener('click', () => this.hideSettings());
        this.elements.saveSettings.addEventListener('click', () => this.saveSettingsAndReconnect());
        
        // Quick actions
        this.elements.quickActions.forEach((btn, index) => {
            btn.addEventListener('click', () => this.handleQuickAction(index));
        });
    }
    
    loadSettings() {
        const defaults = {
            wsUrl: 'ws://localhost:8765',
            userId: 'user123',
            language: 'en-US'
        };
        
        const saved = localStorage.getItem('empirionSettings');
        return saved ? { ...defaults, ...JSON.parse(saved) } : defaults;
    }
    
    saveSettings() {
        this.settings = {
            wsUrl: this.elements.wsUrl.value,
            userId: this.elements.userId.value,
            language: this.elements.language.value
        };
        
        localStorage.setItem('empirionSettings', JSON.stringify(this.settings));
    }
    
    connect() {
        try {
            this.ws = new WebSocket(this.settings.wsUrl);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus(true);
                
                // Authenticate
                this.authenticate();
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleMessage(message);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.connect(), 5000);
            };
            
        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateConnectionStatus(false);
        }
    }
    
    authenticate() {
        this.send({
            type: 'auth',
            data: {
                user_id: this.settings.userId,
                token: 'demo_token' // In production, use proper authentication
            }
        });
    }
    
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
            this.showNotification('Not connected to server', 'error');
        }
    }
    
    handleMessage(message) {
        console.log('Received message:', message);
        
        switch (message.type) {
            case 'connection':
                this.clientId = message.client_id;
                this.showNotification('Connected to Empirion Assistant', 'success');
                break;
                
            case 'auth_response':
                if (message.success) {
                    this.showNotification('Authentication successful', 'success');
                    // Subscribe to events
                    this.subscribeToEvents();
                } else {
                    this.showNotification('Authentication failed', 'error');
                }
                break;
                
            case 'response':
                this.handleAssistantResponse(message.data);
                break;
                
            case 'event':
                this.handleEvent(message);
                break;
                
            case 'error':
                this.showNotification(message.message, 'error');
                break;
        }
    }
    
    subscribeToEvents() {
        this.send({
            type: 'subscribe',
            events: ['notification', 'call', 'message', 'system']
        });
    }
    
    sendMessage() {
        const text = this.elements.messageInput.value.trim();
        if (!text) return;
        
        // Add user message to chat
        this.addChatMessage('user', text);
        
        // Clear input
        this.elements.messageInput.value = '';
        
        // Send to server
        this.send({
            type: 'request',
            request_id: this.generateRequestId(),
            data: {
                type: 'text',
                content: text,
                metadata: {
                    language: this.settings.language,
                    timestamp: new Date().toISOString()
                }
            }
        });
    }
    
    async toggleVoiceRecording() {
        if (!this.isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                this.mediaRecorder = new MediaRecorder(stream);
                this.audioChunks = [];
                
                this.mediaRecorder.ondataavailable = (event) => {
                    this.audioChunks.push(event.data);
                };
                
                this.mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                    await this.sendAudioMessage(audioBlob);
                    
                    // Stop all tracks
                    stream.getTracks().forEach(track => track.stop());
                };
                
                this.mediaRecorder.start();
                this.isRecording = true;
                this.elements.voiceBtn.classList.add('bg-red-600');
                this.elements.voiceBtn.classList.remove('bg-blue-600');
                
            } catch (error) {
                console.error('Failed to start recording:', error);
                this.showNotification('Microphone access denied', 'error');
            }
        } else {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.elements.voiceBtn.classList.remove('bg-red-600');
            this.elements.voiceBtn.classList.add('bg-blue-600');
        }
    }
    
    async sendAudioMessage(audioBlob) {
        // Convert audio to base64
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];
            
            this.addChatMessage('user', '🎤 Voice message');
            
            this.send({
                type: 'request',
                request_id: this.generateRequestId(),
                data: {
                    type: 'voice',
                    content: base64Audio,
                    metadata: {
                        language: this.settings.language,
                        format: 'wav',
                        timestamp: new Date().toISOString()
                    }
                }
            });
        };
        reader.readAsDataURL(audioBlob);
    }
    
    handleAssistantResponse(response) {
        if (response.status === 'success') {
            const content = response.content;
            
            // Add assistant message to chat
            if (content.message) {
                this.addChatMessage('assistant', content.message);
            } else if (content.response) {
                this.addChatMessage('assistant', content.response);
            }
            
            // Handle specific actions
            if (content.action) {
                this.handleAction(content);
            }
        } else {
            this.addChatMessage('assistant', 'Sorry, I encountered an error processing your request.');
        }
    }
    
    handleAction(content) {
        switch (content.action) {
            case 'phone_call':
                this.showNotification(`Initiating call to ${content.number}`, 'info');
                break;
                
            case 'send_message':
                this.showNotification('Opening messaging app...', 'info');
                break;
                
            case 'open_app':
                this.showNotification('Launching application...', 'info');
                break;
                
            case 'samsung_store':
                this.showNotification('Opening Samsung Store...', 'info');
                break;
                
            default:
                console.log('Unhandled action:', content.action);
        }
    }
    
    handleEvent(event) {
        switch (event.event_type) {
            case 'notification':
                this.showNotification(`New notification: ${event.data.title}`, 'info');
                break;
                
            case 'call':
                this.showNotification(`Incoming call from ${event.data.number}`, 'warning');
                break;
                
            case 'message':
                this.showNotification(`New message from ${event.data.sender}`, 'info');
                break;
                
            case 'system':
                this.showNotification(`System: ${event.data.message}`, 'info');
                break;
        }
    }
    
    handleQuickAction(index) {
        const actions = [
            { type: 'action', content: 'make_call', metadata: {} },
            { type: 'action', content: 'send_sms', metadata: {} },
            { type: 'action', content: 'open_samsung_store', metadata: {} },
            { type: 'action', content: 'open_settings', metadata: {} }
        ];
        
        if (actions[index]) {
            this.send({
                type: 'request',
                request_id: this.generateRequestId(),
                data: actions[index]
            });
        }
    }
    
    addChatMessage(sender, text) {
        const messagesContainer = this.elements.chatMessages;
        
        // Remove placeholder if exists
        const placeholder = messagesContainer.querySelector('.text-center');
        if (placeholder) placeholder.remove();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`;
        
        const bubble = document.createElement('div');
        bubble.className = `max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
            sender === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-gray-100'
        }`;
        bubble.textContent = text;
        
        messageDiv.appendChild(bubble);
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300 ${
            type === 'success' ? 'bg-green-600' :
            type === 'error' ? 'bg-red-600' :
            type === 'warning' ? 'bg-yellow-600' :
            'bg-blue-600'
        } text-white`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => notification.classList.add('translate-x-0'), 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    updateConnectionStatus(connected) {
        const statusBtn = this.elements.connectionStatus;
        const icon = statusBtn.querySelector('i');
        const text = statusBtn.querySelector('span');
        
        if (connected) {
            statusBtn.classList.remove('bg-red-600');
            statusBtn.classList.add('bg-green-600');
            text.textContent = 'Connected';
        } else {
            statusBtn.classList.remove('bg-green-600');
            statusBtn.classList.add('bg-red-600');
            text.textContent = 'Disconnected';
        }
    }
    
    showSettings() {
        this.elements.settingsModal.classList.remove('hidden');
    }
    
    hideSettings() {
        this.elements.settingsModal.classList.add('hidden');
    }
    
    saveSettingsAndReconnect() {
        this.saveSettings();
        this.hideSettings();
        
        // Disconnect current connection
        if (this.ws) {
            this.ws.close();
        }
        
        // Reconnect with new settings
        setTimeout(() => this.connect(), 500);
    }
    
    generateRequestId() {
        return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

// Initialize the assistant when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.empirionAssistant = new EmpirionAssistant();
});
