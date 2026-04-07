import re
from typing import List, Optional
from datetime import datetime


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: The text to truncate
        max_length: Maximum length before truncation
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def word_count(text: str) -> int:
    """
    Count words in a text string.
    
    Args:
        text: The text to count words in
        
    Returns:
        Number of words
    """
    if not text or not text.strip():
        return 0
    return len(text.strip().split())


def contains_vague_markers(text: str, markers: Optional[List[str]] = None) -> bool:
    """
    Check if text contains vague/marketing language markers.
    
    Args:
        text: The text to check
        markers: List of vague markers to look for (uses defaults if None)
        
    Returns:
        True if any marker is found
    """
    if markers is None:
        markers = [
            "explain",
            "tell me about",
            "help me with",
            "what do you think",
            "derive",
            "analyze",
            "strategy",
            "model",
            "volatility",
            "options",
            "pricing",
        ]
    
    lower = text.lower()
    return any(marker in lower for marker in markers)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Args:
        filename: The string to sanitize
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized or "unnamed"


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime as ISO timestamp string.
    
    Args:
        dt: Datetime to format (uses now if None)
        
    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def estimate_tokens(text: str) -> int:
    """
    Roughly estimate the number of tokens in text.
    Uses a simple heuristic: ~4 characters per token on average.
    
    Args:
        text: The text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return len(text) // 4


def clean_markdown_code_blocks(text: str) -> str:
    """
    Clean up markdown code blocks by removing language specifiers.
    
    Args:
        text: Text potentially containing markdown code blocks
        
    Returns:
        Cleaned text
    """
    # Remove ```language and ``` markers
    cleaned = re.sub(r'```\w*\n?', '', text)
    cleaned = re.sub(r'```', '', cleaned)
    return cleaned.strip()


def split_into_chunks(text: str, chunk_size: int = 1000) -> List[str]:
    """
    Split text into chunks of approximately equal size.
    
    Args:
        text: Text to split
        chunk_size: Target size for each chunk
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        current_chunk.append(word)
        current_size += len(word) + 1  # +1 for space
        
        if current_size >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_size = 0
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks
