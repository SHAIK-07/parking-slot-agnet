# Parking Management System

A modular parking management system with an AI-powered chat assistant that helps users find, book, and manage parking spaces. The system uses Groq with the Llama-3.3-70b-versatile model for the AI assistant.

## Features

- **AI Chat Assistant**: Natural language interface for all parking operations powered by Groq's Llama-3.3-70b-versatile model
- **Database Management**: MySQL schema for users, vehicles, parking slots, bookings, and payments
- **Custom Tools**: Modular Python functions for parking operations
- **FastAPI Backend**: RESTful API with agent integration
- **Chat Memory**: Conversation history with vector database storage using HuggingFace embeddings
- **React Frontend**: Modern UI with Tailwind CSS

## Project Structure

```
parking_management_system/
├── backend/
│   ├── app/
│   │   ├── database/       # SQLAlchemy models and CRUD operations
│   │   ├── tools/          # Custom tools for parking operations
│   │   ├── agent/          # Langchain agent setup
│   │   ├── memory/         # Chat memory management
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt
│   └── .env                # Environment variables
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/     # React components
    │   ├── styles/         # Tailwind CSS
    │   ├── App.jsx
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd parking_management_system/backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. No need to set up a separate database as we're using SQLite, which is a file-based database.

6. The `.env` file is already configured with the Groq API key.

7. Run the FastAPI application:
   ```
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd parking_management_system/frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

4. Open your browser and navigate to `http://localhost:3000`

## API Endpoints

- `GET /`: Welcome message
- `POST /chat/`: Chat endpoint for the AI assistant
- `GET /health`: Health check endpoint

## Usage Examples

### Chat with the AI Assistant

1. Log in with your user ID
2. Type your query in the chat interface, for example:
   - "Show me available parking slots for tomorrow"
   - "What are the parking rates?"
   - "Book a parking slot for my car"
   - "Cancel my booking"
   - "Show me my booking history"

## Technologies Used

- **Backend**: Python, FastAPI, SQLAlchemy, Langchain, Groq
- **LLM**: Llama-3.3-70b-versatile via Groq API
- **Embeddings**: HuggingFace sentence-transformers
- **Frontend**: React, Vite, Tailwind CSS
- **Database**: SQLite (file-based)
- **Chat Memory**: Simple file-based JSON storage

## License

MIT
