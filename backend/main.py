import uuid
import time
import anyio
from typing import List
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel

from utils import logger, request_id_ctx_var
from services import process_pdf_and_generate_questions, ServiceError

# Hard limit for security and stability
# Enforcement happens via best-effort header check and mandatory post-read check.
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class QuestionResponse(BaseModel):
    questions: List[str]
    requestId: str

class ErrorResponse(BaseModel):
    error: str
    requestId: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting up...")
    yield
    logger.info("Server shutting down...")

app = FastAPI(lifespan=lifespan)

# NOTE: Wide-open CORS for local development only. 
# For production, this MUST be restricted to specific origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request_id_ctx_var.set(request_id)
    
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request completed in {process_time:.2f}s - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        # Global fallback formatted to match detail structure of HTTPException
        return JSONResponse(
            status_code=500,
            content={
                "detail": {
                    "error": "Internal Server Error",
                    "requestId": request_id
                }
            }
        )

@app.post("/api/generate-questions", response_model=QuestionResponse)
async def generate_questions(file: UploadFile = File(...)):
    request_id = request_id_ctx_var.get()
    
    # 1. Quick Content-Type / Extension Check (Initial Rejection)
    # NOTE: Shallow guard only; real validation (magic bytes) happens in service layer.
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
         logger.warning(f"Rejected content-type: {file.content_type}")
         raise HTTPException(
             status_code=400,
             detail={"error": "Invalid file type. Only PDF is supported.", "requestId": request_id}
         )

    # 2. File Size Limit (Early Rejection)
    # NOTE: .size is best-effort only; real enforcement happens after file.read().
    content_length = file.size if hasattr(file, 'size') else None
    if content_length and content_length > MAX_FILE_SIZE:
        logger.warning(f"Rejected file size (from header): {content_length} bytes")
        raise HTTPException(
            status_code=413, # Request Entity Too Large
            detail={"error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.", "requestId": request_id}
        )

    try:
        # 3. Read content with size check in case header was missing or spoofed
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            logger.warning(f"Rejected file size (after read): {len(content)} bytes")
            raise HTTPException(
                status_code=413,
                detail={"error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB.", "requestId": request_id}
            )
            
        logger.info(f"Received file: {file.filename}, Size: {len(content)} bytes")
        
        # 4. Offload blocking I/O and AI calls to a thread pool
        questions = await anyio.to_thread.run_sync(
            process_pdf_and_generate_questions, content, file.filename
        )
        
        logger.info(f"Successfully generated {len(questions)} questions")
        return QuestionResponse(
            questions=questions,
            requestId=request_id
        )
        
    except ServiceError as e:
        logger.warning(f"Service validation failed: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={"error": e.message, "requestId": request_id}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "An unexpected error occurred processing the file.", "requestId": request_id}
        )
