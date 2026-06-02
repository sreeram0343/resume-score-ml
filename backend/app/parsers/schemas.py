from dataclasses import dataclass, field

@dataclass
class ATSFlags:
    tables_detected: bool = False
    columns_detected: bool = False
    images_detected: bool = False
    special_chars_ratio: float = 0.0  # non-ASCII / total chars
    is_scanned_pdf: bool = False

@dataclass
class ParseResult:
    text: str
    word_count: int
    page_count: int
    ats_flags: ATSFlags
    parser_used: str  # "pdfplumber" | "pymupdf" | "python-docx" | "txt"
    warnings: list[str] = field(default_factory=list)
