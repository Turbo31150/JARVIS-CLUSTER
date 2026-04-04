"""Utility functions for JARVIS CLUSTER."""

import logging
import os
import re
from typing import Any, Optional


def log(
    message: str,
    level: str = "INFO",
    component: str = "",
) -> None:
    """Log a message with optional component tagging."""
    if not component:
        logger = logging.getLogger("jarvis")
    else:
        logger = logging.getLogger(f"jarvis.{component}")
    
    level_upper = level.upper()
    if level_upper == "INFO":
        logger.info(message)
    elif level_upper == "WARNING":
        logger.warning(message)
    elif level_upper == "ERROR":
        logger.error(message)
    elif level_upper == "DEBUG":
        logger.debug(message)


def ensure_dir(path: str) -> None:
    """Ensure directory exists, create if not."""
    os.makedirs(path, exist_ok=True)


def safe_eval(
    expression: str,
    context: Optional[dict] = None,
) -> tuple[bool, Any, Optional[str]]:
    """Safely evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression as string
        context: Optional variable context for evaluation
        
    Returns:
        Tuple of (success, result or error, error_message if failed)
    """
    try:
        # Remove whitespace
        expr = " ".join(expression.split())
        
        # Replace common words with safe operators
        safe_expr = re.sub(r"sqrt\(", "math.sqrt(", expr)
        safe_expr = re.sub(r"log\(", "math.log10(", safe_expr)
        safe_expr = re.sub(r"sin\(", "math.sin(", safe_expr)
        safe_expr = re.sub(r"cos\(", "math.cos(", safe_expr)
        safe_expr = re.sub(r"tan\(", "math.tan(", safe_expr)
        
        # Evaluate with limited context
        if not context:
            context = {}
        
        result = eval(safe_expr, {"__builtins__": {}}, {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "pow": pow,
            "math": __import__("math"),
            **{k: str(v) for k, v in context.items() if isinstance(v, (int, float))},
        })
        
        # Convert result to string if it's a numeric type
        if isinstance(result, (int, float)):
            return True, str(result), None
        
        return True, result, None
        
    except Exception as e:
        return False, None, f"Evaluation error: {str(e)}"


def sanitize_input(text: str) -> str:
    """Sanitize input text to remove potentially dangerous characters."""
    # Remove null bytes and control characters
    if not isinstance(text, str):
        return ""
    
    # Remove null bytes
    sanitized = text.replace("\x00", "")
    
    # Remove control characters except newlines and tabs
    sanitized = "".join(
        c for c in sanitized 
        if ord(c) >= 32 or c in "\n\t\r"
    )
    
    return sanitized


def parse_number(value: Any, default: float = 0.0) -> float:
    """Parse a numeric value from various input types."""
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        try:
            return float(" ".join(value.split()))
        except ValueError:
            return default
    
    return default


def truncate_string(text: str, max_length: int = 1000) -> str:
    """Truncate a string to maximum length with ellipsis."""
    if len(text) <= max_length:
        return text
    
    words = text.split(" ")
    truncated = " ".join(words[:max_length // 5]) + "..."
    
    return truncated


# Logger singleton
logger = logging.getLogger("jarvis.utils")
