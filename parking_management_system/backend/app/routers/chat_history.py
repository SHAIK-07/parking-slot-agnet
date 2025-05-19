from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uuid

from ..database.database import get_db
from ..memory.file_chat_history import FileChatHistory

router = APIRouter(
    prefix="/chat-history",
    tags=["chat-history"],
    responses={404: {"description": "Not found"}},
)

# Request and response models
class ConversationCreate(BaseModel):
    name: str

class ConversationRename(BaseModel):
    name: str

class ConversationResponse(BaseModel):
    conversation_id: str
    name: str
    created_at: str
    updated_at: str
    interaction_count: int

class InteractionResponse(BaseModel):
    user_query: str
    agent_response: str
    timestamp: str

# Helper function to get chat history
def get_chat_history(user_id: str):
    return FileChatHistory(user_id=user_id)

@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    x_user_id: str = Header(..., description="User ID for conversation tracking"),
    db: Session = Depends(get_db)
):
    """List all conversations for the user."""
    try:
        vector_chat = get_chat_history(user_id=x_user_id)
        conversations = vector_chat.list_conversations()
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing conversations: {str(e)}")

@router.post("/conversations", response_model=ConversationResponse)
def create_conversation(
    conversation: ConversationCreate,
    x_user_id: str = Header(..., description="User ID for conversation tracking"),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    try:
        print(f"Creating new conversation for user {x_user_id} with name: {conversation.name}")
        vector_chat = get_chat_history(user_id=x_user_id)
        conversation_id = str(uuid.uuid4())

        # Add a dummy interaction to create the conversation
        vector_chat.add_interaction(
            conversation_id=conversation_id,
            user_query="New conversation",
            agent_response="Welcome to the Parking Management System! How can I assist you today?",
            conversation_name=conversation.name
        )

        # Get the created conversation
        conversations = vector_chat.list_conversations()
        for conv in conversations:
            if conv["conversation_id"] == conversation_id:
                print(f"Successfully created conversation with ID: {conversation_id}")
                return conv

        raise HTTPException(status_code=500, detail="Failed to create conversation")
    except Exception as e:
        print(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")

@router.get("/conversations/{conversation_id}", response_model=List[InteractionResponse])
def get_conversation_history(
    conversation_id: str,
    x_user_id: str = Header(..., description="User ID for conversation tracking"),
    db: Session = Depends(get_db)
):
    """Get the complete history of a specific conversation."""
    try:
        print(f"Getting conversation history for user {x_user_id}, conversation {conversation_id}")
        vector_chat = get_chat_history(user_id=x_user_id)
        history = vector_chat.get_conversation_history(conversation_id)

        if not history:
            print(f"No history found for conversation {conversation_id}")
            # Return empty list instead of raising an error
            return []

        print(f"Found {len(history)} messages in conversation {conversation_id}")
        return history
    except Exception as e:
        print(f"Error getting conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting conversation history: {str(e)}")

@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
def rename_conversation(
    conversation_id: str,
    conversation: ConversationRename,
    x_user_id: str = Header(..., description="User ID for conversation tracking"),
    db: Session = Depends(get_db)
):
    """Rename a conversation."""
    try:
        vector_chat = get_chat_history(user_id=x_user_id)
        success = vector_chat.rename_conversation(conversation_id, conversation.name)

        if not success:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

        # Get the updated conversation
        conversations = vector_chat.list_conversations()
        for conv in conversations:
            if conv["conversation_id"] == conversation_id:
                return conv

        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renaming conversation: {str(e)}")

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    x_user_id: str = Header(..., description="User ID for conversation tracking"),
    db: Session = Depends(get_db)
):
    """Delete a conversation and all its interactions."""
    try:
        vector_chat = get_chat_history(user_id=x_user_id)
        success = vector_chat.delete_conversation(conversation_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

        return {"message": f"Conversation {conversation_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

@router.get("/search", response_model=List[InteractionResponse])
def search_conversations(
    query: str,
    limit: int = 5,
    x_user_id: str = Header(..., description="User ID for conversation tracking"),
    db: Session = Depends(get_db)
):
    """Search for relevant interactions across all conversations."""
    try:
        vector_chat = get_chat_history(user_id=x_user_id)
        results = vector_chat.get_relevant_history(query, k=limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching conversations: {str(e)}")
