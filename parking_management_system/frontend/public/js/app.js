// Main application logic
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking user login');

    // Check if user is logged in
    const userId = localStorage.getItem('userId');
    if (!userId) {
        console.log('No user ID found, redirecting to login');
        // Redirect to login page if not logged in
        window.location.href = 'login.html';
        return;
    }

    console.log('User ID found:', userId);

    // Set user display immediately
    updateUserDisplay();

    // Initialize app
    initializeApp(userId);
});

// Function to update user display
function updateUserDisplay() {
    const userId = localStorage.getItem('userId');
    const userName = localStorage.getItem('userName') || 'User';
    const userDisplay = document.getElementById('userDisplay');

    console.log('Updating user display from app.js:', { userDisplay, userName, userId });

    if (userDisplay) {
        // Force display to be visible
        userDisplay.style.display = 'flex';

        // Set content
        userDisplay.innerHTML = `<i class="fas fa-user-circle mr-2 text-xl"></i>${userName} <span class="text-xs opacity-75">(ID: ${userId})</span>`;
        console.log('User display updated successfully from app.js');
    } else {
        console.error('User display element not found in app.js!');
    }

    // Setup logout button
    setupLogoutButton();
}

// Function to setup logout button
function setupLogoutButton() {
    const logoutButton = document.getElementById('logoutButton');
    console.log('Setting up logout button:', logoutButton);

    if (logoutButton) {
        // Remove any existing event listeners
        logoutButton.replaceWith(logoutButton.cloneNode(true));

        // Get the fresh reference
        const freshLogoutButton = document.getElementById('logoutButton');

        // Add event listener
        freshLogoutButton.addEventListener('click', function() {
            console.log('Logout button clicked');
            logout();
        });

        console.log('Logout button setup successfully');
    } else {
        console.error('Logout button not found!');
    }
}

// Initialize the application
function initializeApp(userId) {
    // Initialize components
    initializeComponents();

    // Load user data and existing conversation
    loadUserData(userId);
}

// Initialize all components
function initializeComponents() {
    // Initialize chat interface if not already initialized
    if (!window.chatInterfaceComponent && document.getElementById('chatInterfacePanel')) {
        window.chatInterfaceComponent = new ChatInterfaceComponent();
    }

    // Initialize parking info if not already initialized
    if (!window.parkingInfoComponent && document.getElementById('parkingInfoPanel')) {
        window.parkingInfoComponent = new ParkingInfoComponent();
    }

    // Initialize chat sidebar if not already initialized
    if (!window.chatSidebarComponent && document.getElementById('chatHistorySidebar')) {
        window.chatSidebarComponent = new ChatSidebarComponent();
    }

    // Make sure components are accessible to each other
    console.log('Components initialized:', {
        chatInterface: !!window.chatInterfaceComponent,
        parkingInfo: !!window.parkingInfoComponent,
        chatSidebar: !!window.chatSidebarComponent
    });
}

// Initialize a new chat for the user
function initializeNewChat(userId) {
    console.log('Initializing new chat for user:', userId);

    // Create a new conversation on the backend
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
        console.log('New conversation created:', data.conversation_id);

        // Set the current conversation ID
        window.currentConversationId = data.conversation_id;

        // Store the conversation ID in localStorage
        localStorage.setItem('currentConversationId', data.conversation_id);

        // If chat interface component exists, set its conversation ID
        if (window.chatInterfaceComponent) {
            window.chatInterfaceComponent.currentConversationId = data.conversation_id;
        }

        // If chat sidebar component exists, refresh conversations and set active
        if (window.chatSidebarComponent) {
            window.chatSidebarComponent.activeConversationId = data.conversation_id;
            window.chatSidebarComponent.fetchConversations();
        }
    })
    .catch(error => {
        console.error('Error initializing chat:', error);
    });
}

// Logout function
function logout() {
    console.log('Logout function called');

    // Clear local storage
    localStorage.removeItem('userId');
    localStorage.removeItem('userName');

    // Clear any other user-related data
    localStorage.removeItem('currentConversationId');

    console.log('Local storage cleared, redirecting to login page');

    // Redirect to login page
    window.location.href = 'login.html';
}

