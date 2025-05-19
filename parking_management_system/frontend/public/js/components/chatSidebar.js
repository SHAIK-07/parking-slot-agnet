// Chat Sidebar Component
class ChatSidebarComponent {
    constructor() {
        this.container = document.getElementById('chatHistorySidebar');
        this.conversationsList = document.getElementById('conversationsList');
        this.conversations = [];
        this.activeConversationId = null;
        this.render();
        this.bindEvents();
        this.fetchConversations();
    }

    render() {
        // The HTML structure is already in index.html
    }

    bindEvents() {
        // Search conversations
        const searchInput = document.getElementById('searchConversations');
        if (searchInput) {
            searchInput.addEventListener('input', () => {
                this.searchConversations(searchInput.value.trim());
            });

            // Clear search when ESC is pressed
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    searchInput.value = '';
                    this.searchConversations('');
                }
            });
        }
    }

    searchConversations(query) {
        // If no query, show all conversations
        if (!query) {
            document.querySelectorAll('#conversationsList > div').forEach(item => {
                if (item.classList.contains('conversation-item')) {
                    item.style.display = 'block';
                }
            });
            return;
        }

        // Convert query to lowercase for case-insensitive search
        query = query.toLowerCase();

        // Filter conversations
        document.querySelectorAll('#conversationsList > div').forEach(item => {
            if (item.classList.contains('conversation-item')) {
                const title = item.querySelector('.conversation-title');
                if (title && title.textContent.toLowerCase().includes(query)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            }
        });
    }

    fetchConversations() {
        // Get current user ID
        const userId = localStorage.getItem('userId');
        if (!userId) return;

        // Show loading state
        this.conversationsList.innerHTML = `
            <div class="text-center py-4 text-gray-500">
                <i class="fas fa-spinner fa-spin"></i>
                <p class="text-sm mt-2">Loading conversations...</p>
            </div>
        `;

        // Fetch conversations from API
        fetch(`${API_BASE_URL}/chat-history/conversations`, {
            headers: {
                'X-User-ID': userId
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load conversations');
            }
            return response.json();
        })
        .then(conversations => {
            this.conversations = conversations;
            this.renderConversations();
        })
        .catch(error => {
            console.error('Error fetching conversations:', error);
            this.conversationsList.innerHTML = `
                <div class="text-center py-4 text-red-500">
                    <i class="fas fa-exclamation-circle"></i>
                    <p class="text-sm mt-2">Failed to load conversations</p>
                </div>
            `;
        });
    }

    renderConversations() {
        if (this.conversations.length === 0) {
            this.conversationsList.innerHTML = `
                <div class="text-center py-4 text-gray-500">
                    <p class="text-sm">No conversations yet</p>
                    <p class="text-xs mt-2">Start a new chat to begin</p>
                </div>
            `;
            return;
        }

        this.conversationsList.innerHTML = '';

        // Sort conversations by updated_at (newest first)
        this.conversations.sort((a, b) => {
            return new Date(b.updated_at) - new Date(a.updated_at);
        });

        this.conversations.forEach(conversation => {
            this.addConversationToSidebar(conversation);
        });
    }

    addConversationToSidebar(conversation) {
        const conversationItem = document.createElement('div');
        conversationItem.className = `conversation-item p-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
            conversation.conversation_id === this.activeConversationId ? 'bg-blue-50' : ''
        }`;
        conversationItem.dataset.conversationId = conversation.conversation_id;

        // Format date
        const date = new Date(conversation.updated_at);
        const formattedDate = date.toLocaleDateString();

        conversationItem.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex-1 truncate conversation-title-container">
                    <div class="font-medium truncate conversation-title" title="${conversation.name}">${conversation.name}</div>
                    <input type="text" class="conversation-title-input hidden w-full border border-blue-300 rounded px-2 py-1 text-sm" value="${conversation.name}">
                    <div class="text-xs text-gray-500 flex items-center">
                        <i class="far fa-clock mr-1"></i> ${formattedDate}
                    </div>
                </div>
                <div class="flex items-center">
                    <button type="button" class="edit-conversation-btn text-gray-400 hover:text-blue-500 ml-2" title="Rename conversation">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button type="button" class="delete-conversation-btn text-gray-400 hover:text-red-500 ml-2" title="Delete conversation">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `;

        // Add click event to load conversation
        conversationItem.addEventListener('click', (e) => {
            // Don't trigger if buttons were clicked
            if (e.target.closest('.delete-conversation-btn') ||
                e.target.closest('.edit-conversation-btn') ||
                e.target.closest('.conversation-title-input')) {
                return;
            }

            this.loadConversation(conversation.conversation_id);
        });

        // Add delete button event
        const deleteBtn = conversationItem.querySelector('.delete-conversation-btn');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteConversation(conversation.conversation_id);
        });

        // Add edit button event
        const editBtn = conversationItem.querySelector('.edit-conversation-btn');
        editBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.startEditingConversation(conversationItem, conversation.conversation_id);
        });

        // Add input blur and keydown events
        const titleInput = conversationItem.querySelector('.conversation-title-input');
        titleInput.addEventListener('blur', () => {
            this.finishEditingConversation(conversationItem, conversation.conversation_id);
        });

        titleInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                titleInput.blur();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                // Reset to original value
                titleInput.value = conversation.name;
                titleInput.blur();
            }
        });

        this.conversationsList.appendChild(conversationItem);
    }

    loadConversation(conversationId) {
        console.log('Loading conversation:', conversationId);

        // Set active conversation
        this.activeConversationId = conversationId;

        // Store the conversation ID in localStorage
        localStorage.setItem('currentConversationId', conversationId);

        // Update UI to show active conversation
        document.querySelectorAll('#conversationsList > div').forEach(item => {
            if (item.dataset.conversationId === conversationId) {
                item.classList.add('bg-blue-50');
            } else {
                item.classList.remove('bg-blue-50');
            }
        });

        // Set current conversation ID in chat interface
        if (window.chatInterfaceComponent) {
            window.chatInterfaceComponent.currentConversationId = conversationId;
            window.currentConversationId = conversationId;

            // Show loading indicator in chat
            window.chatInterfaceComponent.clearChat();
            window.chatInterfaceComponent.addAssistantMessage('<i class="fas fa-spinner fa-spin"></i> Loading conversation...');
        }

        // Load conversation messages
        this.fetchConversationMessages(conversationId);
    }

    fetchConversationMessages(conversationId) {
        console.log('Fetching messages for conversation:', conversationId);
        const userId = localStorage.getItem('userId');
        if (!userId) {
            console.error('No user ID found when fetching conversation messages');
            return;
        }

        // Show loading indicator
        if (window.chatInterfaceComponent) {
            window.chatInterfaceComponent.clearChat();
            window.chatInterfaceComponent.addAssistantMessage('<i class="fas fa-spinner fa-spin"></i> Loading conversation...');
        }

        // Store the conversation ID in localStorage immediately
        localStorage.setItem('currentConversationId', conversationId);

        // Set the current conversation ID in window and chat interface
        window.currentConversationId = conversationId;
        if (window.chatInterfaceComponent) {
            window.chatInterfaceComponent.currentConversationId = conversationId;
        }

        // Make the API call with a retry mechanism
        this.fetchConversationMessagesWithRetry(conversationId, userId, 3);
    }

    fetchConversationMessagesWithRetry(conversationId, userId, retryCount = 3) {
        console.log(`Attempting to fetch messages for conversation ${conversationId} (retries left: ${retryCount})`);

        fetch(`${API_BASE_URL}/chat-history/conversations/${conversationId}`, {
            headers: {
                'X-User-ID': userId
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load conversation messages: ${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then(messages => {
            console.log(`Successfully loaded ${messages.length} messages for conversation ${conversationId}`);

            if (window.chatInterfaceComponent) {
                // Only process if this is still the active conversation
                if (window.currentConversationId === conversationId) {
                    // Clear existing messages
                    window.chatInterfaceComponent.clearChat();

                    if (messages.length === 0) {
                        // If no messages, show welcome message
                        window.chatInterfaceComponent.addAssistantMessage('Welcome to a new conversation! How can I help you with parking today?');
                    } else {
                        // Add messages
                        messages.forEach(message => {
                            window.chatInterfaceComponent.addUserMessage(message.user_query);
                            window.chatInterfaceComponent.addAssistantMessage(message.agent_response);
                        });
                    }

                    // Scroll to bottom
                    window.chatInterfaceComponent.scrollToBottom();
                } else {
                    console.log(`Conversation ${conversationId} is no longer active, not updating UI`);
                }
            }
        })
        .catch(error => {
            console.error(`Error loading conversation messages for ${conversationId}:`, error);

            // Retry if we have retries left
            if (retryCount > 0) {
                console.log(`Retrying fetch for conversation ${conversationId}...`);
                setTimeout(() => {
                    this.fetchConversationMessagesWithRetry(conversationId, userId, retryCount - 1);
                }, 1000); // Wait 1 second before retrying
                return;
            }

            // Show error message in chat if this is still the active conversation
            if (window.chatInterfaceComponent && window.currentConversationId === conversationId) {
                window.chatInterfaceComponent.clearChat();
                window.chatInterfaceComponent.addAssistantMessage('Sorry, there was an error loading the conversation. Please try again or start a new chat.');
            }
        });
    }

    createNewChat() {
        // Create new conversation on backend
        const userId = localStorage.getItem('userId');
        if (!userId) return;

        // Show loading state in chat interface
        if (window.chatInterfaceComponent) {
            window.chatInterfaceComponent.clearChat();
            window.chatInterfaceComponent.addAssistantMessage('<i class="fas fa-spinner fa-spin"></i> Creating new conversation...');
        }

        // Show loading state in sidebar
        const newChatBtn = document.getElementById('newChatSidebarBtn');
        if (newChatBtn) {
            // Save original content for reference (not used but kept for future use)
            // const originalContent = newChatBtn.innerHTML;
            newChatBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            newChatBtn.disabled = true;
        }

        fetch(`${API_BASE_URL}/chat-history/conversations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId
            },
            body: JSON.stringify({
                name: 'New Chat'
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to create new conversation');
            }
            return response.json();
        })
        .then(data => {
            // Add new conversation to list
            this.conversations.unshift(data);
            this.renderConversations();

            // Set as active conversation
            this.loadConversation(data.conversation_id);

            // Clear chat interface and show welcome message
            if (window.chatInterfaceComponent) {
                window.chatInterfaceComponent.clearChat();
                window.chatInterfaceComponent.addAssistantMessage('Welcome to a new conversation! How can I help you with parking today?');
            }
        })
        .catch(error => {
            console.error('Error creating new chat:', error);

            // Show error message in chat
            if (window.chatInterfaceComponent) {
                window.chatInterfaceComponent.clearChat();
                window.chatInterfaceComponent.addAssistantMessage('Sorry, there was an error creating a new conversation. Please try again.');
            }
        })
        .finally(() => {
            // Reset new chat button
            const newChatBtn = document.getElementById('newChatSidebarBtn');
            if (newChatBtn) {
                newChatBtn.innerHTML = '<i class="fas fa-plus-circle"></i> New Chat';
                newChatBtn.disabled = false;
            }
        });
    }

    startEditingConversation(conversationItem, conversationId) {
        // Note: conversationId is included in the method signature for consistency
        // even though it's not used in this method

        // Hide title, show input
        const titleElement = conversationItem.querySelector('.conversation-title');
        const titleInput = conversationItem.querySelector('.conversation-title-input');

        titleElement.classList.add('hidden');
        titleInput.classList.remove('hidden');

        // Focus input and select all text
        titleInput.focus();
        titleInput.select();
    }

    finishEditingConversation(conversationItem, conversationId) {
        const titleElement = conversationItem.querySelector('.conversation-title');
        const titleInput = conversationItem.querySelector('.conversation-title-input');
        const newTitle = titleInput.value.trim();

        // Hide input, show title
        titleInput.classList.add('hidden');
        titleElement.classList.remove('hidden');

        // If title is empty, revert to original
        if (!newTitle) {
            const originalTitle = titleElement.textContent;
            titleInput.value = originalTitle;
            return;
        }

        // If title hasn't changed, do nothing
        if (newTitle === titleElement.textContent) {
            return;
        }

        // Update title in UI
        titleElement.textContent = newTitle;
        titleElement.setAttribute('title', newTitle);

        // Update title in backend
        this.renameConversation(conversationId, newTitle);
    }

    renameConversation(conversationId, newName) {
        const userId = localStorage.getItem('userId');
        if (!userId) return;

        // Show loading state
        const conversationItem = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (conversationItem) {
            const titleElement = conversationItem.querySelector('.conversation-title');
            titleElement.innerHTML = `<i class="fas fa-spinner fa-spin fa-xs mr-1"></i> ${newName}`;
        }

        // Call API to rename conversation
        fetch(`${API_BASE_URL}/chat-history/conversations/${conversationId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-User-ID': userId
            },
            body: JSON.stringify({ name: newName })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to rename conversation');
            }
            return response.json();
        })
        .then(() => {
            // Update conversation in local array (we don't need the response data)
            const conversation = this.conversations.find(c => c.conversation_id === conversationId);
            if (conversation) {
                conversation.name = newName;
            }

            // Update UI
            if (conversationItem) {
                const titleElement = conversationItem.querySelector('.conversation-title');
                titleElement.textContent = newName;
            }
        })
        .catch(error => {
            console.error('Error renaming conversation:', error);

            // Revert to original name in UI
            if (conversationItem) {
                const conversation = this.conversations.find(c => c.conversation_id === conversationId);
                if (conversation) {
                    const titleElement = conversationItem.querySelector('.conversation-title');
                    titleElement.textContent = conversation.name;
                }
            }
        });
    }

    deleteConversation(conversationId) {
        if (!confirm('Are you sure you want to delete this conversation?')) {
            return;
        }

        const userId = localStorage.getItem('userId');
        if (!userId) return;

        // Show loading state
        const conversationItem = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (conversationItem) {
            conversationItem.style.opacity = '0.5';
            conversationItem.style.pointerEvents = 'none';
        }

        fetch(`${API_BASE_URL}/chat-history/conversations/${conversationId}`, {
            method: 'DELETE',
            headers: {
                'X-User-ID': userId
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete conversation');
            }

            // Remove from conversations array
            this.conversations = this.conversations.filter(
                conv => conv.conversation_id !== conversationId
            );

            // Re-render conversations
            this.renderConversations();

            // If deleted the active conversation, create a new one
            if (conversationId === this.activeConversationId) {
                if (this.conversations.length > 0) {
                    this.loadConversation(this.conversations[0].conversation_id);
                } else {
                    this.createNewChat();
                }
            }
        })
        .catch(error => {
            console.error('Error deleting conversation:', error);
            alert('Failed to delete conversation. Please try again.');

            // Reset UI
            if (conversationItem) {
                conversationItem.style.opacity = '1';
                conversationItem.style.pointerEvents = 'auto';
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatSidebarComponent = new ChatSidebarComponent();
});
