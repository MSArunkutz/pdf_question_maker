import logging
import sys
import contextvars
from typing import Optional

request_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("request_id", default=None)

def get_request_id() -> str:
    return request_id_ctx_var.get() or "SYSTEM"

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True

def setup_logger():
    logger = logging.getLogger("pdf_question_maker")
    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [RequestID: %(request_id)s] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addFilter(RequestIdFilter())
    logger.addHandler(handler)
    return logger

logger = setup_logger()
