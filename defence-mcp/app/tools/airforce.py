from app.schemas.defence import EligibilityRequest, EntryResult, Stream
from app.tools.common import has_12th_or_appearing, is_indian


def check_air_force_after_12th(data: EligibilityRequest) -> EntryResult:
    reasons: list[str] = []
    blockers: list[str] = []

    if is_indian(data.nationality):
        reasons.append("Nationality is Indian.")
    else:
        blockers.append("Indian nationality required in this v1 checker.")

    if 16.5 <= data.age <= 19.5:
        reasons.append("Age is within the common Air Force 10+2 officer-entry screening range of 16.5 to 19.5 years.")
    else:
        blockers.append("Age is outside the common Air Force 10+2 officer-entry screening range of 16.5 to 19.5 years.")

    if has_12th_or_appearing(data.qualification):
        reasons.append("12th pass/appearing or higher qualification is present.")
    else:
        blockers.append("10+2 entry requires 12th pass/appearing eligibility.")

    if data.stream == Stream.pcm:
        reasons.append("PCM stream matches the Physics, Chemistry, and Mathematics requirement.")
    else:
        blockers.append("Air Force 10+2 technical/flying routes generally need Physics and Mathematics.")

    return EntryResult(
        entry="Indian Air Force after 10+2 basic screening",
        eligible=len(blockers) == 0,
        reasons=reasons,
        missing_or_blockers=blockers,
        next_step="Verify the latest Indian Air Force career notification for the exact entry route.",
    )
