# Parking Management System Backend

This is the backend for the Parking Management System, which uses Groq with the Llama-3.3-70b-versatile model for the AI assistant.

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. No need to set up a separate database as we're using SQLite, which is a file-based database.

5. The `.env` file is already configured to use SQLite and includes the Groq API key.

6. Initialize the database with sample data:
   ```
   python init_db.py
   ```

7. Run the FastAPI application:
   ```
   python run.py
   ```

## Using Groq with Llama-3.3-70b-versatile

This backend uses Groq with the Llama-3.3-70b-versatile model for the AI assistant. The key components are:

1. **Direct Groq API Integration**: The `agent.py` file uses the `requests` library to directly call the Groq API, avoiding complex dependencies.

2. **Simple File-based Memory**: We use a simple file-based JSON storage for chat memory to avoid compilation issues with vector stores.

3. **SQLite Database**: We use SQLite as a file-based database to avoid the need for a separate database server.

4. **Environment Variables**: The Groq API key is stored in the `.env` file.

## API Endpoints

- `GET /`: Welcome message
- `POST /chat/`: Chat endpoint for the AI assistant
- `GET /health`: Health check endpoint

## Testing the API

You can test the API using curl:

```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -H "X-User-ID: 1" \
  -d '{"query": "Show me available parking slots for tomorrow"}'
```

Or using the frontend application.

## Customizing the Model

If you want to use a different model from Groq, you can change the `model_name` parameter in the `ParkingAgent` class in `agent.py`. Available models include:

- llama-3.3-70b-versatile
- llama-3.1-70b-versatile
- llama-3.1-8b-versatile
- mixtral-8x7b-32768
- gemma-7b-it

## Troubleshooting

If you encounter any issues with the Groq API, check the following:

1. Make sure the API key is correct in the `.env` file.
2. Verify that the model name is correct.
3. Check the Groq API status at https://status.groq.com/.
