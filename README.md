# PDF Question Maker

A modern web application that generates conceptual questions from PDF documents using Google's Gemini AI.

## Features

- **Secure PDF Processing**: Validates file size (10MB limit), magic bytes, and encryption.
- **AI-Powered Questions**: Uses Gemini AI to generate 5 high-quality conceptual questions.
- **Modern UI**: A responsive, dark-themed React frontend built with Vite.
- **Developer Friendly**: FastAPI backend with structured logging, type safety (Pydantic), and thread-pool offloading for blocking tasks.

## Tech Stack

- **Frontend**: React, Vite, Vanilla CSS.
- **Backend**: Python, FastAPI, Gemini API, PyPDF.
- **Deployment**: Configurable via environment variables.

## Getting Started

### Backend Setup

1. Navigate to `backend/`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example`:
   ```bash
   GEMINI_API_KEY=your_google_ai_key
   GEMINI_MODEL=gemini-2.5-flash
   ```
4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to `frontend/`.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## Design Choices & Tradeoffs

- **Security**: 
    - Early rejection for large files (>10MB) to prevent memory exhaustion.
    - Sanitized `ServiceError` messages to prevent leaking internal library details or stack traces to the client.
    - Shallow guards for Content-Type in the API layer, with deep validation (magic bytes) in the service layer.
- **Performance**:
    - Blocking I/O (PDF parsing) and AI calls are offloaded to a thread pool using `anyio.to_thread` to keep the FastAPI event loop responsive.
- **Reliability**:
    - AI generation uses retries with exponential backoff via `tenacity`.
    - Fallback dummy questions are provided only if the API key is missing (dev mode). Real API failures are reported to the user.
- **Regex Sanitization**:
    - We intentionally preserve double newlines to maintain paragraph structure, which helps the AI understand document context better.

## Logging

The application uses a structured logger with Request ID tracking. All service-level errors are logged with full stack traces internally for debugging, while users receive generic, safe error messages.
