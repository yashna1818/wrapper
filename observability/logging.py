"""
Structured JSON Logger.
Formats log messages with test_run_id, synthetic context, and application metadata.
"""

import json
import logging
import sys
from typing import Any, Dict
from wrapper.context import get_current_context

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ctx = get_current_context()
        log_entry: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "test_run_id": ctx.test_run_id if ctx else None,
            "application": ctx.application if ctx else None,
            "synthetic": ctx.synthetic if ctx else True,
            "virtual_user_id": ctx.virtual_user_id if ctx else None,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_structured_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("genai_load_framework")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger
