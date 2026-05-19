import os
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

from app.schemas.defence import (
    EligibilityRequest,
    Gender,
    Qualification,
    Stream,
)
from app.services.claude_summary import call_claude_for_summary
from app.services.eligibility_engine import build_eligibility_response, check_single_entry
from app.services.pdf_quiz import create_quiz_from_pdf as build_quiz_from_pdf
from app.services.pyq_library import extract_pyq_questions as extract_pyq_questions_from_library
from app.services.pyq_library import get_pyq_paper as get_pyq_paper_from_library
from app.services.pyq_library import list_pyq_papers as list_pyq_papers_from_library
from app.tools.common import get_entry_details, list_supported_entries


mcp = FastMCP(
    "Hind AI",
    host=os.getenv("HOST", "127.0.0.1"),
    port=int(os.getenv("PORT", "8000")),
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def list_supported_defence_entries() -> dict:
    """List the defence entries supported by this v1 MCP server."""
    return list_supported_entries()


@mcp.tool()
def get_defence_entry_details(entry_id: str) -> dict:
    """Get basic details for one supported defence entry.

    Supported ids: nda_na, navy_ssr, air_force_10_2, army_gd.
    """
    return get_entry_details(entry_id)


@mcp.tool()
def create_quiz_from_pdf(
    pdf_path: str,
    question_count: int = 5,
    subject: str = "mathematics",
    max_pages: int = 12,
    use_claude: bool = True,
) -> dict:
    """Read a local PDF and create quiz questions from its extracted text.

    Use this from MCP clients by passing a PDF path available on this machine.
    For scanned PDFs, v1 may return no text because OCR is not implemented yet.
    """
    return build_quiz_from_pdf(
        pdf_path=pdf_path,
        question_count=question_count,
        subject=subject,
        max_pages=max_pages,
        use_claude=use_claude,
    )


@mcp.tool()
def list_pyq_papers(query: Optional[str] = None, limit: int = 20) -> dict:
    """List previous-year question paper PDFs available in Hind AI's PYQ library.

    Use this when a student asks for PYQ, previous-year papers, NDA paper, or past papers.
    """
    return list_pyq_papers_from_library(query=query, limit=limit)


@mcp.tool()
def get_pyq_paper(filename: str) -> dict:
    """Get metadata and local path for one previous-year question paper from Hind AI's PYQ library."""
    return get_pyq_paper_from_library(filename)


@mcp.tool()
def extract_pyq_questions(filename: str, max_pages: int = 12, limit: int = 50) -> dict:
    """Extract question text from a PYQ PDF stored in Hind AI's local PYQ library.

    Use this after get_pyq_paper when a student asks for the list of questions in a paper.
    """
    return extract_pyq_questions_from_library(
        filename=filename,
        max_pages=max_pages,
        limit=limit,
    )


def build_request(
    age: float,
    gender: Literal["male", "female", "other"],
    qualification: Literal["10th", "12th_appearing", "12th_pass", "graduate"],
    stream: Literal["PCM", "PCB", "commerce", "arts", "other"],
    nationality: str = "Indian",
    unmarried: Optional[bool] = True,
    marks_percent: Optional[float] = None,
) -> EligibilityRequest:
    return EligibilityRequest(
        age=age,
        nationality=nationality,
        gender=Gender(gender),
        qualification=Qualification(qualification),
        stream=Stream(stream),
        unmarried=unmarried,
        marks_percent=marks_percent,
    )


@mcp.tool()
def check_nda_eligibility(
    age: float,
    gender: Literal["male", "female", "other"],
    qualification: Literal["10th", "12th_appearing", "12th_pass", "graduate"],
    stream: Literal["PCM", "PCB", "commerce", "arts", "other"],
    nationality: str = "Indian",
    unmarried: Optional[bool] = True,
    marks_percent: Optional[float] = None,
) -> dict:
    """Check NDA / NA basic eligibility for a 10+2 candidate."""
    return check_single_entry(
        build_request(age, gender, qualification, stream, nationality, unmarried, marks_percent),
        "nda_na",
    ).model_dump()


@mcp.tool()
def check_navy_ssr_eligibility(
    age: float,
    gender: Literal["male", "female", "other"],
    qualification: Literal["10th", "12th_appearing", "12th_pass", "graduate"],
    stream: Literal["PCM", "PCB", "commerce", "arts", "other"],
    nationality: str = "Indian",
    unmarried: Optional[bool] = True,
    marks_percent: Optional[float] = None,
) -> dict:
    """Check Indian Navy Agniveer SSR basic eligibility."""
    return check_single_entry(
        build_request(age, gender, qualification, stream, nationality, unmarried, marks_percent),
        "navy_ssr",
    ).model_dump()


@mcp.tool()
def check_airforce_eligibility(
    age: float,
    gender: Literal["male", "female", "other"],
    qualification: Literal["10th", "12th_appearing", "12th_pass", "graduate"],
    stream: Literal["PCM", "PCB", "commerce", "arts", "other"],
    nationality: str = "Indian",
    unmarried: Optional[bool] = True,
    marks_percent: Optional[float] = None,
) -> dict:
    """Check Indian Air Force 10+2 route basic eligibility."""
    return check_single_entry(
        build_request(age, gender, qualification, stream, nationality, unmarried, marks_percent),
        "air_force_10_2",
    ).model_dump()


@mcp.tool()
def check_army_gd_eligibility(
    age: float,
    gender: Literal["male", "female", "other"],
    qualification: Literal["10th", "12th_appearing", "12th_pass", "graduate"],
    stream: Literal["PCM", "PCB", "commerce", "arts", "other"],
    nationality: str = "Indian",
    unmarried: Optional[bool] = True,
    marks_percent: Optional[float] = None,
) -> dict:
    """Check Indian Army Agniveer GD basic eligibility."""
    return check_single_entry(
        build_request(age, gender, qualification, stream, nationality, unmarried, marks_percent),
        "army_gd",
    ).model_dump()


@mcp.tool()
def check_defence_criteria(
    age: float,
    gender: Literal["male", "female", "other"],
    qualification: Literal["10th", "12th_appearing", "12th_pass", "graduate"],
    stream: Literal["PCM", "PCB", "commerce", "arts", "other"],
    nationality: str = "Indian",
    unmarried: Optional[bool] = True,
    marks_percent: Optional[float] = None,
    use_claude: bool = False,
) -> dict:
    """Check basic Indian defence eligibility after 10th/12th.

    Returns eligible entries, matched criteria, blockers, and next steps.
    This is guidance only; official notifications decide final eligibility.
    """
    request = build_request(age, gender, qualification, stream, nationality, unmarried, marks_percent)
    result = build_eligibility_response(request)
    if use_claude:
        result.claude_summary = call_claude_for_summary(request, result)

    return result.model_dump()


def main() -> None:
    mcp.run(transport="stdio")


def http() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
