"""
Simple in-memory store for persisting agent state between requests.
"""

class InMemoryStore:
    """Simple in-memory store for persisting agent state between requests."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InMemoryStore, cls).__new__(cls)
            cls._instance.pending_bookings = {}
            cls._instance.conversation_contexts = {}
        return cls._instance

    def get_pending_booking(self, user_id):
        """Get pending booking for a user."""
        return self.pending_bookings.get(user_id)

    def set_pending_booking(self, user_id, booking):
        """Set pending booking for a user."""
        self.pending_bookings[user_id] = booking

    def clear_pending_booking(self, user_id):
        """Clear pending booking for a user."""
        if user_id in self.pending_bookings:
            del self.pending_bookings[user_id]

    def get_conversation_context(self, user_id):
        """Get conversation context for a user."""
        return self.conversation_contexts.get(user_id, {
            "selected_mall": None,
            "selected_mall_id": None,
            "selected_vehicle_type": None,
            "selected_license_plate": None,
            "selected_time_period": None,
            "last_query_type": None,
            "parking_rates": None,
            "intent": None,
            "pending_slot_id": None
        })

    def set_conversation_context(self, user_id, context):
        """Set conversation context for a user."""
        self.conversation_contexts[user_id] = context

    def update_conversation_context(self, user_id, key, value):
        """Update a specific key in the conversation context for a user."""
        if user_id not in self.conversation_contexts:
            self.conversation_contexts[user_id] = {
                "selected_mall": None,
                "selected_mall_id": None,
                "selected_vehicle_type": None,
                "selected_license_plate": None,
                "selected_time_period": None,
                "last_query_type": None,
                "parking_rates": None,
                "intent": None,
                "pending_slot_id": None
            }
        self.conversation_contexts[user_id][key] = value
