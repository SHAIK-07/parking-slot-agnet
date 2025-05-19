"""
Simple file-based chat history implementation that doesn't rely on vector stores.
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class FileChatHistory:
    """Chat history manager that uses simple JSON files."""

    def __init__(self, user_id: str, persist_directory: str = "chat_history"):
        """Initialize the file chat history manager.

        Args:
            user_id: The user ID to associate with this chat history
            persist_directory: Directory to persist the chat history
        """
        self.user_id = user_id
        self.persist_directory = os.path.join(persist_directory, f"user_{user_id}")

        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Metadata file for conversation names and other metadata
        self.metadata_file = os.path.join(self.persist_directory, "metadata.json")
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file if it exists."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {str(e)}")

        # Return default metadata if file doesn't exist or loading fails
        return {
            "user_id": self.user_id,
            "conversations": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    def _save_metadata(self):
        """Save metadata to file."""
        try:
            self.metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {str(e)}")

    def _get_conversation_file(self, conversation_id: str) -> str:
        """Get the file path for a conversation."""
        return os.path.join(self.persist_directory, f"{conversation_id}.json")

    def add_interaction(self, conversation_id: str, user_query: str, agent_response: str,
                        conversation_name: Optional[str] = None) -> str:
        """Add a user-agent interaction to the chat history.

        Args:
            conversation_id: ID of the conversation
            user_query: User's query
            agent_response: Agent's response
            conversation_name: Optional name for the conversation

        Returns:
            The ID of the added interaction
        """
        # Generate interaction ID
        interaction_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Create interaction
        interaction = {
            "interaction_id": interaction_id,
            "user_query": user_query,
            "agent_response": agent_response,
            "timestamp": timestamp
        }

        # Get conversation file
        conversation_file = self._get_conversation_file(conversation_id)

        # Load existing interactions or create new list
        interactions = []
        if os.path.exists(conversation_file):
            try:
                with open(conversation_file, "r") as f:
                    interactions = json.load(f)
            except Exception as e:
                print(f"Error loading conversation file: {str(e)}")

        # Add new interaction
        interactions.append(interaction)

        # Save interactions
        try:
            with open(conversation_file, "w") as f:
                json.dump(interactions, f, indent=2)
        except Exception as e:
            print(f"Error saving conversation file: {str(e)}")

        # Update metadata
        if conversation_id not in self.metadata["conversations"]:
            self.metadata["conversations"][conversation_id] = {
                "name": conversation_name or f"Conversation {len(self.metadata['conversations']) + 1}",
                "created_at": timestamp,
                "updated_at": timestamp,
                "interactions": []
            }

        self.metadata["conversations"][conversation_id]["interactions"].append({
            "interaction_id": interaction_id,
            "timestamp": timestamp
        })
        self.metadata["conversations"][conversation_id]["updated_at"] = timestamp

        # Save metadata
        self._save_metadata()

        return interaction_id

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get the complete history of a specific conversation.

        Args:
            conversation_id: ID of the conversation to retrieve

        Returns:
            List of interactions in the conversation
        """
        if conversation_id not in self.metadata["conversations"]:
            return []

        # Get conversation file
        conversation_file = self._get_conversation_file(conversation_id)

        # Load interactions
        interactions = []
        if os.path.exists(conversation_file):
            try:
                with open(conversation_file, "r") as f:
                    interactions = json.load(f)
            except Exception as e:
                print(f"Error loading conversation file: {str(e)}")

        # Sort by timestamp
        interactions.sort(key=lambda x: x.get("timestamp", ""))

        return interactions

    def list_conversations(self) -> List[Dict[str, Any]]:
        """List all conversations for the user.

        Returns:
            List of conversation metadata
        """
        return [
            {
                "conversation_id": conv_id,
                "name": conv_data["name"],
                "created_at": conv_data["created_at"],
                "updated_at": conv_data["updated_at"],
                "interaction_count": len(conv_data["interactions"])
            }
            for conv_id, conv_data in self.metadata["conversations"].items()
        ]

    def rename_conversation(self, conversation_id: str, new_name: str) -> bool:
        """Rename a conversation.

        Args:
            conversation_id: ID of the conversation to rename
            new_name: New name for the conversation

        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.metadata["conversations"]:
            return False

        self.metadata["conversations"][conversation_id]["name"] = new_name
        self.metadata["conversations"][conversation_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_metadata()

        return True

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its interactions.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            True if successful, False otherwise
        """
        if conversation_id not in self.metadata["conversations"]:
            return False

        # Delete conversation file
        conversation_file = self._get_conversation_file(conversation_id)
        if os.path.exists(conversation_file):
            try:
                os.remove(conversation_file)
            except Exception as e:
                print(f"Error deleting conversation file: {str(e)}")

        # Delete from metadata
        del self.metadata["conversations"][conversation_id]
        self._save_metadata()

        return True

    def get_relevant_history(self, query: str, k: int = 5) -> List[Dict[str, str]]:
        """Get relevant conversation history based on simple keyword matching.

        This is a simplified version that doesn't use vector search.
        It just returns the most recent interactions.

        Args:
            query: The query to find relevant history for (ignored in this implementation)
            k: Number of relevant interactions to retrieve

        Returns:
            List of relevant interactions as dictionaries
        """
        # Get all conversations
        all_interactions = []
        for conversation_id in self.metadata["conversations"]:
            interactions = self.get_conversation_history(conversation_id)
            all_interactions.extend(interactions)

        # Sort by timestamp (most recent first)
        all_interactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        # Return the k most recent interactions
        return all_interactions[:k]
