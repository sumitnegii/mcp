from app.schemas.defence import EligibilityRequest, EntryResult, Stream
from app.tools.common import has_12th_or_appearing, is_indian


def check_nda(data: EligibilityRequest) -> EntryResult:
    reasons: list[str] = []
    blockers: list[str] = []

    if is_indian(data.nationality):
        reasons.append("Nationality is Indian.")
    else:
        blockers.append("NDA screening requires Indian nationality in this v1 checker.")

    if 16.5 <= data.age <= 19.5:
        reasons.append("Age is within the common NDA screening range of 16.5 to 19.5 years.")
    else:
        blockers.append("Age is outside the common NDA screening range of 16.5 to 19.5 years.")

    if has_12th_or_appearing(data.qualification):
        reasons.append("12th pass/appearing or higher qualification is present.")
    else:
        blockers.append("NDA requires 12th pass/appearing eligibility.")

    if data.unmarried is True:
        reasons.append("Unmarried status provided.")
    elif data.unmarried is False:
        blockers.append("NDA entries generally require unmarried candidates.")
    else:
        blockers.append("Marital status was not provided.")

    if data.stream == Stream.pcm:
        reasons.append("PCM stream supports Army, Navy, and Air Force NDA wings.")
    else:
        reasons.append("Non-PCM stream may be considered for Army wing only; Navy/Air Force need Physics and Mathematics.")

    eligible = len(blockers) == 0
    return EntryResult(
        entry="NDA / NA basic screening",
        eligible=eligible,
        reasons=reasons,
        missing_or_blockers=blockers,
        next_step=(
            "Check the latest UPSC NDA/NA notification for exact date-of-birth window and wing-specific rules."
            if eligible
            else "Fix the blockers above, then compare with the latest UPSC NDA/NA notification."
        ),
    )
