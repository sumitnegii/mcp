# Defence Criteria MCP v1

Small FastAPI service for basic Indian defence eligibility screening after 10th/12th.

## What v1 checks

- NDA / NA basic screening
- Indian Navy Agniveer SSR basic screening
- Indian Air Force after 10+2 basic screening
- Indian Army Agniveer GD basic screening

This is not an official eligibility decision. Official notices often use exact date-of-birth windows, physical standards, medical standards, category rules, and intake-specific conditions.

## Real MCP server

V1 exposes focused MCP tools:

```text
check_defence_criteria
check_nda_eligibility
check_navy_ssr_eligibility
check_airforce_eligibility
check_army_gd_eligibility
list_supported_defence_entries
get_defence_entry_details
create_quiz_from_pdf
list_pyq_papers
get_pyq_paper
extract_pyq_questions
```

Run the real MCP server over stdio:

```bash
python -m app.mcp_server
```

This is the version an MCP client can launch as a tool server.

Run the real MCP server over Streamable HTTP:

```bash
python -c "from app.mcp_server import http; http()"
```

For Render, use this start command so Claude can connect to the public MCP endpoint:

```bash
HOST=0.0.0.0 python -c "from app.mcp_server import http; http()"
```

Render provides the `PORT` environment variable automatically. The MCP endpoint will be:

```text
https://your-render-service.onrender.com/mcp
```

Docker/Render files are included:

```text
Dockerfile
render.yaml
```

The FastAPI app also keeps prototype helper routes:

```text
GET  /mcp/tools
POST /mcp/tools/call
POST /mcp
```

## Project structure

```text
app/
  main.py                  # FastAPI routes and MCP-style HTTP demo routes
  mcp_server.py            # Real MCP server for stdio and Streamable HTTP
  schemas/defence.py       # Pydantic request/response schemas
  services/
    eligibility_engine.py  # Aggregates rule checks
    claude_summary.py      # Optional AI explanation layer
    pdf_quiz.py            # PDF extraction and quiz creation
    pyq_library.py         # Previous-year question paper lookup
  tools/
    nda.py
    navy.py
    airforce.py
    army.py
    common.py
```

## Run locally

```bash
cd defence-mcp
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8001/docs
```

## Example request

POST `/mcp/tools/call`

```json
{
  "tool": "check_defence_criteria",
  "use_claude": true,
  "arguments": {
    "age": 17.5,
    "nationality": "Indian",
    "gender": "male",
    "qualification": "12th_pass",
    "stream": "PCM",
    "unmarried": true,
    "marks_percent": 62
  }
}
```

## PYQ library

Previous-year question papers live in:

```text
app/pyq/
```

Students can ask Claude/Hind AI for PYQs, and the MCP server can use:

```text
list_pyq_papers
get_pyq_paper
extract_pyq_questions
```

Example:

```json
{
  "tool": "list_pyq_papers",
  "arguments": {
    "query": "NDA Math 2024",
    "limit": 5
  }
}
```

Specific tool calls are also supported:

```json
{
  "tool": "check_nda_eligibility",
  "use_claude": false,
  "arguments": {
    "age": 17.5,
    "nationality": "Indian",
    "gender": "male",
    "qualification": "12th_pass",
    "stream": "PCM",
    "unmarried": true,
    "marks_percent": 62
  }
}
```

## Claude summary

Set this in `.env`, then restart the Python server:

```text
CLAUDE_API_KEY=your_key_here
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

The MCP tool still works without Claude. Claude only adds a short explanation.

## Why this is MCP-style

This backend is reusable. Later, the same MCP tool can be called from:

- React website
- Android app
- Discord bot
- Minecraft plugin/script
- Voice assistant

## Official references to verify before production use

- UPSC NDA/NA notification for NDA exact DOB and qualification rules
- Join Indian Navy Agniveer SSR eligibility page
- Indian Air Force career pages for after-10+2 entries
- Join Indian Army Agniveer eligibility PDFs/notifications
