from app.schemas.defence import EligibilityRequest, EntryResult, Qualification
from app.tools.common import is_indian


def check_army_gd(data: EligibilityRequest) -> EntryResult:
    reasons: list[str] = []
    blockers: list[str] = []

    if is_indian(data.nationality):
        reasons.append("Nationality is Indian.")
    else:
        blockers.append("Indian nationality required in this v1 checker.")

    if 17.5 <= data.age <= 22:
        reasons.append("Age is within the current common Agniveer GD screening range of 17.5 to 22 years.")
    else:
        blockers.append("Age is outside the current common Agniveer GD screening range of 17.5 to 22 years.")

    if data.qualification in {
        Qualification.tenth,
        Qualification.twelfth_appearing,
        Qualification.twelfth_pass,
        Qualification.graduate,
    }:
        reasons.append("10th or higher qualification is present.")
    else:
        blockers.append("Army GD requires at least 10th in this v1 checker.")

    if data.marks_percent is None:
        blockers.append("Marks percentage is missing; v1 checks the common 45% aggregate guideline.")
    elif data.marks_percent >= 45:
        reasons.append("Marks are at least 45%.")
    else:
        blockers.append("Marks are below 45%.")

    return EntryResult(
        entry="Indian Army Agniveer GD basic screening",
        eligible=len(blockers) == 0,
        reasons=reasons,
        missing_or_blockers=blockers,
        next_step="Verify the latest Join Indian Army rally/CEE notification for category, state, and physical criteria.",
    )
