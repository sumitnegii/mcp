import json
import os
import urllib.error
import urllib.request
from typing import Any

from app.schemas.defence import EligibilityRequest, EligibilityResponse
from app.utils.env import load_local_env


def call_claude_for_summary(data: EligibilityRequest, result: EligibilityResponse) -> str | None:
    load_local_env()
    api_key = os.getenv("CLAUDE_API_KEY", "").strip()
    if not api_key:
        return None

    payload = {
        "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929"),
        "max_tokens": 350,
        "system": (
            "You are a concise Indian defence career guidance assistant. "
            "Use only the supplied eligibility checker result. Do not claim this is official. "
            "Mention that the student must verify the latest official notification."
        ),
        "messages": [
            {
                "role": "user",
                "content": (
                    "Create a simple student-friendly explanation for this defence eligibility check.\n\n"
                    f"Student input:\n{data.model_dump_json(indent=2)}\n\n"
                    f"Checker result:\n{result.model_dump_json(indent=2)}"
                ),
            }
        ],
    }

    body = call_claude_messages(payload, timeout=20)
    if body is None:
        return None

    return extract_text_content(body)


def call_claude_for_quiz(
    text: str,
    question_count: int,
    subject: str,
) -> list[dict[str, Any]] | None:
    load_local_env()
    api_key = os.getenv("CLAUDE_API_KEY", "").strip()
    if not api_key:
        return None

    payload = {
        "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929"),
        "max_tokens": 1600,
        "system": (
            "You convert exam paper text into quiz JSON. Return only valid JSON. "
            "Do not include markdown fences or explanation outside JSON."
        ),
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Create {question_count} {subject} quiz questions from this extracted PDF text. "
                    "Return a JSON array. Each item must have: question, options, answer_index, explanation, topic, difficulty. "
                    "options must contain exactly 4 strings. answer_index must be 0, 1, 2, or 3. "
                    "If the answer is not clear from the text, create a reasonable practice MCQ from the concept.\n\n"
                    f"PDF text:\n{text[:12000]}"
                ),
            }
        ],
    }

    body = call_claude_messages(payload, timeout=40)
    if body is None:
        return None

    raw_json = extract_text_content(body)
    if not raw_json:
        return None

    if raw_json.startswith("```"):
        raw_json = raw_json.strip("`")
        raw_json = raw_json.removeprefix("json").strip()

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return None

    if isinstance(parsed, list):
        return parsed
    return None


def call_claude_messages(payload: dict[str, Any], timeout: int) -> dict[str, Any] | None:
    api_key = os.getenv("CLAUDE_API_KEY", "").strip()
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def extract_text_content(body: dict[str, Any]) -> str | None:
    text_parts: list[str] = []
    for block in body.get("content", []):
        if block.get("type") == "text":
            text_parts.append(block.get("text", ""))

    return "\n".join(part for part in text_parts if part).strip() or None
