from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.schemas.defence import (
    EligibilityRequest,
    EligibilityResponse,
    JSONRPCRequest,
    MCPToolCall,
    MCPToolResponse,
)
from app.services.claude_summary import call_claude_for_summary
from app.services.eligibility_engine import build_eligibility_response, check_single_entry
from app.services.pdf_quiz import create_quiz_from_pdf
from app.services.pyq_library import extract_pyq_questions, get_pyq_paper, list_pyq_papers
from app.tools.common import SUPPORTED_ENTRIES, get_entry_details, list_supported_entries


app = FastAPI(
    title="Defence Criteria MCP",
    version="1.0.0",
    description="V1 basic eligibility screening for Indian defence entries after 10th/12th.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SPECIFIC_ENTRY_TOOLS = {
    "check_nda_eligibility": "nda_na",
    "check_navy_ssr_eligibility": "navy_ssr",
    "check_airforce_eligibility": "air_force_10_2",
    "check_army_gd_eligibility": "army_gd",
}


def eligibility_tool_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": EligibilityRequest.model_json_schema()["properties"],
        "required": ["age", "gender", "qualification", "stream"],
        "additionalProperties": False,
    }


def mcp_tools_list() -> list[dict]:
    tools = [
        {
            "name": "check_defence_criteria",
            "description": "Checks all supported Indian defence entries after 10th/12th and returns entries, reasons, blockers, and next steps.",
            "input_schema": eligibility_tool_schema(),
        },
        {
            "name": "check_nda_eligibility",
            "description": "Check NDA / NA basic eligibility for a 10+2 candidate.",
            "input_schema": eligibility_tool_schema(),
        },
        {
            "name": "check_navy_ssr_eligibility",
            "description": "Check Indian Navy Agniveer SSR basic eligibility.",
            "input_schema": eligibility_tool_schema(),
        },
        {
            "name": "check_airforce_eligibility",
            "description": "Check Indian Air Force 10+2 route basic eligibility.",
            "input_schema": eligibility_tool_schema(),
        },
        {
            "name": "check_army_gd_eligibility",
            "description": "Check Indian Army Agniveer GD basic eligibility.",
            "input_schema": eligibility_tool_schema(),
        },
        {
            "name": "list_supported_defence_entries",
            "description": "Lists the defence entries supported by this v1 MCP server.",
            "input_schema": {
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        },
        {
            "name": "get_defence_entry_details",
            "description": "Returns basic details for one supported defence entry.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "entry_id": {
                        "type": "string",
                        "enum": list(SUPPORTED_ENTRIES.keys()),
                    }
                },
                "required": ["entry_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "create_quiz_from_pdf",
            "description": "Reads a local PDF file and creates a quiz from its extracted text.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pdf_path": {"type": "string"},
                    "question_count": {"type": "integer", "minimum": 1, "maximum": 20},
                    "subject": {"type": "string"},
                    "max_pages": {"type": "integer", "minimum": 1, "maximum": 50},
                    "use_claude": {"type": "boolean"},
                },
                "required": ["pdf_path"],
                "additionalProperties": False,
            },
        },
        {
            "name": "list_pyq_papers",
            "description": "List previous-year question paper PDFs available in Hind AI's local PYQ library.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "get_pyq_paper",
            "description": "Get metadata and local path for one previous-year question paper from Hind AI's PYQ library.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                },
                "required": ["filename"],
                "additionalProperties": False,
            },
        },
        {
            "name": "extract_pyq_questions",
            "description": "Extract question text from a previous-year question paper stored in Hind AI's PYQ library.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "max_pages": {"type": "integer", "minimum": 1, "maximum": 50},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                },
                "required": ["filename"],
                "additionalProperties": False,
            },
        },
    ]
    return tools


