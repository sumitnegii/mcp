from app.schemas.defence import EligibilityRequest, EligibilityResponse, EntryResult
from app.tools.airforce import check_air_force_after_12th
from app.tools.army import check_army_gd
from app.tools.common import IMPORTANT_NOTE
from app.tools.navy import check_navy_ssr
from app.tools.nda import check_nda


def build_eligibility_response(
    data: EligibilityRequest,
    claude_summary: str | None = None,
) -> EligibilityResponse:
    results = [
        check_nda(data),
        check_navy_ssr(data),
        check_air_force_after_12th(data),
        check_army_gd(data),
    ]
    eligible_entries = [result.entry for result in results if result.eligible]

    if eligible_entries:
        summary = f"Basic screening matched {len(eligible_entries)} entry/entries."
    else:
        summary = "No entry matched all v1 screening rules. Review blockers for each entry."

    return EligibilityResponse(
        summary=summary,
        eligible_entries=eligible_entries,
        results=results,
        important_note=IMPORTANT_NOTE,
        claude_summary=claude_summary,
    )


def check_single_entry(data: EligibilityRequest, entry_id: str) -> EntryResult:
    checkers = {
        "nda_na": check_nda,
        "navy_ssr": check_navy_ssr,
        "air_force_10_2": check_air_force_after_12th,
        "army_gd": check_army_gd,
    }

    try:
        checker = checkers[entry_id]
    except KeyError as exc:
        raise ValueError(f"Unknown defence entry: {entry_id}") from exc

    return checker(data)
