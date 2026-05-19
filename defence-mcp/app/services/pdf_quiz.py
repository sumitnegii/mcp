from pathlib import Path
from typing import Any

from app.services.claude_summary import call_claude_for_quiz


def extract_pdf_text(pdf_path: str, max_pages: int = 12) -> dict[str, Any]:
    path = Path(pdf_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only .pdf files are supported.")

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("pypdf is not installed. Run: pip install -r requirements.txt") from exc

    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    selected_pages = min(page_count, max_pages)
    chunks: list[str] = []

    for index in range(selected_pages):
        chunks.append(reader.pages[index].extract_text() or "")

    text = "\n".join(chunks).strip()
    return {
        "pdf_path": str(path),
        "page_count": page_count,
        "pages_read": selected_pages,
        "text": text,
    }


def fallback_quiz_from_text(
    text: str,
    question_count: int,
    subject: str,
) -> list[dict[str, Any]]:
    lines = [
        line.strip()
        for line in text.splitlines()
        if len(line.strip()) > 20
    ]
    question_like = [
        line
        for line in lines
        if "?" in line or line[:3].strip(" .)").isdigit()
    ]
    source_lines = question_like or lines

    quiz: list[dict[str, Any]] = []
    for line in source_lines[:question_count]:
        cleaned = " ".join(line.split())
        quiz.append(
            {
                "question": cleaned if cleaned.endswith("?") else f"Review this {subject} item: {cleaned}",
                "options": [
                    "Solve from the given paper text",
                    "Needs teacher review",
                    "Skip this question",
                    "Not enough information",
                ],
                "answer_index": 0,
                "explanation": "This fallback quiz was generated without Claude. Add CLAUDE_API_KEY for proper MCQs with explanations.",
                "topic": subject,
                "difficulty": "review",
            }
        )

    return quiz


def create_quiz_from_pdf(
    pdf_path: str,
    question_count: int = 5,
    subject: str = "mathematics",
    max_pages: int = 12,
    use_claude: bool = True,
) -> dict[str, Any]:
    question_count = max(1, min(question_count, 20))
    extracted = extract_pdf_text(pdf_path, max_pages=max_pages)
    text = extracted["text"]

    if not text:
        return {
            "pdf_path": extracted["pdf_path"],
            "page_count": extracted["page_count"],
            "pages_read": extracted["pages_read"],
            "quiz": [],
            "source": "none",
            "error": "No readable text found. This may be a scanned PDF; OCR is not implemented in v1.",
        }

    quiz = call_claude_for_quiz(text, question_count, subject) if use_claude else None
    source = "claude" if quiz else "fallback"
    if quiz is None:
        quiz = fallback_quiz_from_text(text, question_count, subject)

    return {
        "pdf_path": extracted["pdf_path"],
        "page_count": extracted["page_count"],
        "pages_read": extracted["pages_read"],
        "characters_read": len(text),
        "subject": subject,
        "question_count": len(quiz),
        "source": source,
        "quiz": quiz,
        "note": "For scanned PDFs, add OCR in a later version. For better MCQs, configure CLAUDE_API_KEY.",
    }
