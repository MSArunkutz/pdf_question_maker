import uuid
import time
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from utils import logger, request_id_ctx_var
from services import process_pdf_and_generate_questions, ServiceError

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Server starting up...")
    yield
    logger.info("Server shutting down...")

app = FastAPI(lifespan=lifespan)

# CORS (Allowing * for dev convenience as per implicit requirement to "connect")
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
        # Global fallback for unhandled exceptions
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "requestId": request_id
            }
        )

@app.post("/api/generate-questions")
async def generate_questions(file: UploadFile = File(...)):
    request_id = request_id_ctx_var.get()
    
    # Check content type immediately
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
         logger.warning(f"Rejected content-type: {file.content_type}")
         return JSONResponse(
             status_code=400,
             content={
                 "error": "Invalid file type. Only PDF is supported.",
                 "requestId": request_id
             }
         )

    try:
        content = await file.read()
        logger.info(f"Received file: {file.filename}, Size: {len(content)} bytes")
        
        questions = process_pdf_and_generate_questions(content, file.filename)
        
        logger.info(f"Successfully generated {len(questions)} questions")
        return {
            "questions": questions,
            "requestId": request_id
        }
        
    except ServiceError as e:
        logger.warning(f"Service validation failed: {e.message}")
        return JSONResponse(
            status_code=400,
            content={
                "error": e.message,
                "requestId": request_id
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "An unexpected error occurred processing the file.",
                "requestId": request_id
            }
        )