// Load user data
function loadUserData(userId) {
    // Load bookings
    if (window.parkingInfoComponent) {
        window.parkingInfoComponent.fetchBookings();
    }

    // Load existing conversation
    const storedConversationId = localStorage.getItem('currentConversationId');
    if (storedConversationId) {
        console.log('Found stored conversation ID:', storedConversationId);
        loadConversationMessages(storedConversationId, userId);
    } else {
        // No stored conversation, create a new one
        loadOrCreateConversation(userId);
    }
}

// Load existing conversation or create a new one
function loadOrCreateConversation(userId) {
    console.log('Loading or creating conversation for user:', userId);

    // Check if we have a stored conversation ID in localStorage
    const storedConversationId = localStorage.getItem('currentConversationId');
    console.log('Stored conversation ID:', storedConversationId);

    // Try to get conversations from the backend
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
        console.log('Loaded conversations:', conversations.length);

        if (conversations && conversations.length > 0) {
            let selectedConversation;

            // If we have a stored conversation ID, try to find it in the list
            if (storedConversationId) {
                selectedConversation = conversations.find(
                    conv => conv.conversation_id === storedConversationId
                );

                if (selectedConversation) {
                    console.log('Found stored conversation:', selectedConversation.conversation_id);
                } else {
                    console.log('Stored conversation not found, using most recent');
                }
            }

            // If no stored conversation or it wasn't found, use the most recent
            if (!selectedConversation) {
                selectedConversation = conversations[0];
                console.log('Using most recent conversation:', selectedConversation.conversation_id);
            }

            // Set the current conversation ID
            window.currentConversationId = selectedConversation.conversation_id;
            localStorage.setItem('currentConversationId', selectedConversation.conversation_id);

            // If chat interface component exists, set its conversation ID
            if (window.chatInterfaceComponent) {
                window.chatInterfaceComponent.currentConversationId = selectedConversation.conversation_id;
            }

            // If chat sidebar component exists, highlight the active conversation
            if (window.chatSidebarComponent) {
                window.chatSidebarComponent.activeConversationId = selectedConversation.conversation_id;
                window.chatSidebarComponent.renderConversations();
            }

            // Load the conversation messages
            if (window.chatSidebarComponent) {
                // Use the sidebar component to load messages (which handles UI updates)
                window.chatSidebarComponent.fetchConversationMessages(selectedConversation.conversation_id);
            } else {
                // Fallback to direct loading if sidebar component isn't available
                loadConversationMessages(selectedConversation.conversation_id, userId);
            }
        } else {
            // No conversations found, create a new one
            console.log('No conversations found, creating new one');
            initializeNewChat(userId);
        }
    })
    .catch(error => {
        console.error('Error loading conversations:', error);
        // If there's an error, create a new conversation
        initializeNewChat(userId);
    });
}

// Load messages for a specific conversation
function loadConversationMessages(conversationId, userId) {
    console.log('Loading messages for conversation:', conversationId);

    // Store the conversation ID in localStorage
    localStorage.setItem('currentConversationId', conversationId);

    // Set the current conversation ID in window and chat interface
    window.currentConversationId = conversationId;
    if (window.chatInterfaceComponent) {
        window.chatInterfaceComponent.currentConversationId = conversationId;
    }

    // Show loading indicator
    if (window.chatInterfaceComponent) {
        window.chatInterfaceComponent.clearChat();
        window.chatInterfaceComponent.addAssistantMessage('<i class="fas fa-spinner fa-spin"></i> Loading conversation...');
    }

    // Use retry mechanism
    loadConversationMessagesWithRetry(conversationId, userId, 3);
}

// Load messages with retry mechanism
function loadConversationMessagesWithRetry(conversationId, userId, retryCount = 3) {
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

        // Only process if this is still the active conversation
        if (window.currentConversationId === conversationId && window.chatInterfaceComponent) {
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
    })
    .catch(error => {
        console.error(`Error loading conversation messages for ${conversationId}:`, error);

        // Retry if we have retries left
        if (retryCount > 0) {
            console.log(`Retrying fetch for conversation ${conversationId}...`);
            setTimeout(() => {
                loadConversationMessagesWithRetry(conversationId, userId, retryCount - 1);
            }, 1000); // Wait 1 second before retrying
            return;
        }

        // Show error message in chat if this is still the active conversation
        if (window.currentConversationId === conversationId && window.chatInterfaceComponent) {
            window.chatInterfaceComponent.clearChat();
            window.chatInterfaceComponent.addAssistantMessage('Sorry, there was an error loading the conversation. Please try again or start a new chat.');
        }
    });
}
