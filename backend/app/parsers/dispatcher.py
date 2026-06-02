from .base_parser import ParseError
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .txt_parser import TXTParser
from .schemas import ParseResult

class ParserDispatcher:
    """Dispatches parsing tasks to the appropriate parser based on file magic bytes."""

    @staticmethod
    def get_parser(file_bytes: bytes):
        if not file_bytes:
            raise ParseError("Empty file provided", reason="empty_file")

        # Check for PDF magic bytes: %PDF-
        if file_bytes.startswith(b'%PDF'):
            return PDFParser()
        
        # Check for DOCX/ZIP magic bytes: PK\x03\x04
        if file_bytes.startswith(b'PK\x03\x04'):
            # This could be any ZIP, but for our context we assume DOCX if it matches PK
            return DOCXParser()

        # Fallback to TXT parser for everything else
        # A more robust check might involve checking for binary content
        return TXTParser()

    @classmethod
    def parse(cls, file_bytes: bytes) -> ParseResult:
        parser = cls.get_parser(file_bytes)
        return parser.parse(file_bytes)
