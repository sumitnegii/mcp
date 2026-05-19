from app.schemas.defence import EligibilityRequest, EntryResult, Stream
from app.tools.common import has_12th_pass_or_higher, is_indian


def check_navy_ssr(data: EligibilityRequest) -> EntryResult:
    reasons: list[str] = []
    blockers: list[str] = []

    if is_indian(data.nationality):
        reasons.append("Nationality is Indian.")
    else:
        blockers.append("Indian nationality required in this v1 checker.")

    if 17.5 <= data.age <= 21:
        reasons.append("Age is within the common Agniveer SSR screening range of 17.5 to 21 years.")
    else:
        blockers.append("Age is outside the common Agniveer SSR screening range of 17.5 to 21 years.")

    if has_12th_pass_or_higher(data.qualification):
        reasons.append("12th pass or higher qualification is present.")
    else:
        blockers.append("Navy SSR requires 12th pass in this v1 checker.")

    if data.stream == Stream.pcm:
        reasons.append("PCM stream matches the Physics and Mathematics requirement.")
    else:
        blockers.append("Navy SSR generally requires 10+2 with Mathematics and Physics.")

    if data.marks_percent is None:
        blockers.append("Marks percentage is missing; v1 checks the common 50% minimum.")
    elif data.marks_percent >= 50:
        reasons.append("Marks are at least 50%.")
    else:
        blockers.append("Marks are below 50%.")

    return EntryResult(
        entry="Indian Navy Agniveer SSR basic screening",
        eligible=len(blockers) == 0,
        reasons=reasons,
        missing_or_blockers=blockers,
        next_step="Verify the latest Join Indian Navy SSR notification before applying.",
    )
