# FoundersAI Backend
##
This repository contains the backend service for FoundersAI, built with FastAPI. The service provides an API to interact with a custom Large Language Model (LLM).

## Features

- **FastAPI Framework**: High-performance, easy-to-use web framework for building APIs.
- **Custom LLM Integration**: Connects to any self-hosted or third-party LLM via an HTTP API.
- **JWT Authentication**: User signup/login with hashed passwords and bearer JWT tokens.
- **Scalable Architecture**: Organized into modular components (core, services, models, api) for easy maintenance and expansion.
- **Asynchronous Support**: Built with `async` and `await` for handling concurrent requests efficiently.
- **Dependency Injection**: Uses FastAPI's dependency injection system for managing resources like database connections and HTTP clients.

---

## Project Structure

The project follows a clean, modular architecture:

```
FoundersAI_backend/
├── app/
│   ├── api/          # API endpoints (routers)
│   ├── core/         # Core logic, settings, and configuration
│   ├── models/       # Pydantic models for data validation
│   ├── services/     # Business logic (e.g., LLM communication)
│   └── main.py       # Main FastAPI application entry point
├── .env              # Environment variables (local, not committed)
├── .gitignore        # Files to be ignored by Git
├── requirements.txt  # Python dependencies
├── Dockerfile        # Docker configuration for containerization
└── README.md         # This file
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- An accessible API endpoint for your custom LLM

### Installation & Setup

1.  **Clone the repository:**

    ```
    git clone <your-repository-url>
    cd FoundersAI_backend
    ```

2.  **Create and activate a virtual environment:**

    ```
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the required dependencies:**

    ```
    pip install -r requirements.txt
    ```

4.  **Configure environment variables:**
    Create a `.env` file in the root directory (if it doesn't exist) and include at least:
    ```ini
    MONGO_URI=mongodb+srv://<user>:<pass>@<cluster>/<db>?retryWrites=true&w=majority
    DB_NAME=founders_ai_db
    GOOGLE_API_KEY=your_gemini_api_key
    JWT_SECRET_KEY=super_long_random_secret
    ACCESS_TOKEN_EXPIRE_MINUTES=60
    FRONTEND_ORIGINS=http://localhost:5174,http://localhost:5173,https://founders-ai.vercel.app
    ```
    Optional: adjust token expiry as needed.

### Running the Application

To run the development server, use the following command from the root directory:

```
uvicorn app.main:app --reload
```

The server will start, and the API will be accessible at `http://127.0.0.1:8000`.

---

## API Usage

The API provides interactive documentation via Swagger UI and ReDoc.

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Example Request

### Auth Endpoints

Base path: `/auth`

1. Signup
```
POST /auth/signup
{
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "StrongPass123!"
}
```
Response:
```
{
    "id": "...",
    "name": "Jane Doe",
    "email": "jane@example.com",
    "created_at": "2024-01-01T12:00:00Z"
}
```

2. Login
```
POST /auth/login
{
    "email": "jane@example.com",
    "password": "StrongPass123!"
}
```
Response:
```
{
    "access_token": "<jwt>",
    "token_type": "bearer"
}
```

3. Current User
```
GET /auth/me
Authorization: Bearer <jwt>
```

### Example curl Login
```
curl -X POST http://127.0.0.1:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"jane@example.com","password":"StrongPass123!"}'
```

Use the returned `access_token` as a Bearer token for protected endpoints.

### Security Notes
- Emails stored in lowercase; unique index enforced.
- Passwords hashed with bcrypt via Passlib.
- JWT includes standard claims plus user email & name.
- Configure `JWT_SECRET_KEY` with a long random value (32+ chars).
- Set `FRONTEND_ORIGINS` (comma-separated) to control allowed CORS origins. If not set, sensible defaults including ports 5173/5174 are used.

### LLM Example (existing)
Refer to `/recommend` endpoint to query Gemini model.
