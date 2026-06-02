from abc import ABC, abstractmethod
from .schemas import ParseResult

class ParseError(Exception):
    """Custom exception for parsing errors."""
    def __init__(self, message: str, file_type: str | None = None, reason: str | None = None):
        super().__init__(message)
        self.file_type = file_type
        self.reason = reason

class BaseParser(ABC):
    """Abstract base class for all resume parsers."""

    @abstractmethod
    def parse(self, file_bytes: bytes) -> ParseResult:
        """Parse the given file bytes and return a ParseResult."""
        pass

    def validate_size(self, file_bytes: bytes, max_mb: int = 10) -> None:
        """Validate that the file size is within the allowed limit."""
        if len(file_bytes) > max_mb * 1024 * 1024:
            raise ParseError(f"File size exceeds {max_mb}MB limit", reason="file_too_large")

    def calculate_special_chars_ratio(self, text: str) -> float:
        """Calculate the ratio of non-ASCII characters in the text."""
        if not text:
            return 0.0
        non_ascii = len([c for c in text if ord(c) > 127])
        return non_ascii / len(text)
