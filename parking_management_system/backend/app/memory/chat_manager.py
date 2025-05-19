from typing import List, Dict, Any, Optional
import os
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime, timezone
import json
import uuid

# Custom implementation of memory to avoid deprecation warnings
class CustomConversationMemory:
    def __init__(self, memory_key="chat_history"):
        self.memory_key = memory_key
        self.chat_memory = CustomChatMessageHistory()

    def add_user_message(self, message: str) -> None:
        self.chat_memory.add_user_message(message)

    def add_ai_message(self, message: str) -> None:
        self.chat_memory.add_ai_message(message)

class CustomChatMessageHistory(BaseChatMessageHistory):
    def __init__(self):
        self.messages = []

    def add_user_message(self, message: str) -> None:
        self.messages.append(HumanMessage(content=message))

    def add_ai_message(self, message: str) -> None:
        self.messages.append(AIMessage(content=message))

    def clear(self) -> None:
        """Clear the message history."""
        self.messages = []

class ChatMemoryManager:
    def __init__(self, user_id: str, persist_directory: str = "memory_db"):
        self.user_id = user_id
        self.persist_directory = os.path.join(persist_directory, f"user_{user_id}")
        self.memory = CustomConversationMemory(memory_key="chat_history")
        self.conversation_history = []

        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Load existing conversation history if available
        self._load_conversation_history()

    def _load_conversation_history(self):
        """Load conversation history from file if it exists."""
        history_file = os.path.join(self.persist_directory, "conversation_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as f:
                    self.conversation_history = json.load(f)

                # Rebuild memory from history
                for entry in self.conversation_history:
                    if "user_query" in entry and "agent_response" in entry:
                        self.memory.add_user_message(entry["user_query"])
                        self.memory.add_ai_message(entry["agent_response"])
            except Exception as e:
                print(f"Error loading conversation history: {str(e)}")
                self.conversation_history = []

    def _save_conversation_history(self):
        """Save conversation history to file."""
        history_file = os.path.join(self.persist_directory, "conversation_history.json")
        try:
            with open(history_file, "w") as f:
                json.dump(self.conversation_history, f, indent=2)
        except Exception as e:
            print(f"Error saving conversation history: {str(e)}")

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

    def get_relevant_history(self, query: str, k: int = 5) -> List[str]:
        """Retrieve relevant conversation history based on the query.

        This is a simple implementation that returns the most recent conversations.
        In a production environment, you would want to use a proper vector store.
        """
        if not self.conversation_history:
            return []

        # Sort by timestamp (newest first) and take the k most recent conversations
        sorted_history = sorted(
            self.conversation_history,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:k]

        # Format the conversations
        return [
            f"User: {entry['user_query']}\nAgent: {entry['agent_response']}"
            for entry in sorted_history
        ]

    def get_conversation_memory(self) -> CustomConversationMemory:
        """Get the conversation memory for the agent."""
        return self.memory

    def clear_memory(self) -> None:
        """Clear the conversation memory."""
        self.memory = CustomConversationMemory(memory_key="chat_history")
        self.conversation_history = []
        self._save_conversation_history()

    def save_memory_to_file(self, file_path: Optional[str] = None) -> str:
        """Save the current conversation memory to a file."""
        if file_path is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(self.persist_directory, f"memory_{timestamp}.json")

        memory_dict = {
            "user_id": self.user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "messages": [
                {
                    "type": msg.type,
                    "content": msg.content
                }
                for msg in self.memory.chat_memory.messages
            ],
            "conversation_history": self.conversation_history
        }

        with open(file_path, "w") as f:
            json.dump(memory_dict, f, indent=2)

        return file_path

    def load_memory_from_file(self, file_path: str) -> bool:
        """Load conversation memory from a file."""
        try:
            with open(file_path, "r") as f:
                memory_dict = json.load(f)

            # Clear current memory
            self.clear_memory()

            # Add messages to memory
            for msg in memory_dict["messages"]:
                if msg["type"] == "human":
                    self.memory.add_user_message(msg["content"])
                elif msg["type"] == "ai":
                    self.memory.add_ai_message(msg["content"])

            # Load conversation history if available
            if "conversation_history" in memory_dict:
                self.conversation_history = memory_dict["conversation_history"]
                self._save_conversation_history()

            return True
        except Exception as e:
            print(f"Error loading memory from file: {str(e)}")
            return False
