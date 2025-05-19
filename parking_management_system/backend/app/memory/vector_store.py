from typing import List, Dict, Any, Optional
import os
import json
import uuid
from datetime import datetime, timezone

# Try different import paths based on what's available
try:
    from langchain_chroma import Chroma
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
    except ImportError:
        from langchain.vectorstores import Chroma

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:
        from langchain.embeddings import HuggingFaceEmbeddings

try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.schema import Document
    except ImportError:
        # Define a simple Document class if all else fails
        class Document:
            def __init__(self, page_content, metadata=None):
                self.page_content = page_content
                self.metadata = metadata or {}

class VectorChatHistory:
    """Chat history manager that uses vector database for semantic search."""

    def __init__(self, user_id: str, persist_directory: str = "vector_db"):
        """Initialize the vector chat history manager.

        Args:
            user_id: The user ID to associate with this chat history
            persist_directory: Directory to persist the vector database
        """
        self.user_id = user_id
        self.persist_directory = os.path.join(persist_directory, f"user_{user_id}")

        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            cache_folder=os.path.join(persist_directory, "models")
        )

        # Initialize or load vector store
        self._initialize_vector_store()

        # Metadata file for conversation names and other metadata
        self.metadata_file = os.path.join(self.persist_directory, "metadata.json")
        self.metadata = self._load_metadata()

    def _initialize_vector_store(self):
        """Initialize or load the vector store."""
        try:
            # Try to load existing vector store
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
        except Exception as e:
            print(f"Error loading vector store: {str(e)}")
            # Create a new vector store if loading fails
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )

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

    def add_interaction(self, conversation_id: str, user_query: str, agent_response: str,
                        conversation_name: Optional[str] = None) -> str:
        """Add a user-agent interaction to the vector store.

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

        # Create documents for vector store
        user_doc = Document(
            page_content=user_query,
            metadata={
                "interaction_id": interaction_id,
                "conversation_id": conversation_id,
                "user_id": self.user_id,
                "timestamp": timestamp,
                "type": "user_query"
            }
        )

        agent_doc = Document(
            page_content=agent_response,
            metadata={
                "interaction_id": interaction_id,
                "conversation_id": conversation_id,
                "user_id": self.user_id,
                "timestamp": timestamp,
                "type": "agent_response"
            }
        )

        # Add documents to vector store
        self.vector_store.add_documents([user_doc, agent_doc])

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

        # Note: persist() is no longer needed in Chroma 0.4.x as docs are automatically persisted
        # self.vector_store.persist()

        return interaction_id

    def get_relevant_history(self, query: str, k: int = 5) -> List[Dict[str, str]]:
        """Retrieve relevant conversation history based on semantic similarity.

        Args:
            query: The query to find relevant history for
            k: Number of relevant interactions to retrieve

        Returns:
            List of relevant interactions as dictionaries
        """
        # Search for relevant documents
        docs_and_scores = self.vector_store.similarity_search_with_score(query, k=k)

        # Group by interaction_id to get complete interactions
        interactions_map = {}
        for doc, score in docs_and_scores:
            interaction_id = doc.metadata.get("interaction_id")
            if interaction_id not in interactions_map:
                interactions_map[interaction_id] = {
                    "score": score,
                    "user_query": None,
                    "agent_response": None,
                    "timestamp": doc.metadata.get("timestamp"),
                    "conversation_id": doc.metadata.get("conversation_id")
                }

            if doc.metadata.get("type") == "user_query":
                interactions_map[interaction_id]["user_query"] = doc.page_content
            elif doc.metadata.get("type") == "agent_response":
                interactions_map[interaction_id]["agent_response"] = doc.page_content

        # Filter out incomplete interactions and sort by score
        complete_interactions = [
            interaction for interaction in interactions_map.values()
            if interaction["user_query"] and interaction["agent_response"]
        ]
        complete_interactions.sort(key=lambda x: x["score"])

        # Format the interactions
        return [
            {
                "user_query": interaction["user_query"],
                "agent_response": interaction["agent_response"],
                "conversation_id": interaction["conversation_id"],
                "timestamp": interaction["timestamp"]
            }
            for interaction in complete_interactions
        ]

    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get the complete history of a specific conversation.

        Args:
            conversation_id: ID of the conversation to retrieve

        Returns:
            List of interactions in the conversation
        """
        if conversation_id not in self.metadata["conversations"]:
            return []

        # Get interaction IDs for the conversation
        interaction_ids = [
            interaction["interaction_id"]
            for interaction in self.metadata["conversations"][conversation_id]["interactions"]
        ]

        # Query vector store for each interaction
        interactions = []
        for interaction_id in interaction_ids:
            docs = self.vector_store.get(
                where={"interaction_id": interaction_id}
            )

            user_query = None
            agent_response = None
            timestamp = None

            for doc in docs:
                # Handle both Document objects and dictionaries
                if hasattr(doc, 'metadata'):
                    # It's a Document object
                    metadata = doc.metadata
                    content = doc.page_content
                elif isinstance(doc, dict):
                    # It's a dictionary
                    metadata = doc.get('metadata', {})
                    content = doc.get('page_content', '')
                else:
                    # Skip if it's neither
                    continue

                # Extract type from metadata
                doc_type = metadata.get("type") if isinstance(metadata, dict) else None

                if doc_type == "user_query":
                    user_query = content
                    timestamp = metadata.get("timestamp") if isinstance(metadata, dict) else None
                elif doc_type == "agent_response":
                    agent_response = content

            if user_query and agent_response:
                interactions.append({
                    "user_query": user_query,
                    "agent_response": agent_response,
                    "timestamp": timestamp
                })

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

        # Get interaction IDs for the conversation
        interaction_ids = [
            interaction["interaction_id"]
            for interaction in self.metadata["conversations"][conversation_id]["interactions"]
        ]

        # Delete documents from vector store
        for interaction_id in interaction_ids:
            self.vector_store.delete(
                where={"interaction_id": interaction_id}
            )

        # Delete from metadata
        del self.metadata["conversations"][conversation_id]
        self._save_metadata()

        # Note: persist() is no longer needed in Chroma 0.4.x as docs are automatically persisted
        # self.vector_store.persist()

        return True
