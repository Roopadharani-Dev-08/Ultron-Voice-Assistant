import re
from datetime import datetime

def clean_text(text: str) -> str:
    """
    Cleans the input text for easier matching (lowercasing, removing extra whitespaces,
    and stripping basic punctuation).
    """
    if not text:
        return ""
    text = text.lower().strip()
    # Remove standard punctuation like periods, question marks, exclamation marks at the end
    text = re.sub(r'[?.!,]', '', text)
    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_current_time() -> str:
    """
    Returns the current time formatted nicely, e.g., '08:35 PM'.
    """
    return datetime.now().strftime("%I:%M %p")

def get_current_date() -> str:
    """
    Returns the current date formatted nicely, e.g., 'Sunday, July 19, 2026'.
    """
    return datetime.now().strftime("%A, %B %d, %Y")

def log(tag: str, message: str) -> None:
    """
    Prints a timestamped log to console for debugging.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{tag}] {message}", flush=True)
