// Chat History Component
class ChatHistoryComponent {
    constructor() {
        this.container = document.getElementById('chatHistoryPanel');
        this.render();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <h2 class="text-lg font-semibold">Chat History</h2>
                    <button type="button" id="newChatButton" class="text-blue-500 hover:text-blue-700">
                        <i class="fas fa-plus-circle"></i> New
                    </button>
                </div>
                <div id="chatHistoryList" class="panel-body space-y-2">
                    <!-- Chat history items will be added here -->
                </div>
            </div>
        `;
    }

    bindEvents() {
        document.getElementById('newChatButton').addEventListener('click', () => {
            createNewChat();
        });
    }

    addChatToHistory(chatId, title, time, messageCount) {
        const chatItem = document.createElement('div');
        chatItem.className = 'p-3 rounded-lg border bg-blue-50 border-blue-300 cursor-pointer';
        chatItem.dataset.chatId = chatId;
        chatItem.innerHTML = `
            <div class="font-medium">${title}</div>
            <div class="text-xs text-gray-500 mt-1">
                <span>${time}</span>
                <span>${messageCount} messages</span>
            </div>
        `;
        
        chatItem.addEventListener('click', () => {
            // Load this chat conversation
            loadChat(chatId);
        });
        
        document.getElementById('chatHistoryList').prepend(chatItem);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatHistoryComponent = new ChatHistoryComponent();
});