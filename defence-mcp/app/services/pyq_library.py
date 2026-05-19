import re
from pathlib import Path
from typing import Any

from app.services.pdf_quiz import extract_pdf_text


PYQ_DIR = Path(__file__).resolve().parents[1] / "pyq"


def list_pyq_papers(query: str | None = None, limit: int = 20) -> dict[str, Any]:
    papers = [_paper_metadata(path) for path in sorted(PYQ_DIR.glob("*.pdf"))]
    if query:
        query_terms = [
            term
            for term in query.strip().lower().replace("-", " ").split()
            if term
        ]
        papers = [
            paper
            for paper in papers
            if _matches_query(paper, query_terms)
        ]

    return {
        "count": len(papers),
        "papers": papers[: max(1, min(limit, 100))],
        "note": "These PYQs are served from Hind AI's local app/pyq folder.",
    }


def get_pyq_paper(filename: str) -> dict[str, Any]:
    requested = _safe_pdf_path(filename)
    if requested is None or not requested.exists():
        return {
            "found": False,
            "filename": filename,
            "available": list_pyq_papers(limit=100)["papers"],
        }

    return {
        "found": True,
        **_paper_metadata(requested),
        "usage_hint": "Use extract_pyq_questions to read questions from this paper through Hind AI.",
    }


def extract_pyq_questions(filename: str, max_pages: int = 12, limit: int = 50) -> dict[str, Any]:
    requested = _safe_pdf_path(filename)
    if requested is None or not requested.exists():
        return {
            "found": False,
            "filename": filename,
            "available": list_pyq_papers(limit=100)["papers"],
        }

    extracted = extract_pdf_text(str(requested), max_pages=max_pages)
    questions = _extract_question_lines(_question_section_text(extracted["text"]), limit=limit)
    return {
        "found": True,
        "filename": requested.name,
        "title": requested.stem,
        "page_count": extracted["page_count"],
        "pages_read": extracted["pages_read"],
        "question_count": len(questions),
        "questions": questions,
        "source": "Hind AI PYQ library",
        "note": "If a PDF page is scanned or formatting-heavy, some questions may be incomplete until OCR is added.",
    }


def _safe_pdf_path(filename: str) -> Path | None:
    candidate = Path(filename).name
    if not candidate.lower().endswith(".pdf"):
        return None
    return PYQ_DIR / candidate


def _paper_metadata(path: Path) -> dict[str, Any]:
    return {
        "filename": path.name,
        "title": path.stem,
        "path": str(path),
        "size_bytes": path.stat().st_size,
    }


def _matches_query(paper: dict[str, Any], query_terms: list[str]) -> bool:
    haystack = f"{paper['filename']} {paper['title']}".lower().replace("-", " ")
    return all(term in haystack for term in query_terms)


def _extract_question_lines(text: str, limit: int) -> list[dict[str, Any]]:
    normalized = " ".join(text.split())
    starts = [
        match
        for match in re.finditer(r"(?<!\d)(\d{1,3})\.\s+", normalized)
        if _looks_like_question_start(normalized, match)
    ]

    questions: list[dict[str, Any]] = []
    for index, match in enumerate(starts[:limit]):
        next_start = starts[index + 1].start() if index + 1 < len(starts) else len(normalized)
        questions.append(
            {
                "number": int(match.group(1)),
                "text": normalized[match.start():next_start].strip(),
            }
        )

    return questions[: max(1, min(limit, 200))]


def _looks_like_question_start(text: str, match: re.Match[str]) -> bool:
    number = int(match.group(1))
    if number <= 0:
        return False

    previous_context = text[max(0, match.start() - 4):match.start()]
    if "×" in previous_context:
        return False

    return True


def _question_section_text(text: str) -> str:
    marker = "QUESTION PAPER"
    upper_text = text.upper()
    marker_index = upper_text.find(marker)
    if marker_index == -1:
        return text
    return text[marker_index + len(marker):]
