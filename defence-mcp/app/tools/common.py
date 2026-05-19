from typing import Any

from app.schemas.defence import Qualification


IMPORTANT_NOTE = (
    "This is a v1 guidance checker, not an official eligibility decision. "
    "Always verify exact age cutoffs, DOB windows, gender rules, marital status, marks, physical standards, "
    "medical standards, and intake-specific conditions from official notifications."
)


SUPPORTED_ENTRIES: dict[str, dict[str, Any]] = {
    "nda_na": {
        "name": "NDA / NA basic screening",
        "category": "Officer entry after 10+2",
        "minimum_qualification": "12th pass or appearing",
        "preferred_stream": "PCM for Navy/Air Force wings; non-PCM may only fit Army wing in this v1 checker.",
        "common_age_range": "16.5 to 19.5 years",
    },
    "navy_ssr": {
        "name": "Indian Navy Agniveer SSR basic screening",
        "category": "Sailor entry after 10+2",
        "minimum_qualification": "12th pass with Mathematics and Physics",
        "preferred_stream": "PCM",
        "common_age_range": "17.5 to 21 years",
    },
    "air_force_10_2": {
        "name": "Indian Air Force after 10+2 basic screening",
        "category": "Air Force route after 10+2",
        "minimum_qualification": "12th pass or appearing",
        "preferred_stream": "PCM",
        "common_age_range": "16.5 to 19.5 years",
    },
    "army_gd": {
        "name": "Indian Army Agniveer GD basic screening",
        "category": "Soldier entry",
        "minimum_qualification": "10th pass or higher",
        "preferred_stream": "Any stream in this v1 checker",
        "common_age_range": "17.5 to 22 years",
    },
}


def is_indian(nationality: str) -> bool:
    return nationality.strip().lower() == "indian"


def has_12th_or_appearing(qualification: Qualification) -> bool:
    return qualification in {
        Qualification.twelfth_appearing,
        Qualification.twelfth_pass,
        Qualification.graduate,
    }


def has_12th_pass_or_higher(qualification: Qualification) -> bool:
    return qualification in {Qualification.twelfth_pass, Qualification.graduate}


def list_supported_entries() -> dict[str, Any]:
    return {
        "entries": [
            {"id": entry_id, **entry}
            for entry_id, entry in SUPPORTED_ENTRIES.items()
        ],
        "note": "These are v1 screening categories. Always verify official intake notifications.",
    }


def get_entry_details(entry_id: str) -> dict[str, Any]:
    entry = SUPPORTED_ENTRIES.get(entry_id)
    if entry is None:
        return {
            "found": False,
            "entry_id": entry_id,
            "available_entry_ids": list(SUPPORTED_ENTRIES.keys()),
        }

    return {
        "found": True,
        "entry_id": entry_id,
        **entry,
        "important_note": "This is guidance only, not an official eligibility decision.",
    }
