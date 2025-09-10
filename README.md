# FoundersAI Backend
##
This repository contains the backend service for FoundersAI, built with FastAPI. The service provides an API to interact with a custom Large Language Model (LLM).

## Features

- **FastAPI Framework**: High-performance, easy-to-use web framework for building APIs.
- **Custom LLM Integration**: Connects to any self-hosted or third-party LLM via an HTTP API.
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
    Create a `.env` file in the root directory by copying the example file:
    ```
    cp .env.example .env
    ```
    Open the `.env` file and set the `LLM_API_URL` to your model's endpoint:
    ```
    LLM_API_URL="http://your-llm-api-host:port/generate"
    ```

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

You can test the LLM endpoint by sending a `POST` request to `/api/v1/llm/generate-response`.

**Using `curl`:**

```
curl -X POST "http://127.0.0.1:8000/api/v1/llm/generate-response" \
-H "Content-Type: application/json" \
-d '{"text": "Explain the importance of APIs in modern software."}'
```
