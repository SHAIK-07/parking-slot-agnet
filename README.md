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

## Installation

### Prerequisites

- Python 3.9+
- Node.js 16+
- MySQL (or SQLite for development)
- Groq API key

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/parking-management-system.git
   cd parking-management-system
   ```

2. Navigate to the backend directory:
   ```bash
   cd parking_management_system/backend
   ```

3. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file with the following variables:
   ```
   DATABASE_URL=sqlite:///./parking.db
   GROQ_API_KEY=your_groq_api_key
   ```

6. Initialize the database:
   ```bash
   python init_db.py
   ```

7. Start the backend server:
   ```bash
   python run.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```



2. Start the development server:
   ```bash
   python serve.py
   ```

3. Open your browser and navigate to `http://localhost:3000`

## Usage

### Chat with the AI Assistant

1. Log in with your user ID
2. Type your query in the chat interface, for example:
   - "Show me available parking slots for tomorrow"
   - "What are the parking rates?"
   - "Book a parking slot for my car"
   - "Cancel my booking"
   - "Show me my booking history"

## API Endpoints

- `GET /`: Welcome message
- `POST /chat/`: Chat endpoint for the AI assistant
- `GET /health`: Health check endpoint

## Contributing

We welcome contributions to the Parking Management System! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Contribution Guidelines

- Follow the existing code style and conventions
- Write clear commit messages
- Add unit tests for new features
- Update documentation as needed
- Make sure all tests pass before submitting a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Groq for providing the LLM API
- HuggingFace for the sentence-transformers models
- All contributors who have helped shape this project
