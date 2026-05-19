from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class Qualification(str, Enum):
    tenth = "10th"
    twelfth_appearing = "12th_appearing"
    twelfth_pass = "12th_pass"
    graduate = "graduate"


class Stream(str, Enum):
    pcm = "PCM"
    pcb = "PCB"
    commerce = "commerce"
    arts = "arts"
    other = "other"


class EligibilityRequest(BaseModel):
    age: float = Field(..., ge=10, le=35, examples=[17.5])
    nationality: str = Field("Indian", examples=["Indian"])
    gender: Gender = Field(..., examples=["male"])
    qualification: Qualification = Field(..., examples=["12th_pass"])
    stream: Stream = Field(..., examples=["PCM"])
    unmarried: Optional[bool] = Field(True, examples=[True])
    marks_percent: Optional[float] = Field(None, ge=0, le=100, examples=[62])


class EntryResult(BaseModel):
    entry: str
    eligible: bool
    reasons: list[str]
    missing_or_blockers: list[str]
    next_step: str


class EligibilityResponse(BaseModel):
    summary: str
    eligible_entries: list[str]
    results: list[EntryResult]
    important_note: str
    claude_summary: Optional[str] = None


class MCPToolCall(BaseModel):
    tool: str = Field(..., examples=["check_defence_criteria"])
    arguments: dict[str, Any] = Field(default_factory=dict)
    use_claude: bool = Field(True, examples=[True])


class MCPToolResponse(BaseModel):
    tool: str
    content: dict[str, Any]


class JSONRPCRequest(BaseModel):
    jsonrpc: str = Field("2.0", examples=["2.0"])
    id: int | str | None = Field(None, examples=[1])
    method: str = Field(..., examples=["tools/call"])
    params: dict = Field(default_factory=dict)
