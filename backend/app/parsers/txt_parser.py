import re
from .base_parser import BaseParser, ParseError
from .schemas import ParseResult, ATSFlags

class TXTParser(BaseParser):
    """Parser for plain text files."""

    def parse(self, file_bytes: bytes) -> ParseResult:
        self.validate_size(file_bytes)
        
        try:
            # Try UTF-8 first
            try:
                text = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback to latin-1
                text = file_bytes.decode('latin-1')

            # Normalize line endings and strip excessive whitespace
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = text.strip()

            ats_flags = ATSFlags()
            ats_flags.special_chars_ratio = self.calculate_special_chars_ratio(text)

            return ParseResult(
                text=text,
                word_count=len(text.split()),
                page_count=1,
                ats_flags=ats_flags,
                parser_used="txt"
            )

        except Exception as e:
            raise ParseError(f"TXT parsing failed: {str(e)}", file_type="TXT")
