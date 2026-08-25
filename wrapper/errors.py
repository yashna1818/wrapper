"""
Error normalization module.
Categorizes heterogeneous application, network, and HTTP errors into standardized
GenAI failure categories without letting worker exceptions crash Locust load runs.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any

class ErrorCategory(str, Enum):
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    AUTH_ERROR = "AUTH_ERROR"
    SERVER_ERROR = "SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MODEL_ERROR = "MODEL_ERROR"
    QUEUE_TIMEOUT = "QUEUE_TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    UNKNOWN = "UNKNOWN"

@dataclass
class NormalizedError:
    category: ErrorCategory
    status_code: Optional[int]
    message: str
    raw_error: Optional[Any] = None

class ErrorNormalizer:
    @staticmethod
    def normalize(error: Any, status_code: Optional[int] = None) -> NormalizedError:
        """
        Normalizes HTTP status code, exception type, or error message into ErrorCategory.
        """
        msg = str(error) if error else "Unknown error"
        
        # Check HTTP status codes first if provided
        if status_code is not None:
            if status_code == 429:
                return NormalizedError(ErrorCategory.RATE_LIMIT, status_code, msg, error)
            elif status_code in (401, 403):
                return NormalizedError(ErrorCategory.AUTH_ERROR, status_code, msg, error)
            elif status_code == 408 or status_code == 504:
                return NormalizedError(ErrorCategory.TIMEOUT, status_code, msg, error)
            elif status_code in (400, 422):
                return NormalizedError(ErrorCategory.VALIDATION_ERROR, status_code, msg, error)
            elif status_code in (502, 503):
                return NormalizedError(ErrorCategory.SERVER_ERROR, status_code, msg, error)
            elif status_code >= 500:
                return NormalizedError(ErrorCategory.SERVER_ERROR, status_code, msg, error)

        # Inspect error message or exception class name
        lower_msg = msg.lower()
        if "timeout" in lower_msg or "timed out" in lower_msg:
            return NormalizedError(ErrorCategory.TIMEOUT, status_code, msg, error)
        elif "rate limit" in lower_msg or "429" in lower_msg or "too many requests" in lower_msg:
            return NormalizedError(ErrorCategory.RATE_LIMIT, status_code, msg, error)
        elif "unauthorized" in lower_msg or "forbidden" in lower_msg or "auth" in lower_msg:
            return NormalizedError(ErrorCategory.AUTH_ERROR, status_code, msg, error)
        elif "queue" in lower_msg and "timeout" in lower_msg:
            return NormalizedError(ErrorCategory.QUEUE_TIMEOUT, status_code, msg, error)
        elif "model" in lower_msg or "cuda" in lower_msg or "out of memory" in lower_msg or "oom" in lower_msg:
            return NormalizedError(ErrorCategory.MODEL_ERROR, status_code, msg, error)
        elif "connection refused" in lower_msg or "network" in lower_msg or "dns" in lower_msg:
            return NormalizedError(ErrorCategory.NETWORK_ERROR, status_code, msg, error)

        return NormalizedError(ErrorCategory.UNKNOWN, status_code, msg, error)
