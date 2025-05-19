# AI Agent Documentation

This document provides a detailed explanation of how our AI agent works, focusing on its four main features: Natural Language Understanding, Intent Recognition, Tool Selection, and Memory Management.

## Overview

Our AI agent is built to provide a natural language interface for the Parking Management System. It uses the Groq API with the Llama-3.3-70b-versatile model to understand user queries, determine intent, select appropriate tools, and maintain conversation context.

## 1. Natural Language Understanding

The agent uses advanced natural language processing to understand user queries in plain English, eliminating the need for users to learn specific commands or syntax.

### Implementation Details

- **Model**: Llama-3.3-70b-versatile via Groq API
- **Context Window**: The agent can process up to 1000 tokens in a single query
- **Temperature Setting**: 0.2 (lower temperature for more deterministic responses)
- **Pattern Recognition**: Regular expressions to extract specific information like license plate numbers

### Example Flow

1. User inputs a natural language query: "I need to find parking at Phoenix Mall tomorrow morning"
2. The agent processes the text to extract key information:
   - Action: find parking
   - Location: Phoenix Mall
   - Time: tomorrow morning
3. The agent formulates a response based on the extracted information

```python
def _call_groq_api(self, messages):
    """Call the Groq API directly."""
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": self.model_name,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 1000
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=data
    )
```

## 2. Intent Recognition

The agent analyzes user queries to determine the underlying intent, allowing it to respond appropriately even when requests are ambiguous or incomplete.

### Key Intents

- **booking_creation**: Creating a new parking booking
- **booking_cancellation**: Canceling an existing booking
- **booking_inquiry**: Checking existing bookings
- **slot_availability**: Finding available parking slots
- **rate_inquiry**: Checking parking rates
- **vehicle_management**: Managing user vehicles
- **mall_information**: Getting information about malls
- **payment_calculation**: Calculating parking fees

### Implementation Details

The agent uses a combination of keyword matching and contextual analysis to determine intent:

```python
# Track query type and intent
if "available" in query_lower or "find" in query_lower or "looking for" in query_lower:
    self.conversation_context["intent"] = "check_available_slots"
elif "book" in query_lower or "reserve" in query_lower:
    self.conversation_context["intent"] = "create_booking"
elif "cancel" in query_lower:
    self.conversation_context["intent"] = "cancel_booking"
elif "rate" in query_lower or "price" in query_lower or "cost" in query_lower:
    self.conversation_context["intent"] = "check_parking_rates"
```

### Intent Scoring

The agent assigns confidence scores to each detected intent:

```
Detected intents: {
    'booking_creation': 0.7, 
    'booking_inquiry': 0.8, 
    'slot_availability': 0.0, 
    'rate_inquiry': 0.0
}
```

## 3. Tool Selection

Based on the detected intent, the agent selects the most appropriate tool to handle the user's request.

### Available Tools

- **create_booking**: Create a new parking booking
- **cancel_booking**: Cancel an existing booking
- **get_user_bookings**: Retrieve a user's bookings
- **get_available_slots**: Find available parking slots
- **get_parking_rates**: Check parking rates
- **get_user_vehicles**: Retrieve a user's vehicles
- **add_vehicle**: Add a new vehicle
- **remove_vehicle**: Remove a vehicle
- **get_malls**: Get a list of malls
- **get_mall_stats**: Get statistics for a mall
- **calculate_parking_fee**: Calculate parking fees
- **get_booking_receipt**: Get a booking receipt

### Tool Selection Algorithm

The agent combines intent scores with keyword matching to select the most appropriate tool:

```
Combined tool scores: {
    'create_booking': 0.7, 
    'cancel_booking': 0.0, 
    'get_user_bookings': 1.17, 
    'get_available_slots': 0.0
}
Selected tool: get_user_bookings (score: 1.17)
```

### Implementation Details

```python
# If no specific command matched, check the detected intent
elif self.conversation_context.get("intent"):
    intent = self.conversation_context["intent"]
    print(f"Using detected intent: {intent}")

    if intent == "check_available_slots":
        return self._check_available_slots()
    elif intent == "check_parking_rates":
        return self._check_parking_rates()
    elif intent == "check_user_bookings":
        return self._check_user_bookings()
    elif intent == "create_booking" and self.conversation_context["selected_mall_id"] and self.conversation_context["selected_vehicle_type"]:
        return self._create_booking_from_context()
```

## 4. Memory Management

The agent maintains conversation context and history to provide a coherent and personalized experience across multiple interactions.

### Memory Components

1. **Conversation Context**: Stores information about the current conversation
2. **In-Memory Store**: Persists data between requests
3. **Vector Store**: Stores and retrieves conversation history using embeddings
4. **File-based Chat History**: Backup storage for conversation history

### Implementation Details

#### Conversation Context

```python
# Initialize conversation context
self.conversation_context = {
    "selected_mall_id": None,
    "selected_vehicle_type": None,
    "selected_license_plate": None,
    "selected_slot_id": None,
    "selected_booking_id": None,
    "selected_date": None,
    "selected_duration": None,
    "last_query_type": None,
    "intent": None
}
```

#### Adding Interactions to Memory

```python
def add_interaction(self, user_query: str, agent_response: str) -> None:
    """Add a user-agent interaction to the memory."""
    # Add to conversation buffer memory
    self.memory.add_user_message(user_query)
    self.memory.add_ai_message(agent_response)

    # Create entry for conversation history
    timestamp = datetime.now(timezone.utc).isoformat()
    interaction_id = str(uuid.uuid4())

    entry = {
        "user_query": user_query,
        "agent_response": agent_response,
        "timestamp": timestamp,
        "interaction_id": interaction_id,
        "user_id": self.user_id
    }

    # Add to conversation history
    self.conversation_history.append(entry)

    # Save conversation history
    self._save_conversation_history()
```

### Memory Retrieval

The agent can retrieve relevant conversation history to maintain context:

```python
# Get relevant conversation history
relevant_history = self.memory_manager.get_relevant_history(query, max_entries=5)

# Add conversation history to messages
if relevant_history:
    # Add each message from history as a separate message with proper role
    for history_entry in relevant_history:
        if history_entry.startswith("User: "):
            user_msg = history_entry.replace("User: ", "", 1)
            messages.append({"role": "user", "content": user_msg})
        elif history_entry.startswith("Agent: "):
            agent_msg = history_entry.replace("Agent: ", "", 1)
            messages.append({"role": "assistant", "content": agent_msg})
```

## Integration with Frontend

The frontend uses JavaScript to analyze message intent and manage the booking state:

```javascript
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
    }
}
```

## Conclusion

Our AI agent combines natural language understanding, intent recognition, tool selection, and memory management to provide a seamless and intuitive interface for the Parking Management System. By leveraging the power of the Llama-3.3-70b-versatile model through the Groq API, the agent can understand complex queries, maintain context across conversations, and execute the appropriate actions to help users find, book, and manage parking spaces.