def run_mcp_tool(call: MCPToolCall) -> MCPToolResponse:
    if call.tool == "list_supported_defence_entries":
        return MCPToolResponse(tool=call.tool, content=list_supported_entries())

    if call.tool == "get_defence_entry_details":
        entry_id = str(call.arguments.get("entry_id", ""))
        return MCPToolResponse(tool=call.tool, content=get_entry_details(entry_id))

    if call.tool == "create_quiz_from_pdf":
        return MCPToolResponse(
            tool=call.tool,
            content=create_quiz_from_pdf(
                pdf_path=str(call.arguments.get("pdf_path", "")),
                question_count=int(call.arguments.get("question_count", 5)),
                subject=str(call.arguments.get("subject", "mathematics")),
                max_pages=int(call.arguments.get("max_pages", 12)),
                use_claude=bool(call.arguments.get("use_claude", call.use_claude)),
            ),
        )

    if call.tool == "list_pyq_papers":
        return MCPToolResponse(
            tool=call.tool,
            content=list_pyq_papers(
                query=call.arguments.get("query"),
                limit=int(call.arguments.get("limit", 20)),
            ),
        )

    if call.tool == "get_pyq_paper":
        return MCPToolResponse(
            tool=call.tool,
            content=get_pyq_paper(str(call.arguments.get("filename", ""))),
        )

    if call.tool == "extract_pyq_questions":
        return MCPToolResponse(
            tool=call.tool,
            content=extract_pyq_questions(
                filename=str(call.arguments.get("filename", "")),
                max_pages=int(call.arguments.get("max_pages", 12)),
                limit=int(call.arguments.get("limit", 50)),
            ),
        )

    if call.tool in SPECIFIC_ENTRY_TOOLS:
        request = EligibilityRequest(**call.arguments)
        result = check_single_entry(request, SPECIFIC_ENTRY_TOOLS[call.tool])
        return MCPToolResponse(tool=call.tool, content=result.model_dump())

    if call.tool != "check_defence_criteria":
        raise ValueError(f"Unknown MCP tool: {call.tool}")

    request = EligibilityRequest(**call.arguments)
    result = build_eligibility_response(request)
    if call.use_claude:
        result.claude_summary = call_claude_for_summary(request, result)

    return MCPToolResponse(tool=call.tool, content=result.model_dump())


@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": "Defence Criteria MCP v1 is running",
        "docs": "/docs",
        "mcp_tools": "GET /mcp/tools",
        "mcp_call": "POST /mcp/tools/call",
    }


@app.post("/check-criteria", response_model=EligibilityResponse)
def check_criteria(data: EligibilityRequest) -> EligibilityResponse:
    return build_eligibility_response(data)


@app.get("/mcp/tools")
def list_mcp_tools() -> dict[str, list[dict]]:
    return {"tools": mcp_tools_list()}


@app.post("/mcp/tools/call", response_model=MCPToolResponse)
def call_mcp_tool(call: MCPToolCall) -> MCPToolResponse:
    return run_mcp_tool(call)


@app.post("/mcp/pdf/create-quiz", response_model=MCPToolResponse)
async def upload_pdf_create_quiz(
    file: UploadFile = File(...),
    question_count: int = 5,
    subject: str = "mathematics",
    use_claude: bool = True,
) -> MCPToolResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload a .pdf file.")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")

    with NamedTemporaryFile(suffix=".pdf", delete=True) as temp_file:
        temp_file.write(contents)
        temp_file.flush()
        return run_mcp_tool(
            MCPToolCall(
                tool="create_quiz_from_pdf",
                use_claude=use_claude,
                arguments={
                    "pdf_path": temp_file.name,
                    "question_count": question_count,
                    "subject": subject,
                    "use_claude": use_claude,
                },
            )
        )


@app.post("/mcp")
def mcp_jsonrpc(request: JSONRPCRequest) -> dict:
    if request.method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {"tools": mcp_tools_list()},
        }

    if request.method == "tools/call":
        call = MCPToolCall(
            tool=request.params.get("name", ""),
            arguments=request.params.get("arguments", {}),
            use_claude=bool(request.params.get("use_claude", True)),
        )
        response = run_mcp_tool(call)
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": response.model_dump(),
        }

    return {
        "jsonrpc": "2.0",
        "id": request.id,
        "error": {"code": -32601, "message": f"Method not found: {request.method}"},
    }
