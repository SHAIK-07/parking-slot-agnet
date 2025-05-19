// Chat Interface Component
class ChatInterfaceComponent {
    constructor() {
        this.container = document.getElementById('chatInterfacePanel');
        this.conversations = [];

        // Get conversation ID from localStorage if available
        this.currentConversationId = localStorage.getItem('currentConversationId') || null;

        this.isWaitingForResponse = false;
        this.bookingState = {
            inProgress: false,
            step: null, // 'mall-selection', 'vehicle-selection', 'slot-selection', 'confirmation'
            data: {}
        };

        // Log the current conversation ID
        console.log('ChatInterfaceComponent initialized with conversation ID:', this.currentConversationId);

        this.render();
        this.bindEvents();
    }

    render() {
        this.container.innerHTML = `
            <div class="panel">
                <div class="panel-header">
                    <div class="flex items-center">
                        <h2 class="text-xl font-semibold">Parking Assistant</h2>
                        <button type="button" id="newChatButton" class="ml-4 text-sm bg-blue-100 text-blue-700 px-3 py-1 rounded-md hover:bg-blue-200">
                            <i class="fas fa-plus mr-1"></i> New Chat
                        </button>
                    </div>
                    <div class="flex space-x-2">
                        <button type="button" id="clearChatButton" class="text-sm text-gray-500 hover:text-gray-700">
                            <i class="fas fa-eraser mr-1"></i> Clear Chat
                        </button>
                    </div>
                </div>

                <div id="chatMessages" class="panel-body space-y-4 chat-container">
                    <!-- Messages will be added here -->
                    <div class="assistant-message">
                        <p>Welcome to the Parking Management System! I can help you find and book parking slots at our malls.</p>

                        <div class="example-queries-container">
                            <h4 class="example-queries-title">Example Queries (Format):</h4>
                            <div class="example-query">
                                I need to park my [vehicle type] at [Mall] for 2 hours tomorrow morning
                            </div>

                        </div>


                    </div>
                </div>

                <form id="chatForm" class="panel-footer">
                    <div class="relative">
                        <textarea
                            id="messageInput"
                            class="w-full px-4 py-3 border border-gray-300 rounded-md pr-12 resize-none"
                            placeholder="Type your message here..."
                            rows="2"
                            style="min-height: 60px; max-height: 150px;"
                        ></textarea>
                        <button
                            type="submit"
                            class="absolute right-2 bottom-2 p-2 bg-blue-600 text-white rounded-md flex items-center justify-center hover:bg-blue-700"
                        >
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                    <div class="text-xs text-gray-500 mt-2 text-center">
                        Press Enter to send, Shift+Enter for new line
                    </div>
                </form>
            </div>
        `;
    }

    bindEvents() {
        document.getElementById('chatForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        document.getElementById('clearChatButton').addEventListener('click', () => {
            this.clearChat();
        });

        document.getElementById('newChatButton').addEventListener('click', () => {
            this.createNewChat();
        });

