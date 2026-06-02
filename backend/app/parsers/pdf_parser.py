import io
import pdfplumber
import fitz  # PyMuPDF
from .base_parser import BaseParser, ParseError
from .schemas import ParseResult, ATSFlags

class PDFParser(BaseParser):
    """Parser for PDF files using pdfplumber with PyMuPDF fallback."""

    def parse(self, file_bytes: bytes) -> ParseResult:
        self.validate_size(file_bytes)
        
        text = ""
        warnings = []
        parser_used = "pdfplumber"
        ats_flags = ATSFlags()
        page_count = 0

        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    # Detect tables
                    tables = page.extract_tables()
                    if tables:
                        ats_flags.tables_detected = True
                    
                    # Multi-column detection (simple heuristic based on horizontal gaps)
                    words = page.extract_words()
                    if self._detect_columns(words):
                        ats_flags.columns_detected = True
                    
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"

            # Fallback to PyMuPDF if text is too short or pdfplumber failed
            if len(text.strip()) < 50:
                text, parser_used = self._parse_with_pymupdf(file_bytes, ats_flags)
                
        except Exception as e:
            # If pdfplumber fails, try PyMuPDF as a last resort
            try:
                text, parser_used = self._parse_with_pymupdf(file_bytes, ats_flags)
            except Exception as e_inner:
                raise ParseError(f"PDF parsing failed: {str(e_inner)}", file_type="PDF")

        # Post-parse checks
        if len(text.strip()) < 100:
            ats_flags.is_scanned_pdf = True
            warnings.append("Low text content detected. This might be a scanned PDF or image-based document.")

        # Image detection via PyMuPDF
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                if page.get_images():
                    ats_flags.images_detected = True
                    break
            if page_count == 0:
                page_count = len(doc)
            doc.close()
        except Exception:
            pass

        ats_flags.special_chars_ratio = self.calculate_special_chars_ratio(text)

        return ParseResult(
            text=text.strip(),
            word_count=len(text.split()),
            page_count=page_count,
            ats_flags=ats_flags,
            parser_used=parser_used,
            warnings=warnings
        )

    def _parse_with_pymupdf(self, file_bytes: bytes, ats_flags: ATSFlags) -> tuple[str, str]:
        text = ""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text, "pymupdf"

    def _detect_columns(self, words: list[dict]) -> bool:
        """Heuristic to detect multiple columns."""
        if not words:
            return False
        
        # Look for words on the same line (similar top/bottom) with a large horizontal gap
        lines = {}
        for w in words:
            top = round(w['top'], 1)
            if top not in lines:
                lines[top] = []
            lines[top].append(w)
        
        for top, line_words in lines.items():
            if len(line_words) < 2:
                continue
            line_words.sort(key=lambda x: x['x0'])
            for i in range(len(line_words) - 1):
                gap = line_words[i+1]['x0'] - line_words[i]['x1']
                # If gap is larger than 100 units, likely a column separator
                if gap > 100:
                    return True
        return False
