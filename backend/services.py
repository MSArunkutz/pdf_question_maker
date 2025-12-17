import io
import json
import logging
import os
import re
from typing import List, Optional
import pypdf
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

logger = logging.getLogger("pdf_question_maker")

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    logger.info("Gemini configured successfully")
else:
    logger.warning("Gemini configuration failed")


class ServiceError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

def validate_pdf(file_content: bytes, filename: str) -> str:
    # 1. Size Check (Hard Reject > 10MB)
    if len(file_content) > 10 * 1024 * 1024:
        raise ServiceError("File size exceeds 10MB limit")

    # 2. Magic Bytes / Extension Check
    if not filename.lower().endswith('.pdf'):
        raise ServiceError("File must be a PDF")
    
    if not file_content.startswith(b'%PDF'):
        raise ServiceError("Invalid PDF file structure")

    try:
        reader = pypdf.PdfReader(io.BytesIO(file_content))
        
        # 3. Encryption Check
        if reader.is_encrypted:
            raise ServiceError("Encrypted PDFs are not supported")
            
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
            
        # 4. Empty / Image-only Check
        if len(text.strip()) == 0:
            raise ServiceError("This PDF has no readable text (likely image-only)")
            
        # 5. Soft Reject (Text too small)
        if len(text.strip()) < 500:
             raise ServiceError("Text content too short (minimum 500 characters)")
             
        return text
        
    except pypdf.errors.PdfReadError:
        raise ServiceError("Corrupt or invalid PDF file")
    except Exception as e:
        if isinstance(e, ServiceError):
            raise e
        logger.error(f"Error processing PDF: {str(e)}")
        raise ServiceError(f"Failed to process PDF: {str(e)}")

def sanitize_text(text: str) -> str:
    # Collapse newlines and whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Cap max chars
    return text[:25000]

@retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
def generate_questions_with_gemini(text: str) -> List[str]:
    if not api_key:
        logger.warning("No GEMINI_API_KEY found. Using dummy fallback.")
        return get_dummy_questions()

    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    You are a strict question generation bot.
    Task: Generate exactly 5 conceptual questions based on the provided text.
    
    Input Text:
    {text}
    
    Constraints:
    - Output MUST be a valid JSON array of strings.
    - Exactly 5 items.
    - No numbering, no prefixes in the strings.
    - No answers, only questions.
    - No markdown formatting (like ```json), just the raw JSON string.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Clean potential markdown
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        questions = json.loads(content)
        
        # Validation
        if not isinstance(questions, list):
            raise ValueError("Output is not a list")
        if len(questions) != 5:
            raise ValueError(f"Expected 5 questions, got {len(questions)}")
        if not all(isinstance(q, str) and q.strip() for q in questions):
            raise ValueError("Invalid question format")
            
        return questions
        
    except Exception as e:
        logger.error(f"Gemini generation failed: {str(e)}")
        raise e # Trigger retry

def get_dummy_questions() -> List[str]:
    return [
        "What is the primary function of the mitochondrion in a cell?",
        "Explain the difference between mitosis and meiosis.",
        "How does photosynthesis convert light energy into chemical energy?",
        "Describe the structure of DNA and its role in genetic inheritance.",
        "What are the three main types of rock and how are they formed?"
    ]

def process_pdf_and_generate_questions(file_content: bytes, filename: str) -> List[str]:
    # 1. Validate & Extract
    raw_text = validate_pdf(file_content, filename)
    
    # 2. Sanitize
    clean_text = sanitize_text(raw_text)
    
    # 3. Generate
    try:
        return generate_questions_with_gemini(clean_text)
    except Exception:
        logger.error("AI Generation failed after retries. Returning dummy data for robustness.")
        return get_dummy_questions()