        // Handle textarea Enter key
        const messageInput = document.getElementById('messageInput');
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        messageInput.addEventListener('input', () => {
            messageInput.style.height = 'auto';
            messageInput.style.height = (messageInput.scrollHeight > 150 ? 150 : messageInput.scrollHeight) + 'px';
        });
    }

    createNewChat() {
        // Clear current chat
        this.clearChat();

        // Add welcome message with example queries
        const welcomeMessage = `
            <p>Welcome to the Parking Management System! I can help you find and book parking slots at our malls.</p>

            <div class="example-queries-container">
                <h4 class="example-queries-title">Example Queries (Format):</h4>
                <div class="example-query">
                    I need to park my [vehicle type] at [Mall] for 2 hours tomorrow morning
                </div>
                <div class="example-query">
                    Book a [vehicle type] parking slot at [Mall] for 3 hours today afternoon
                </div>
                <div class="example-query">
                    I want to reserve a [vehicle type] parking at [Mall] for 1 hour on May 25 at 3PM
                </div>
            </div>

            <p class="mt-4">You can also use the navigation bar to:</p>
            <ul class="list-disc pl-5 space-y-1 mt-2">
                <li><a href="info.html" class="text-blue-600 hover:underline">Info</a> - Learn about our parking system</li>
                <li><a href="available-slots.html" class="text-blue-600 hover:underline">Available Slots</a> - Find and book slots manually</li>
                <li><a href="bookings.html" class="text-blue-600 hover:underline">Bookings</a> - View and manage your bookings</li>
            </ul>
        `;
        this.addAssistantMessage(welcomeMessage, 'html');

        // If chat sidebar component exists, use it to create a new chat
        if (window.chatSidebarComponent) {
            window.chatSidebarComponent.createNewChat();
            return;
        }

        // Otherwise, create new conversation directly
        // Create new conversation ID
        this.currentConversationId = null;
        window.currentConversationId = null;

        // Create new chat on backend
        const userId = localStorage.getItem('userId');
        if (!userId) return;

        // Show loading indicator
        this.addAssistantMessage('<i class="fas fa-spinner fa-spin"></i> Creating new conversation...');

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
            // Remove loading indicator
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages.lastChild && chatMessages.lastChild.innerHTML.includes('fa-spinner')) {
                chatMessages.removeChild(chatMessages.lastChild);
            }

            // Set conversation ID
            this.currentConversationId = data.conversation_id;
            window.currentConversationId = data.conversation_id;

            // Store the conversation ID in localStorage
            localStorage.setItem('currentConversationId', data.conversation_id);
            console.log('Stored new conversation ID in localStorage:', data.conversation_id);
        })
        .catch(error => {
            console.error('Error creating new chat:', error);

            // Remove loading indicator
            const chatMessages = document.getElementById('chatMessages');
            if (chatMessages.lastChild && chatMessages.lastChild.innerHTML.includes('fa-spinner')) {
                chatMessages.removeChild(chatMessages.lastChild);
            }

            // Show error message
            this.addAssistantMessage('Sorry, there was an error creating a new conversation. Please try again.');
        });
    }

    sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        const sendButton = document.querySelector('#chatForm button[type="submit"]');

        // Don't allow sending if already waiting for a response
        if (this.isWaitingForResponse) {
            return;
        }

        if (message) {
            // Disable input and button while waiting
            this.isWaitingForResponse = true;
            messageInput.disabled = true;
            sendButton.disabled = true;
            sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

            this.addUserMessage(message);
            messageInput.value = '';
            messageInput.style.height = 'auto';

            // Send to backend and get response
            this.sendToBackend(message);
        }
    }

    addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'user-message';
        messageElement.innerHTML = `<p>${this.formatMessage(message)}</p>`;

        document.getElementById('chatMessages').appendChild(messageElement);
        this.scrollToBottom();
    }

    addAssistantMessage(message, type = 'normal') {
        const messageElement = document.createElement('div');
        messageElement.className = 'assistant-message';

        // Check for special refresh-bookings tag
        const hasRefreshBookingsTag = message.includes('<refresh-bookings></refresh-bookings>');

        // Remove the tag from the displayed message
        let processedMessage = message;
        if (hasRefreshBookingsTag) {
            processedMessage = processedMessage.replace('<refresh-bookings></refresh-bookings>', '');
        }

        if (type === 'typing') {
            // For typing indicator, use the raw HTML
            messageElement.innerHTML = `<p>${processedMessage}</p>`;
            messageElement.classList.add('typing');
        } else if (type === 'html') {
            // For HTML content, use it directly
            messageElement.innerHTML = processedMessage;
        } else {
            // For normal messages, format the content
            messageElement.innerHTML = `<p>${this.formatMessage(processedMessage)}</p>`;
        }

        document.getElementById('chatMessages').appendChild(messageElement);
        this.scrollToBottom();

        // If the message contained the refresh-bookings tag, suggest navigating to bookings page
        if (hasRefreshBookingsTag) {
            console.log('Detected refresh-bookings tag, suggesting bookings page');
            setTimeout(() => {
                this.addAssistantMessage(
                    'You can view your bookings on the <a href="bookings.html" class="text-blue-600 hover:underline">Bookings</a> page.',
                    'html'
                );
            }, 500); // Small delay to ensure the message is displayed first
        }
    }

    removeTypingIndicator() {
        const chatMessages = document.getElementById('chatMessages');
        const typingIndicators = chatMessages.querySelectorAll('.assistant-message.typing');

        typingIndicators.forEach(indicator => {
            chatMessages.removeChild(indicator);
        });
    }

    resetUIState() {
        // Re-enable input and button
        this.isWaitingForResponse = false;
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.querySelector('#chatForm button[type="submit"]');

        if (messageInput) {
            messageInput.disabled = false;
            messageInput.focus();
        }

        if (sendButton) {
            sendButton.disabled = false;
            sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }

    formatMessage(message) {
        // Convert markdown-like syntax to HTML
        let formattedMessage = message;

        // Handle slot listings with special formatting - only process once
        const slotPatterns = [
            'Slot ID:', 'slot id:',
            'Available car slots:', 'Available bike slots:', 'Available truck slots:',
            'Available slots:'
        ];

        let hasSlotListing = false;
        for (const pattern of slotPatterns) {
            if (formattedMessage.includes(pattern)) {
                hasSlotListing = true;
                break;
            }
        }

        if (hasSlotListing) {
            formattedMessage = this.formatSlotListing(formattedMessage);
        }

        // Handle booking details with special formatting
        if (formattedMessage.includes('Booking Details:') || formattedMessage.includes('booking details:')) {
            formattedMessage = this.formatBookingDetails(formattedMessage);
        }

        // Replace * bullet points with HTML list items
        formattedMessage = formattedMessage.replace(/\n\s*\*\s+([^\n]+)/g, '<li>$1</li>');

        // Wrap consecutive list items in <ul> tags
        formattedMessage = formattedMessage.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');

        // Replace numbered lists
        formattedMessage = formattedMessage.replace(/\n\s*(\d+)\.\s+([^\n]+)/g, '<li>$2</li>');

        // Wrap consecutive numbered list items in <ol> tags
        formattedMessage = formattedMessage.replace(/(<li>.*?<\/li>)+/g, '<ol>$&</ol>');

        // Replace newlines with <br> tags
        formattedMessage = formattedMessage.replace(/\n/g, '<br>');

        // Highlight important information
        formattedMessage = formattedMessage.replace(/(Mall:|Slot:|Type:|Number:|Rate:|Vehicle Type:|Amount:|Status:)/g,
            '<strong class="text-blue-600">$1</strong>');

        return formattedMessage;
    }

    formatSlotListing(message) {
        // Skip processing if the message contains "No available slots" but also has slot IDs
        // This will be handled by the cleanupResponse method
        if (message.includes('No available slots found') && message.includes('Slot ID:')) {
            console.log('Skipping formatSlotListing for contradictory response - will be handled by cleanupResponse');
            return message;
        }

        // Extract slot listings and format them as a simple list
        const lines = message.split('\n');
        let formattedMessage = '';
        let inSlotListing = false;
        let slotsList = '';
        let slotIds = new Set(); // Use a Set to avoid duplicates
        let validSlotFound = false;
        let currentMall = '';
        let processingComplete = false;
        let hasNoSlotsMessage = false;

        // First pass: collect all slot IDs and other information
        for (const line of lines) {
            // Check if this line contains "No available slots" message
            if (line.includes('No available slots found')) {
                hasNoSlotsMessage = true;
            }

            // Check for mall information
            const mallMatch = line.match(/Mall:\s*([^,\.]+)/i) || line.match(/at\s+([^,\.]+)\s+Mall/i);
            if (mallMatch && !inSlotListing) {
                currentMall = mallMatch[1].trim();
            }

            // Check for slot information
            if ((line.includes('Slot ID:') || line.includes('slot id:') ||
                (line.toLowerCase().includes('slot') && line.match(/\d+/)) ||
                line.toLowerCase().includes('available') && line.toLowerCase().includes('slots')) &&
                !line.toLowerCase().includes('book slot') &&
                !processingComplete) {

                if (!inSlotListing) {
                    inSlotListing = true;
                }

                // Extract slot information
                const slotInfo = this.extractSlotInfo(line);

                // Only add valid slot IDs (numeric)
                if (slotInfo.id && slotInfo.id !== '?' && !isNaN(parseInt(slotInfo.id))) {
                    slotIds.add(slotInfo.id); // Add to Set to avoid duplicates
                    validSlotFound = true;
                }
            }
            // Check for end of slot listing section
            else if (inSlotListing &&
                    (line.trim() === '' ||
                     line.toLowerCase().includes('please respond') ||
                     line.toLowerCase().includes('to book a slot') ||
                     line.toLowerCase().includes('you can say') ||
                     line.toLowerCase().includes('book slot'))) {

                // Mark that we've processed the slot listing
                processingComplete = true;
            }
        }

        // If we found "No available slots" message but also found valid slots,
        // this is a contradictory response - ignore the "No available slots" message
        const isContradictory = hasNoSlotsMessage && validSlotFound;

        // Second pass: rebuild the message with formatted slot listing
        inSlotListing = false;
        processingComplete = false;

        for (const line of lines) {
            // Skip "No available slots" lines if we found valid slots
            if (isContradictory && line.includes('No available slots found')) {
                continue;
            }

            // Check for start of slot listing
            if ((line.includes('Slot ID:') || line.includes('slot id:') ||
                (line.toLowerCase().includes('slot') && line.match(/\d+/)) ||
                line.toLowerCase().includes('available') && line.toLowerCase().includes('slots')) &&
                !line.toLowerCase().includes('book slot') &&
                !processingComplete) {

                if (!inSlotListing) {
                    inSlotListing = true;

                    // Add the header text before the slot listing
                    formattedMessage += 'Available slots';
                    if (currentMall) {
                        formattedMessage += ` at ${currentMall}`;
                    }
                    formattedMessage += ':\n';

                    // Create the formatted slot listing (only once)
                    slotsList = '<div class="available-slots-list">';

                    // Create a simple list of available slots
                    if (slotIds.size > 0) {
                        slotsList += '<p class="mb-2"><strong>Available Slot IDs:</strong></p>';
                        slotsList += '<div class="slot-ids-container">';

                        // Convert Set to Array and sort numerically
                        Array.from(slotIds).sort((a, b) => parseInt(a) - parseInt(b)).forEach(id => {
                            slotsList += `
                                <button class="slot-id-btn" onclick="window.chatInterfaceComponent.bookSlot(${id})">
                                    Slot ${id}
                                </button>
                            `;
                        });

                        slotsList += '</div>';
                    } else if (validSlotFound) {
                        slotsList += '<p>Error retrieving slot information. Please try again.</p>';
                    } else {
                        slotsList += '<p>No available slots found for your criteria.</p>';
                    }

                    slotsList += '</div>';
                    formattedMessage += slotsList;

                    // Add booking instructions
                    formattedMessage += '\nTo book a slot, please use the format: "Book slot [SLOT_ID]"\n';
                    if (slotIds.size > 0) {
                        formattedMessage += 'For example: "Book slot ' + Array.from(slotIds)[0] + '"\n\n';
                    }
                    formattedMessage += 'Or you can say "yes" or "confirm" to book an available slot automatically.\n';

                    // Mark that we've processed the slot listing
                    processingComplete = true;
                }
            }
            // Skip lines that are part of the slot listing or booking instructions
            else if (!processingComplete &&
                    (line.toLowerCase().includes('slot') ||
                     line.toLowerCase().includes('available') ||
                     line.toLowerCase().includes('to book') ||
                     line.toLowerCase().includes('you can say'))) {
                // Skip these lines as we've already formatted them
                continue;
            }
            // Include all other lines
            else if (processingComplete || !inSlotListing) {
                formattedMessage += line + '\n';
            }
        }

        return formattedMessage;
    }

    extractSlotInfo(line) {
        // Extract slot information from a line
        let idMatch = line.match(/Slot ID:\s*(\d+)/i) || line.match(/slot id:\s*(\d+)/i);

        // Try to extract slot ID from other formats
        if (!idMatch) {
            // Look for "Slot X" pattern
            const slotNumberMatch = line.match(/Slot\s+(\d+)/i);
            if (slotNumberMatch) {
                idMatch = slotNumberMatch;
            }
        }

        const mallMatch = line.match(/Mall:\s*([^,]+)/i) || line.match(/mall:\s*([^,]+)/i);
        const typeMatch = line.match(/Type:\s*([^,]+)/i) || line.match(/type:\s*([^,]+)/i);
        const numberMatch = line.match(/Number:\s*([^,]+)/i) || line.match(/number:\s*([^,]+)/i);
        const rateMatch = line.match(/Rate:\s*₹(\d+)/i) || line.match(/rate:\s*₹(\d+)/i) || line.match(/Rate:\s*(\d+)/i) || line.match(/rate:\s*(\d+)/i);

        return {
            id: idMatch ? idMatch[1] : '?',
            mall: mallMatch ? mallMatch[1].trim() : 'Unknown Mall',
            type: typeMatch ? typeMatch[1].trim() : 'Unknown',
            number: numberMatch ? numberMatch[1].trim() : '?',
            rate: rateMatch ? rateMatch[1] : '?'
        };
    }

    formatBookingDetails(message) {
        // Format booking details section
        const lines = message.split('\n');
        let formattedMessage = '';
        let inBookingDetails = false;
        let bookingCard = '';

        for (const line of lines) {
            if (line.includes('Booking Details:') || line.includes('booking details:')) {
                inBookingDetails = true;
                bookingCard = '<div class="booking-details-card">';
                bookingCard += `<h3 class="booking-details-title">${line.trim()}</h3><div class="booking-details-content">`;
                continue;
            }

            if (inBookingDetails) {
                if (line.trim() === '' || !line.includes('*')) {
                    inBookingDetails = false;
                    bookingCard += '</div></div>';
                    formattedMessage += bookingCard + '\n' + line;
                } else {
                    // Format each detail line
                    const cleanLine = line.replace(/^\s*\*\s*/, '').trim();
                    const parts = cleanLine.split(':');

                    if (parts.length >= 2) {
                        const label = parts[0].trim();
                        const value = parts.slice(1).join(':').trim();

                        bookingCard += `
                            <div class="booking-detail-item">
                                <span class="booking-detail-label">${label}:</span>
                                <span class="booking-detail-value">${value}</span>
                            </div>
                        `;
                    } else {
                        bookingCard += `<div>${cleanLine}</div>`;
                    }
                }
            } else {
                formattedMessage += line + '\n';
            }
        }

        if (inBookingDetails) {
            bookingCard += '</div></div>';
            formattedMessage += bookingCard;
        }

        return formattedMessage;
    }

    bookSlot(slotId) {
        // Helper method to book a slot directly from the UI
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            // Validate slot ID
            if (slotId && slotId !== '?' && !isNaN(parseInt(slotId))) {
                // Store the slot ID in the booking state
                this.bookingState.data.slotId = slotId;
                this.bookingState.step = 'confirmation';

                // First, check if the backend is available
                this.checkBackendAvailability()
                    .then(isAvailable => {
                        if (isAvailable) {
                            // Send the booking command
                            messageInput.value = `Book slot ${slotId}`;
                            this.sendMessage();

                            // Add a confirmation message to help the agent understand the context
                            setTimeout(() => {
                                // Only add if the previous message was sent successfully
                                if (!this.isWaitingForResponse) {
                                    this.addAssistantMessage('Processing your booking request for Slot ' + slotId + '...', 'typing');
                                }
                            }, 500);
                        } else {
                            // If backend is not available, use the direct booking method
                            this.directBookSlot(slotId);
                        }
                    })
                    .catch(() => {
                        // If check fails, use the direct booking method
                        this.directBookSlot(slotId);
                    });
            } else {
                // If slot ID is invalid, just send a general booking confirmation
                messageInput.value = `Confirm booking`;
                this.sendMessage();
            }
        }
    }

    checkBackendAvailability() {
        return new Promise((resolve) => {
            // Try to ping the backend with a simple request
            fetch(`${API_BASE_URL}/health-check`, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' },
                // Set a short timeout
                signal: AbortSignal.timeout(2000)
            })
            .then(response => {
                if (response.ok) {
                    resolve(true);
                    return null; // Return null to avoid chaining to the next then
                } else {
                    // Try the root endpoint as a fallback
                    return fetch(`${API_BASE_URL}/`, {
                        method: 'GET',
                        headers: { 'Content-Type': 'application/json' },
                        signal: AbortSignal.timeout(2000)
                    });
                }
            })
            .then(response => {
                // Only process if we got a response from the fallback
                if (response) {
                    resolve(response.ok);
                }
                // If response is null, we already resolved in the first then
            })
            .catch(() => {
                // If there's any error, assume backend is not available
                resolve(false);
            });
        });
    }

    tryDirectBookingEndpoint(slotId) {
        return new Promise((resolve) => {
            // Get current user ID and name
            const userId = localStorage.getItem('userId');
            const userName = localStorage.getItem('userName');
            if (!userId) {
                resolve(false);
                return;
            }

            // Get booking details from parkingInfoComponent if available
            let startTime, endTime, duration;

            if (window.parkingInfoComponent && window.parkingInfoComponent.availableSlotsFilter) {
                const filter = window.parkingInfoComponent.availableSlotsFilter;

                if (filter.date && filter.time && filter.duration) {
                    // Create start date/time
                    const startDateTime = new Date(filter.date + 'T' + filter.time);
                    startTime = startDateTime.toISOString();

                    // Calculate end date/time
                    const endDateTime = new Date(startDateTime);
                    endDateTime.setHours(endDateTime.getHours() + parseInt(filter.duration));
                    endTime = endDateTime.toISOString();

                    duration = filter.duration;
                }
            }

            // Build query parameters
            const params = new URLSearchParams();
            params.append('slot_id', slotId);

            // Add date/time parameters if available
            if (startTime && endTime && duration) {
                params.append('start_time', startTime);
                params.append('end_time', endTime);
                params.append('duration', duration);
            }

            // Try to book directly with the bookings endpoint
            fetch(`${API_BASE_URL}/bookings?${params.toString()}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-ID': userId,
                    'X-User-Name': userName || ''
                },
                // Set a short timeout
                signal: AbortSignal.timeout(3000)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to book slot');
                }
                return response.json();
            })
            .then(data => {
                // Remove any typing indicators
                this.removeTypingIndicator();

                // Add a success message
                this.addAssistantMessage(`
                    <div class="direct-booking-message">
                        <p><i class="fas fa-check-circle text-green-500 mr-2"></i> <strong>Booking Confirmed!</strong></p>
                        <p class="mt-2">Your booking for Slot ${data.slot_number} at ${data.mall_name} has been confirmed.</p>
                        <p class="mt-1">Start time: ${new Date(data.start_time).toLocaleString()}</p>
                        <p class="mt-1">End time: ${new Date(data.end_time).toLocaleString()}</p>
                        <p class="mt-1">Total amount: ₹${data.total_amount}</p>
                    </div>
                `);

                // Update the booking state
                this.bookingState = {
                    inProgress: false,
                    step: null,
                    data: {}
                };

                // Refresh the bookings tab
                if (window.parkingInfoComponent) {
                    window.parkingInfoComponent.fetchBookings();
                    window.parkingInfoComponent.setActiveTab('bookings');
                }

                // Reset UI state
                this.resetUIState();

                resolve(true);
            })
            .catch(error => {
                console.error('Error in direct booking endpoint:', error);
                resolve(false);
            });
        });
    }

    directBookSlot(slotId) {
        // This is a fallback method to book a slot directly without using the backend
        // Get current user ID
        const userId = localStorage.getItem('userId');
        if (!userId) {
            this.addAssistantMessage('Please log in to book a slot');
            return;
        }

        // Remove any typing indicators
        this.removeTypingIndicator();

        // Get booking details from parkingInfoComponent if available
        let startTime, endTime, duration, mallName, vehicleType;
        const now = new Date();
        const twoHoursLater = new Date(now);
        twoHoursLater.setHours(twoHoursLater.getHours() + 2);

        if (window.parkingInfoComponent && window.parkingInfoComponent.availableSlotsFilter) {
            const filter = window.parkingInfoComponent.availableSlotsFilter;

            if (filter.date && filter.time && filter.duration) {
                // Create start date/time
                const startDateTime = new Date(filter.date + 'T' + filter.time);
                startTime = startDateTime;

                // Calculate end date/time
                const endDateTime = new Date(startDateTime);
                endDateTime.setHours(endDateTime.getHours() + parseInt(filter.duration));
                endTime = endDateTime;

                duration = filter.duration;
                vehicleType = filter.vehicleType || 'car';

                // Try to get mall name
                const slot = window.parkingInfoComponent.findSlotById ?
                    window.parkingInfoComponent.findSlotById(slotId) : null;
                mallName = slot ? slot.mall_name : 'the selected mall';
            }
        }

        // Use defaults if not available
        if (!startTime) startTime = now;
        if (!endTime) endTime = twoHoursLater;
        if (!duration) duration = 2;
        if (!mallName) mallName = 'the selected mall';
        if (!vehicleType) vehicleType = 'car';

        // Add a success message with booking details
        this.addAssistantMessage(`
            <div class="direct-booking-message">
                <p><i class="fas fa-check-circle text-green-500 mr-2"></i> <strong>Booking Confirmed!</strong></p>
                <p class="mt-2">Your booking for Slot ${slotId} at ${mallName} has been confirmed.</p>
                <p class="mt-1"><strong>Vehicle Type:</strong> ${vehicleType}</p>
                <p class="mt-1"><strong>Start:</strong> ${startTime.toLocaleString()}</p>
                <p class="mt-1"><strong>End:</strong> ${endTime.toLocaleString()}</p>
                <p class="mt-1"><strong>Duration:</strong> ${duration} hour(s)</p>
                <p class="text-sm text-gray-600 mt-2">Note: This is a simulated booking as the backend server appears to be offline.</p>
            </div>
        `);

        // Update the booking state
        this.bookingState = {
            inProgress: false,
            step: null,
            data: {}
        };

        // Reset UI state
        this.resetUIState();
    }

    useExampleQuery(element) {
        // Helper method to use an example query
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.value = element.textContent.trim();
            messageInput.focus();

            // Scroll the textarea into view
            messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Optional: Auto-send after a short delay
            setTimeout(() => {
                this.sendMessage();
            }, 500);
        }
    }

    showBookingConfirmationPopup(message) {
        // Extract booking details from the message
        const bookingDetails = this.extractBookingDetails(message);

        // Create popup element
        const popup = document.createElement('div');
        popup.className = 'booking-confirmation-popup';
        popup.innerHTML = `
            <div class="booking-confirmation-content">
                <div class="booking-confirmation-header">
                    <h3><i class="fas fa-check-circle"></i> Booking Confirmed!</h3>
                    <button class="close-popup"><i class="fas fa-times"></i></button>
                </div>
                <div class="booking-confirmation-body">
                    <p>Your parking slot has been successfully booked.</p>
                    <div class="booking-details">
                        <div class="booking-detail">
                            <span class="detail-label">Mall:</span>
                            <span class="detail-value">${bookingDetails.mall || 'N/A'}</span>
                        </div>
                        <div class="booking-detail">
                            <span class="detail-label">Slot:</span>
                            <span class="detail-value">${bookingDetails.slot || 'N/A'}</span>
                        </div>
                        <div class="booking-detail">
                            <span class="detail-label">Vehicle Type:</span>
                            <span class="detail-value">${bookingDetails.vehicleType || 'N/A'}</span>
                        </div>
                        <div class="booking-detail">
                            <span class="detail-label">Amount:</span>
                            <span class="detail-value">${bookingDetails.amount || 'N/A'}</span>
                        </div>
                        <div class="booking-detail">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value status-${bookingDetails.status?.toLowerCase() || 'confirmed'}">${bookingDetails.status || 'Confirmed'}</span>
                        </div>
                    </div>
                </div>
                <div class="booking-confirmation-footer">
                    <button class="view-bookings-btn">View All Bookings</button>
                </div>
            </div>
        `;

        // Add popup to the body
        document.body.appendChild(popup);

        // Add event listeners
        popup.querySelector('.close-popup').addEventListener('click', () => {
            document.body.removeChild(popup);
        });

        popup.querySelector('.view-bookings-btn').addEventListener('click', () => {
            // Switch to bookings tab
            if (window.parkingInfoComponent) {
                window.parkingInfoComponent.setActiveTab('bookings');
            }
            document.body.removeChild(popup);
        });

        // Auto-close after 10 seconds
        setTimeout(() => {
            if (document.body.contains(popup)) {
                document.body.removeChild(popup);
            }
        }, 10000);
    }

    extractBookingDetails(message) {
        console.log('Extracting booking details from message:', message);

        const details = {
            mall: null,
            slot: null,
            vehicleType: null,
            amount: null,
            status: 'Confirmed'
        };

        // Extract mall - try different formats
        let mallMatch = message.match(/Mall:\s*([^\n*]+)/);
        if (!mallMatch) mallMatch = message.match(/\*\*Mall\*\*:\s*([^\n]+)/);
        if (mallMatch) details.mall = mallMatch[1].trim();

        // Extract slot - try different formats
        let slotMatch = message.match(/Slot:\s*([^\n*]+)/);
        if (!slotMatch) slotMatch = message.match(/Slot ID:\s*([^\n*]+)/);
        if (!slotMatch) slotMatch = message.match(/\*\*Slot ID\*\*:\s*([^\n]+)/);
        if (!slotMatch) slotMatch = message.match(/Slot number:\s*([^\n*]+)/);
        if (!slotMatch) slotMatch = message.match(/\*\*Slot number\*\*:\s*([^\n]+)/);
        if (slotMatch) details.slot = slotMatch[1].trim();

        // Extract vehicle type - try different formats
        let vehicleMatch = message.match(/Vehicle Type:\s*([^\n*]+)/);
        if (!vehicleMatch) vehicleMatch = message.match(/\*\*Vehicle type\*\*:\s*([^\n]+)/);
        if (vehicleMatch) details.vehicleType = vehicleMatch[1].trim();

        // Extract amount/rate - try different formats
        let amountMatch = message.match(/Amount:\s*([^\n*]+)/);
        if (!amountMatch) amountMatch = message.match(/Rate:\s*([^\n*]+)/);
        if (!amountMatch) amountMatch = message.match(/\*\*Rate\*\*:\s*([^\n]+)/);
        if (amountMatch) details.amount = amountMatch[1].trim();

        // Extract status - try different formats
        let statusMatch = message.match(/Status:\s*([^\n*]+)/);
        if (statusMatch) details.status = statusMatch[1].trim();

        // If booking is confirmed, set status
        if (message.toLowerCase().includes('booking is confirmed') ||
            message.toLowerCase().includes('booking confirmed') ||
            message.toLowerCase().includes('your booking has been confirmed')) {
            details.status = 'Confirmed';
        }

        console.log('Extracted booking details:', details);
        return details;
    }

    scrollToBottom() {
        const chatContainer = document.getElementById('chatMessages');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    clearChat(keepWelcome = false) {
        const chatMessages = document.getElementById('chatMessages');

        if (keepWelcome) {
            // Keep only the welcome message
            while (chatMessages.children.length > 1) {
                chatMessages.removeChild(chatMessages.lastChild);
            }
        } else {
            // Clear all messages
            chatMessages.innerHTML = '';
        }
    }

    sendToBackend(message) {
        // Get current user ID
        const userId = localStorage.getItem('userId');
        if (!userId) {
            this.resetUIState();
            this.addAssistantMessage('You need to be logged in to use the chat. Please refresh the page and log in again.');
            return;
        }

        // Show typing indicator
        this.addAssistantMessage('<div class="typing-indicator"><span></span><span></span><span></span></div>', 'typing');

        // Analyze message for booking intent
        this.analyzeMessageIntent(message);

        // Check if this is a booking command
        const isBookingCommand = message.toLowerCase().includes('book slot');
        const slotMatch = message.match(/slot\s+(\d+)/i);
        const slotId = slotMatch ? slotMatch[1] : null;

        // First check if backend is available
        this.checkBackendAvailability()
            .then(isAvailable => {
                if (isAvailable) {
                    // Get username if available
                    const userName = localStorage.getItem('userName');

                    // Get conversation ID from this component, window, or localStorage
                    const conversationId = this.currentConversationId ||
                                          window.currentConversationId ||
                                          localStorage.getItem('currentConversationId') ||
                                          null;

                    console.log('Sending message with conversation ID:', conversationId);

                    // Send to backend
                    return fetch(`${API_BASE_URL}/chat`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-User-ID': userId,
                            'X-User-Name': userName || ''
                        },
                        body: JSON.stringify({
                            query: message,
                            conversation_id: conversationId
                        })
                    }).then(response => {
                        // Get the conversation ID from the response headers if available
                        const responseConversationId = response.headers.get('X-Conversation-ID');

                        // Use the response conversation ID, or fall back to the one we sent
                        const finalConversationId = responseConversationId || conversationId;

                        if (finalConversationId) {
                            // Update all conversation ID references
                            this.currentConversationId = finalConversationId;
                            window.currentConversationId = finalConversationId;
                            localStorage.setItem('currentConversationId', finalConversationId);
                            console.log('Updated conversation ID:', finalConversationId);
                        }

                        return response;
                    });
                } else {
                    // If backend is not available and this is a booking command, handle it directly
                    if (isBookingCommand && slotId) {
                        this.removeTypingIndicator();
                        this.directBookSlot(slotId);
                        throw new Error('HANDLED_LOCALLY');
                    } else {
                        // For other commands, use a simulated response
                        this.removeTypingIndicator();
                        this.handleOfflineResponse(message);
                        throw new Error('HANDLED_LOCALLY');
                    }
                }
            })
            .then(response => {
                if (!response || !response.ok) {
                    throw new Error(`HTTP error! Status: ${response?.status}, Text: ${response?.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                // Remove typing indicator
                this.removeTypingIndicator();

                // Clean up and add response
                const cleanedResponse = this.cleanupResponse(data.response);
                this.addAssistantMessage(cleanedResponse);

                // Process response for booking state
                this.processResponseForBookingState(cleanedResponse);

                // Check if this is a booking confirmation
                const responseText = cleanedResponse.toLowerCase();
                if (responseText.includes('booking has been confirmed') ||
                    responseText.includes('booking details') ||
                    responseText.includes('your booking has been added') ||
                    responseText.includes('booking is confirmed') ||
                    responseText.includes('your booking is confirmed')) {

                    console.log('Booking confirmation detected in response');

                    // Reset booking state
                    this.bookingState = {
                        inProgress: false,
                        step: null,
                        data: {}
                    };

                    // Refresh the bookings tab
                    if (window.parkingInfoComponent) {
                        console.log('Refreshing bookings tab');
                        window.parkingInfoComponent.fetchBookings();

                        // Switch to the bookings tab
                        window.parkingInfoComponent.setActiveTab('bookings');
                    }

                    // Show booking confirmation popup
                    console.log('Showing booking confirmation popup');
                    this.showBookingConfirmationPopup(cleanedResponse);
                }

                // Reset UI state
                this.resetUIState();
            })
            .catch(error => {
                console.error('Error sending message:', error);

                // If already handled locally, do nothing
                if (error.message === 'HANDLED_LOCALLY') {
                    return;
                }

                // Remove typing indicator
                this.removeTypingIndicator();

                // Check if this is a booking command
                if (isBookingCommand && slotId) {
                    // Try to book directly with the bookings endpoint
                    this.tryDirectBookingEndpoint(slotId)
                        .then(success => {
                            if (!success) {
                                // If direct booking API fails, use the fallback method
                                this.directBookSlot(slotId);
                            }
                        })
                        .catch(() => {
                            // If there's an error, use the fallback method
                            this.directBookSlot(slotId);
                        });
                } else {
                    // Add error message with more details
                    this.addAssistantMessage(`
                        <div class="error-message">
                            <p><i class="fas fa-exclamation-circle text-red-500 mr-2"></i> <strong>Connection Error</strong></p>
                            <p class="mt-2">Sorry, I couldn't connect to the server. This could be because:</p>
                            <ul class="list-disc ml-5 mt-1">
                                <li>The server is not running</li>
                                <li>There's a network issue</li>
                                <li>The server is temporarily unavailable</li>
                            </ul>
                            <p class="mt-2">You can still use the basic features of the application in offline mode.</p>
                        </div>
                    `);
                }

                // Reset UI state
                this.resetUIState();
            });
    }
    analyzeMessageIntent(message) {
        // Analyze the message to detect booking intent
        const lowerMessage = message.toLowerCase();

        // Check for direct booking confirmation
        if (lowerMessage.match(/^(yes|confirm|book it|proceed|ok|sure)$/i) ||
            lowerMessage.includes('confirm booking')) {

            // If we're in the confirmation step or have a slot ID, this is a confirmation
            if (this.bookingState.step === 'confirmation' || this.bookingState.data.slotId) {
                console.log('Booking confirmation detected');
                return;
            }
        }

        // Check for slot booking command
        if (lowerMessage.includes('book slot') || lowerMessage.includes('reserve slot')) {
            this.bookingState.inProgress = true;

            // Extract slot ID
            const slotMatch = lowerMessage.match(/slot\s+(\d+)/i);
            if (slotMatch && slotMatch[1]) {
                this.bookingState.data.slotId = slotMatch[1];
                this.bookingState.step = 'confirmation';
                console.log('Slot booking detected for slot:', this.bookingState.data.slotId);
            }
            return;
        }

        // Check for "yes" or "book slot X" in any format
        if (lowerMessage === 'yes' ||
            lowerMessage.match(/^book\s+slot\s+\d+$/i) ||
            lowerMessage.match(/^yes\s+book\s+slot\s+\d+$/i)) {

            this.bookingState.inProgress = true;

            // Extract slot ID if present
            const slotMatch = lowerMessage.match(/slot\s+(\d+)/i);
            if (slotMatch && slotMatch[1]) {
                this.bookingState.data.slotId = slotMatch[1];
                this.bookingState.step = 'confirmation';
                console.log('Slot booking detected from yes/book command for slot:', this.bookingState.data.slotId);
            }
            return;
        }

        // Check for general booking intent
        if (lowerMessage.includes('book') || lowerMessage.includes('reserve') || lowerMessage.includes('parking')) {
            this.bookingState.inProgress = true;

            // Check for mall mentions
            if (lowerMessage.includes('mall') || lowerMessage.includes('phoenix') ||
                lowerMessage.includes('palladium') || lowerMessage.includes('orion')) {

                const mallName = this.extractMallName(lowerMessage);
                if (mallName) {
                    this.bookingState.data.mall = mallName;
                    console.log('Mall detected:', this.bookingState.data.mall);

                    // If we have a mall but no step yet, set to vehicle selection
                    if (!this.bookingState.step) {
                        this.bookingState.step = 'vehicle-selection';
                    }
                }
            }

            // Check for vehicle type mentions
            if (lowerMessage.includes('car') || lowerMessage.includes('bike') || lowerMessage.includes('truck')) {
                this.bookingState.data.vehicleType = this.extractVehicleType(lowerMessage);
                console.log('Vehicle type detected:', this.bookingState.data.vehicleType);

                // If we have a vehicle type but no step or we're at vehicle selection, move to slot selection
                if (this.bookingState.data.vehicleType &&
                    (!this.bookingState.step || this.bookingState.step === 'vehicle-selection')) {
                    this.bookingState.step = 'slot-selection';
                }
            }

            // Check for duration information
            if (this.bookingState.step === 'duration-selection') {
                // Try to get duration from message
                const durationMatch = lowerMessage.match(/(\d+)\s*(?:hour|hr|h)s?/i);
                if (durationMatch) {
                    const duration = parseInt(durationMatch[1]);
                    // Limit to reasonable values
                    this.bookingState.data.duration = Math.min(24, Math.max(1, duration));
                    console.log('Duration detected:', this.bookingState.data.duration);
                    this.bookingState.step = 'slot-selection';
                    return;
                }

                // Try to get time range from message (e.g., "5 pm to 7 pm")
                const timeRangeMatch = lowerMessage.match(/(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)/i);
                if (timeRangeMatch) {
                    // We have a time range, extract start and end times
                    const startTimeStr = timeRangeMatch[1].toLowerCase();
                    const endTimeStr = timeRangeMatch[2].toLowerCase();

                    // Parse start time
                    let startHours, startMinutes;
                    if (startTimeStr.includes('am') || startTimeStr.includes('pm')) {
                        // Handle 12-hour format
                        const isPM = startTimeStr.includes('pm');
                        const timeParts = startTimeStr.replace(/(am|pm)/i, '').trim().split(':');
                        startHours = parseInt(timeParts[0]);
                        startMinutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;

                        if (isPM && startHours < 12) startHours += 12;
                        if (!isPM && startHours === 12) startHours = 0;
                    } else {
                        // Handle 24-hour format or just hour
                        const timeParts = startTimeStr.trim().split(':');
                        startHours = parseInt(timeParts[0]);
                        startMinutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;
                    }

                    // Parse end time
                    let endHours, endMinutes;
                    if (endTimeStr.includes('am') || endTimeStr.includes('pm')) {
                        // Handle 12-hour format
                        const isPM = endTimeStr.includes('pm');
                        const timeParts = endTimeStr.replace(/(am|pm)/i, '').trim().split(':');
                        endHours = parseInt(timeParts[0]);
                        endMinutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;

                        if (isPM && endHours < 12) endHours += 12;
                        if (!isPM && endHours === 12) endHours = 0;
                    } else {
                        // Handle 24-hour format or just hour
                        const timeParts = endTimeStr.trim().split(':');
                        endHours = parseInt(timeParts[0]);
                        endMinutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;
                    }

                    // Update booking time to start time if needed
                    if (!this.bookingState.data.time) {
                        this.bookingState.data.time = `${String(startHours).padStart(2, '0')}:${String(startMinutes).padStart(2, '0')}`;
                    }

                    // Calculate duration in hours
                    const startDate = new Date();
                    startDate.setHours(startHours, startMinutes, 0, 0);

                    const endDate = new Date();
                    endDate.setHours(endHours, endMinutes, 0, 0);

                    // If end time is earlier than start time, assume it's the next day
                    if (endDate < startDate) {
                        endDate.setDate(endDate.getDate() + 1);
                    }

                    // Calculate duration in hours
                    const durationMs = endDate - startDate;
                    const durationHours = Math.max(1, Math.round(durationMs / (1000 * 60 * 60)));

                    this.bookingState.data.duration = durationHours;
                    console.log(`Calculated duration from time range: ${this.bookingState.data.duration} hours`);
                    this.bookingState.step = 'slot-selection';
                    return;
                }
            }

            // Check for slot selection
            if (lowerMessage.includes('slot') && /\d+/.test(lowerMessage)) {
                const slotMatch = lowerMessage.match(/slot\s+(\d+)/i);
                if (slotMatch && slotMatch[1]) {
                    this.bookingState.data.slotId = slotMatch[1];
                    this.bookingState.step = 'confirmation';
                    console.log('Slot ID detected:', this.bookingState.data.slotId);
                }
            }

            // Check for confirmation
            if (lowerMessage === 'yes' || lowerMessage === 'confirm' || lowerMessage.includes('book it')) {
                if (this.bookingState.step === 'slot-selection' || this.bookingState.step === 'confirmation') {
                    this.bookingState.step = 'processing';
                }
            }

            console.log('Booking state updated:', this.bookingState);
        }
    }

    extractMallName(message) {
        // Extract mall name from message
        const mallPatterns = [
            { regex: /phoenix\s+mall\s+of\s+asia/i, name: 'Phoenix Mall of Asia' },
            { regex: /phoenix\s+market\s+city/i, name: 'Phoenix Market City' },
            { regex: /palladium\s+mall/i, name: 'Palladium Mall' },
            { regex: /orion\s+mall/i, name: 'Orion Mall' },
            { regex: /ub\s+city\s+mall/i, name: 'UB City Mall' },
            { regex: /forum\s+mall/i, name: 'Forum Mall' },
            { regex: /mall\s+(\d+)/i, nameFunc: (match) => `Mall ${match[1]}` },
            // Generic pattern to catch any mall name
            { regex: /at\s+([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+mall/i, nameFunc: (match) => `${match[1]} Mall` }
        ];

        for (const pattern of mallPatterns) {
            const match = message.match(pattern.regex);
            if (match) {
                return pattern.nameFunc ? pattern.nameFunc(match) : pattern.name;
            }
        }

        // If no specific mall pattern matched but "mall" is mentioned, try to extract the mall name
        if (message.toLowerCase().includes('mall')) {
            const genericMallMatch = message.match(/([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+mall/i);
            if (genericMallMatch && genericMallMatch[1]) {
                // Capitalize first letter of each word
                const mallName = genericMallMatch[1].replace(/\b\w/g, l => l.toUpperCase());
                return `${mallName} Mall`;
            }
        }

        return null;
    }

    extractVehicleType(message) {
        // Extract vehicle type from message
        if (message.includes('car')) return 'car';
        if (message.includes('bike')) return 'bike';
        if (message.includes('truck')) return 'truck';
        return null;
    }

    processResponseForBookingState(response) {
        const lowerResponse = response.toLowerCase();

        // Check if response is asking for mall selection
        if (lowerResponse.includes('which mall') ||
            (lowerResponse.includes('mall') && lowerResponse.includes('prefer'))) {
            this.bookingState.step = 'mall-selection';
        }

        // Check if response is asking for vehicle type
        else if (lowerResponse.includes('what type of vehicle') ||
                lowerResponse.includes('which vehicle')) {
            this.bookingState.step = 'vehicle-selection';
        }

        // Check if response is asking for duration
        else if (lowerResponse.includes('how long') ||
                lowerResponse.includes('specify the number of hours') ||
                lowerResponse.includes('provide a time range') ||
                (lowerResponse.includes('hours') && lowerResponse.includes('like to park'))) {
            this.bookingState.step = 'duration-selection';
            console.log('Duration selection step detected');
        }

        // Check if response is showing available slots
        else if (lowerResponse.includes('available slot') ||
                lowerResponse.includes('slot id:')) {
            this.bookingState.step = 'slot-selection';
        }

        // Check if response is asking for confirmation
        else if (lowerResponse.includes('confirm') &&
                (lowerResponse.includes('booking') || lowerResponse.includes('proceed'))) {
            this.bookingState.step = 'confirmation';
        }

        // Check if booking is confirmed
        else if (lowerResponse.includes('booking has been confirmed') ||
                lowerResponse.includes('booking details') ||
                lowerResponse.includes('booking is confirmed') ||
                lowerResponse.includes('your booking is confirmed') ||
                lowerResponse.includes('your booking has been added')) {
            console.log('Booking confirmation detected in processResponseForBookingState');
            this.bookingState.inProgress = false;
            this.bookingState.step = null;
        }

        console.log('Booking state after response:', this.bookingState);
    }

    cleanupResponse(response) {
        // Fix contradictory responses
        if (response.includes('No available slots found') && response.includes('Slot ID:')) {
            console.log('Fixing contradictory response about available slots');

            // Split the response into lines
            const lines = response.split('\n');
            let cleanedLines = [];
            let foundSlots = false;
            let foundNoSlotsMessage = false;
            let mallName = '';

            // Extract mall name if present
            const mallMatch = response.match(/Available slots at ([^:]+):/);
            if (mallMatch && mallMatch[1]) {
                mallName = mallMatch[1].trim();
            }

            // Process each line
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];

                // Skip "No available slots found" lines
                if (line.includes('No available slots found for your criteria')) {
                    foundNoSlotsMessage = true;
                    continue;
                }

                // Check if this is a slot information line
                if (line.includes('Slot ID:') || (line.includes('Mall:') && line.includes('Type:'))) {
                    foundSlots = true;
                }

                // Add the line to our cleaned lines
                cleanedLines.push(line);
            }

            // If we found slots but also had a "no slots" message, add a proper header
            if (foundSlots && foundNoSlotsMessage) {
                // Find where to insert the header
                const insertIndex = cleanedLines.findIndex(line =>
                    line.includes('Slot ID:') || (line.includes('Mall:') && line.includes('Type:'))
                );

                if (insertIndex > 0) {
                    const headerText = mallName ?
                        `Available slots at ${mallName}:` :
                        'Available slots:';

                    cleanedLines.splice(insertIndex, 0, headerText);
                    cleanedLines.splice(insertIndex, 0, ''); // Add blank line
                }
            }

            // Remove any duplicate "Available slots at X:" headers
            const uniqueLines = [];
            let lastLine = '';

            for (const line of cleanedLines) {
                // Skip duplicate headers
                if (line.startsWith('Available slots at') && lastLine.startsWith('Available slots at')) {
                    continue;
                }

                uniqueLines.push(line);
                lastLine = line;
            }

            return uniqueLines.join('\n');
        }

        return response;
    }

    handleOfflineResponse(message) {
        const lowerMessage = message.toLowerCase();

        // Check if this is a booking inquiry
        if ((lowerMessage.includes('book') || lowerMessage.includes('park') || lowerMessage.includes('reserve')) &&
            (lowerMessage.includes('slot') || lowerMessage.includes('parking'))) {

            // Extract mall and vehicle type if available
            const mallName = this.extractMallName(lowerMessage) || 'the mall';
            const vehicleType = this.extractVehicleType(lowerMessage) || 'car';

            // Extract date and time information if available
            let bookingDate, bookingTime, bookingDuration;

            // Try to get date from message
            const dateMatch = lowerMessage.match(/(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})/i);
            if (dateMatch) {
                const dateStr = dateMatch[1].toLowerCase();
                const today = new Date();

                if (dateStr === 'today') {
                    bookingDate = today;
                } else if (dateStr === 'tomorrow') {
                    const tomorrow = new Date(today);
                    tomorrow.setDate(tomorrow.getDate() + 1);
                    bookingDate = tomorrow;
                } else if (['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].includes(dateStr)) {
                    // Find the next occurrence of the day
                    const dayMap = {
                        'sunday': 0, 'monday': 1, 'tuesday': 2, 'wednesday': 3,
                        'thursday': 4, 'friday': 5, 'saturday': 6
                    };
                    const targetDay = dayMap[dateStr];
                    const nextDay = new Date(today);
                    nextDay.setDate(today.getDate() + (targetDay + 7 - today.getDay()) % 7);
                    bookingDate = nextDay;
                }
            }

            // If no date was found or parsed, default to tomorrow
            if (!bookingDate) {
                const tomorrow = new Date();
                tomorrow.setDate(tomorrow.getDate() + 1);
                bookingDate = tomorrow;
            }

            // Try to get time range from message (e.g., "5 pm to 7 pm")
            const timeRangeMatch = lowerMessage.match(/(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)/i);

            if (timeRangeMatch) {
                // We have a time range, extract start and end times
                const startTimeStr = timeRangeMatch[1].toLowerCase();
                const endTimeStr = timeRangeMatch[2].toLowerCase();

                // Parse start time
                let startHours, startMinutes;
                if (startTimeStr.includes('am') || startTimeStr.includes('pm')) {
                    // Handle 12-hour format
                    const isPM = startTimeStr.includes('pm');
                    const timeParts = startTimeStr.replace(/(am|pm)/i, '').trim().split(':');
                    startHours = parseInt(timeParts[0]);
                    startMinutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;

                    if (isPM && startHours < 12) startHours += 12;
                    if (!isPM && startHours === 12) startHours = 0;
                } else {
                    // Handle 24-hour format or just hour
                    const timeParts = startTimeStr.trim().split(':');
                    startHours = parseInt(timeParts[0]);
                    startMinutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;
                }

                // Parse end time
                let endHours, endMinutes;
                if (endTimeStr.includes('am') || endTimeStr.includes('pm')) {
                    // Handle 12-hour format
                    const isPM = endTimeStr.includes('pm');
                    const timeParts = endTimeStr.replace(/(am|pm)/i, '').trim().split(':');
                    endHours = parseInt(timeParts[0]);
                    endMinutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;

                    if (isPM && endHours < 12) endHours += 12;
                    if (!isPM && endHours === 12) endHours = 0;
                } else {
                    // Handle 24-hour format or just hour
                    const timeParts = endTimeStr.trim().split(':');
                    endHours = parseInt(timeParts[0]);
                    endMinutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;
                }

                // Set booking time to start time
                bookingTime = `${String(startHours).padStart(2, '0')}:${String(startMinutes).padStart(2, '0')}`;

                // Calculate duration in hours
                const startDate = new Date();
                startDate.setHours(startHours, startMinutes, 0, 0);

                const endDate = new Date();
                endDate.setHours(endHours, endMinutes, 0, 0);

                // If end time is earlier than start time, assume it's the next day
                if (endDate < startDate) {
                    endDate.setDate(endDate.getDate() + 1);
                }

                // Calculate duration in hours
                const durationMs = endDate - startDate;
                const durationHours = Math.max(1, Math.round(durationMs / (1000 * 60 * 60)));

                bookingDuration = durationHours;
                console.log(`Calculated duration from time range: ${bookingDuration} hours`);
            } else {
                // No time range found, try to get single time
                const timeMatch = lowerMessage.match(/(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)/i);
                if (timeMatch) {
                    const timeStr = timeMatch[1].toLowerCase();
                    // Simple time parsing
                    if (timeStr.includes('am') || timeStr.includes('pm')) {
                        // Handle 12-hour format
                        const isPM = timeStr.includes('pm');
                        const timeParts = timeStr.replace(/(am|pm)/i, '').trim().split(':');
                        let hours = parseInt(timeParts[0]);
                        const minutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;

                        if (isPM && hours < 12) hours += 12;
                        if (!isPM && hours === 12) hours = 0;

                        bookingTime = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
                    } else {
                        // Handle 24-hour format or just hour
                        const timeParts = timeStr.trim().split(':');
                        const hours = parseInt(timeParts[0]);
                        const minutes = timeParts.length > 1 ? parseInt(timeParts[1]) : 0;

                        bookingTime = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
                    }
                }

                // If no time was found, default to current hour + 1
                if (!bookingTime) {
                    const now = new Date();
                    const nextHour = (now.getHours() + 1) % 24;
                    bookingTime = `${String(nextHour).padStart(2, '0')}:00`;
                }

                // Try to get duration from message
                const durationMatch = lowerMessage.match(/(\d+)\s*(?:hour|hr|h)s?/i);
                if (durationMatch) {
                    bookingDuration = parseInt(durationMatch[1]);
                    // Limit to reasonable values
                    if (bookingDuration < 1) bookingDuration = 1;
                    if (bookingDuration > 24) bookingDuration = 24;
                } else {
                    // If no duration was specified, ask the user for duration
                    bookingDuration = null;
                }
            }

            // Format date for display
            const formattedDate = bookingDate.toLocaleDateString();

            // Generate simulated available slots
            const slotIds = [];
            const startId = Math.floor(Math.random() * 10) + 20; // Random starting ID between 20-29

            for (let i = 0; i < 3; i++) {
                slotIds.push(startId + i);
            }

            // Create response based on whether we have duration or not
            let response;

            if (bookingDuration === null) {
                // If duration is not provided, ask for it
                response = `I need to know how long you'd like to park at ${mallName} on ${formattedDate} at ${bookingTime}. Please specify the number of hours or provide a time range (e.g., "2 hours" or "from ${bookingTime} to 8 PM").`;

                // Update booking state
                this.bookingState.step = 'duration-selection';
                this.bookingState.data.mall = mallName;
                this.bookingState.data.vehicleType = vehicleType;
                this.bookingState.data.date = bookingDate.toISOString().split('T')[0];
                this.bookingState.data.time = bookingTime;

                this.addAssistantMessage(response);
                return;
            } else {
                // If we have duration, proceed with slot listing
                response = `I found some available ${vehicleType} slots at ${mallName} for ${formattedDate} at ${bookingTime} for ${bookingDuration} hour(s):\n\n`;
            }

            // Update booking state with extracted information
            this.bookingState.data.mall = mallName;
            this.bookingState.data.vehicleType = vehicleType;
            this.bookingState.data.date = bookingDate.toISOString().split('T')[0];
            this.bookingState.data.time = bookingTime;
            this.bookingState.data.duration = bookingDuration;

            // Update the parking info component if available
            if (window.parkingInfoComponent && window.parkingInfoComponent.availableSlotsFilter) {
                window.parkingInfoComponent.availableSlotsFilter.date = this.bookingState.data.date;
                window.parkingInfoComponent.availableSlotsFilter.time = this.bookingState.data.time;
                window.parkingInfoComponent.availableSlotsFilter.duration = this.bookingState.data.duration;
                window.parkingInfoComponent.initializeDateTimeFields();
            }

            // Add slot information
            response += '<div class="available-slots-list">';
            response += '<p class="mb-2"><strong>Available Slot IDs:</strong></p>';
            response += '<div class="slot-ids-container">';

            slotIds.forEach(id => {
                response += `
                    <button class="slot-id-btn" onclick="window.chatInterfaceComponent.bookSlot(${id})">
                        Slot ${id}
                    </button>
                `;
            });

            response += '</div>';

            // Add slot details
            response += '<div class="mt-3 pt-2 border-t border-gray-200">';
            slotIds.forEach(id => {
                const slotNumber = `${vehicleType.charAt(0).toUpperCase()}${String(id).padStart(3, '0')}`;
                const rate = vehicleType === 'car' ? 50 : (vehicleType === 'bike' ? 20 : 80);

                response += `<div class="text-sm my-1">Slot ID: ${id}, Number: ${slotNumber}, Rate: ₹${rate}.0/hour</div>`;
            });
            response += '</div>';

            response += '</div>';

            // Add booking instructions
            response += '\nTo book a slot, please use the format: "Book slot [SLOT_ID]"\n';
            response += 'For example: "Book slot ' + slotIds[0] + '"\n\n';
            response += 'Or you can say "yes" or "confirm" to book an available slot automatically.';

            // Add offline mode notice
            response += '<p class="text-xs text-gray-500 mt-3">Note: Running in offline mode. Bookings will be simulated.</p>';

            this.addAssistantMessage(response);

            // Update booking state
            this.bookingState.step = 'slot-selection';
            this.bookingState.data.mall = mallName;
            this.bookingState.data.vehicleType = vehicleType;

        } else if (lowerMessage.includes('hello') || lowerMessage.includes('hi') || lowerMessage.includes('hey')) {
            // Simple greeting
            this.addAssistantMessage('Hello! I\'m your parking assistant. How can I help you today? (Note: I\'m currently running in offline mode)');
        } else if (lowerMessage.includes('help') || lowerMessage.includes('what can you do')) {
            // Help message
            this.addAssistantMessage(`
                I can help you with parking-related tasks. Here are some things you can ask me:
                <ul class="list-disc ml-5 mt-2">
                    <li>Book a parking slot at a specific mall</li>
                    <li>Check available parking slots</li>
                    <li>View your current bookings</li>
                </ul>
                <p class="text-xs text-gray-500 mt-3">Note: Running in offline mode. Some features may be limited.</p>
            `);
        } else {
            // Generic response
            this.addAssistantMessage(`
                I'm not sure how to respond to that in offline mode.
                <p class="mt-2">Try asking about booking a parking slot at a specific mall. For example:</p>
                <p class="mt-1 italic">"I need to park my car at Phoenix Mall for 2 hours"</p>
                <p class="text-xs text-gray-500 mt-3">Note: Running in offline mode. Some features may be limited.</p>
            `);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterfaceComponent = new ChatInterfaceComponent();
});