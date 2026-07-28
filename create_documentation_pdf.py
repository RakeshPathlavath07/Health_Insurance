import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

PDF_OUTPUT_PATH = "/Users/rakeshpathlavath/Desktop/health_insurance/health_insurance_project_architecture.pdf"
MD_OUTPUT_PATH = "/Users/rakeshpathlavath/Desktop/health_insurance/PROJECT_DOCUMENTATION.md"

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_OUTPUT_PATH,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Palette
    PRIMARY = colors.HexColor("#1A237E")
    SECONDARY = colors.HexColor("#0D47A1")
    ACCENT = colors.HexColor("#0288D1")
    BG_LIGHT = colors.HexColor("#F5F7FA")
    TEXT_DARK = colors.HexColor("#212121")

    # Title & Subtitle Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=11,
        leading=14,
        textColor=ACCENT,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=SECONDARY,
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#2E7D32"),
        backColor=colors.HexColor("#ECEFF1"),
        borderColor=colors.HexColor("#CFD8DC"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=8
    )

    story = []

    # Title Banner
    story.append(Paragraph("Health Insurance Multi-Agent System — Architecture & Specification", title_style))
    story.append(Paragraph("Comprehensive Technical Documentation: Inputs, Components, Outputs, & Data Formats", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=12))

    # 1. Executive Summary
    story.append(Paragraph("1. System Purpose & High-Level Architecture", h1_style))
    exec_text = (
        "This project is an enterprise-grade Multi-Agent GenAI System designed for Indian Health Insurance recommendations. "
        "It accepts natural language user questions regarding policy feature comparisons, IRDAI risk metrics, and detailed policy brochure text. "
        "A <b>ReAct Master Dispatcher</b> dynamically orchestrates three specialized tools, maintaining short-term hybrid conversation memory "
        "and validating final output accuracy against automated benchmark suites."
    )
    story.append(Paragraph(exec_text, body_style))

    # Architecture Overview Table
    arch_data = [
        [Paragraph("<b>Layer</b>", body_style), Paragraph("<b>Technology / Implementation</b>", body_style)],
        [Paragraph("Frontend UI", body_style), Paragraph("Streamlit (Session state, chat bubbles, tool badges)", body_style)],
        [Paragraph("REST API", body_style), Paragraph("FastAPI (Asynchronous execution, CORS, Pydantic data validation)", body_style)],
        [Paragraph("Orchestration", body_style), Paragraph("LangChain ReAct Agent Executor backed by Groq (Llama-3.3-70B)", body_style)],
        [Paragraph("Structured DB", body_style), Paragraph("MongoDB Atlas M0 Free Tier (Collection: insurance_db.health_insurance)", body_style)],
        [Paragraph("Vector Store / RAG", body_style), Paragraph("FAISS + HuggingFace sentence-transformers (all-MiniLM-L6-v2) + Web Search Fallback", body_style)],
        [Paragraph("Risk & Metrics", body_style), Paragraph("Versioned IRDAI FY2024 JSON + RapidFuzz Centralized Matching", body_style)],
        [Paragraph("Evaluation Suite", body_style), Paragraph("Automated 5-query benchmark accuracy testing script (backend/eval_suite.py)", body_style)]
    ]
    t_arch = Table(arch_data, colWidths=[120, 420])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BG_LIGHT),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#B0BEC5")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 10))

    # 2. Detailed Component Breakdown
    story.append(Paragraph("2. Component Specifications (Inputs, Processing, Outputs)", h1_style))

    components = [
        {
            "name": "Component 1: Streamlit Frontend (frontend/streamlit_app.py)",
            "inputs": "<b>Input</b>: User query string from chat input box + Session ID stored in <code>st.session_state</code>.",
            "desc": "<b>Processing</b>: Sends HTTP POST request to FastAPI backend (<code>/chat</code>). Renders assistant chat bubbles and displays a styled <code>tool-badge</code> showing exact tool name(s) called.",
            "outputs": "<b>Output Format</b>: Interactive Web Chat UI rendering Markdown text and tool execution badges."
        },
        {
            "name": "Component 2: FastAPI Backend (backend/app/main.py)",
            "inputs": "<b>Input</b>: JSON Request Payload: <code>{\"session_id\": str, \"query\": str}</code>",
            "desc": "<b>Processing</b>: Validates inputs using Pydantic models (<code>ChatRequest</code>). Passes query to Master Dispatcher, applies Guardrails validation, and returns structured response.",
            "outputs": "<b>Output Format</b>: JSON Response Payload:<br/><code>{\"session_id\": str, \"query\": str, \"answer\": str, \"tools_used\": list[str]}</code>"
        },
        {
            "name": "Component 3: ReAct Master Dispatcher (backend/app/dispatcher.py)",
            "inputs": "<b>Input</b>: <code>session_id: str</code>, <code>query: str</code>",
            "desc": "<b>Processing</b>: Loads past chat history from Memory Manager. Constructs ReAct prompt with 3 tools (<code>compare_policies</code>, <code>insurer_financial_risk</code>, <code>policy_document_qa</code>). Uses Groq <code>deep_model</code> (Llama-3.3-70B) for multi-step reasoning. Tracks executed tool names.",
            "outputs": "<b>Output Format</b>: Python Dict: <code>{\"answer\": str, \"tools_used\": list[str]}</code>"
        },
        {
            "name": "Component 4: Text-to-MongoDB Compare Tool (backend/app/tools/compare_tool.py)",
            "inputs": "<b>Input</b>: Natural language comparison query string.",
            "desc": "<b>Processing</b>: Prompts <code>deep_model</code> to generate a single-line PyMongo <code>find()</code> query. Verifies query safety via <code>is_query_safe()</code> (blocking write/delete keywords). Executes query against MongoDB Atlas collection.",
            "outputs": "<b>Output Format</b>: Formatted Markdown comparison text detailing ratings ('good'/'average'/'bad') and feature descriptions across requested policies."
        },
        {
            "name": "Component 5: Dynamic Insurer Risk Tool (backend/app/tools/risk_tool.py)",
            "inputs": "<b>Input</b>: Natural language query containing an insurer/provider name.",
            "desc": "<b>Processing</b>: Extracts provider name using Centralized Fuzzy Matcher. Reads versioned IRDAI data from <code>data/risk_data.json</code>. Enforces data freshness disclaimer.",
            "outputs": "<b>Output Format</b>: Structured string containing Provider, Claim Settlement Ratio (CSR), Incurred Claim Ratio (ICR), Solvency Ratio, and explicit 'IRDAI FY2024' report disclaimer."
        },
        {
            "name": "Component 6: Centralized Fuzzy Matcher (backend/app/tools/fuzzy_matcher.py)",
            "inputs": "<b>Input</b>: <code>query: str</code>, <code>score_threshold: int = 50</code>",
            "desc": "<b>Processing</b>: Checks direct aliases (e.g. 'max bupa' -> 'niva-bupa', 'religare' -> 'care-health'). Uses <code>rapidfuzz.process.extractOne</code> partial ratio against canonical registries in <code>data/policy_names.py</code>.",
            "outputs": "<b>Output Format</b>: Tuple: <code>(canonical_provider_name: str, match_score: int)</code>"
        },
        {
            "name": "Component 7: FAISS Vector Index & PDF Ingest Pipeline (backend/app/ingestion/pdf_ingest.py)",
            "inputs": "<b>Input</b>: <code>pdf_source</code> (URL or local path), <code>provider: str</code>, <code>policy_name: str</code>",
            "desc": "<b>Processing</b>: Extracts text with <code>pdfplumber</code>, splits into 500-char chunks (overlap=50), embeds with local <code>sentence-transformers/all-MiniLM-L6-v2</code> model on CPU. Loads existing FAISS index and appends without overwriting.",
            "outputs": "<b>Output Format</b>: Boolean status (<code>True/False</code>) + Persistent index stored in <code>faiss_index/</code> directory."
        },
        {
            "name": "Component 8: Web Search Agent (backend/app/ingestion/web_search_agent.py)",
            "inputs": "<b>Input</b>: <code>policy_name: str</code>",
            "desc": "<b>Processing</b>: Executes Tavily Search for policy wording/brochure PDF. Prompts Groq <code>light_model</code> to evaluate search results and isolate direct PDF download link.",
            "outputs": "<b>Output Format</b>: Direct PDF URL string (e.g., <code>https://.../policy_wording.pdf</code>) or empty string."
        },
        {
            "name": "Component 9: RAG Tool (backend/app/tools/rag_tool.py)",
            "inputs": "<b>Input</b>: Natural language policy query.",
            "desc": "<b>Processing</b>: Performs similarity search on FAISS vector store. If empty, triggers Web Search Agent -> PDF Ingest pipeline -> Re-searches FAISS. Synthesizes final answer using Groq <code>light_model</code>.",
            "outputs": "<b>Output Format</b>: Detailed synthesized answer string citing retrieved document context."
        },
        {
            "name": "Component 10: Hybrid Session Memory Manager (backend/app/memory.py)",
            "inputs": "<b>Input</b>: <code>session_id: str</code>, new message turn context.",
            "desc": "<b>Processing</b>: Maintains <code>ConversationSummaryBufferMemory(max_token_limit=300)</code> per session. Keeps recent turns verbatim and uses <code>light_model</code> to summarize older turns.",
            "outputs": "<b>Output Format</b>: LangChain chat history message objects."
        },
        {
            "name": "Component 11: Output Validation Guardrails (backend/app/guardrails.py)",
            "inputs": "<b>Input</b>: <code>query: str</code>, <code>raw_answer: str</code>",
            "desc": "<b>Processing</b>: Checks non-emptiness, validates response formatting, and prevents hallucinated output claims.",
            "outputs": "<b>Output Format</b>: Clean validated response string."
        },
        {
            "name": "Component 12: Evaluation Benchmark Suite (backend/eval_suite.py)",
            "inputs": "<b>Input</b>: Array of 5 benchmark test cases containing expected tools and required keywords.",
            "desc": "<b>Processing</b>: Executes queries through <code>handle_query</code>, verifies tool routing accuracy and answer keyword presence.",
            "outputs": "<b>Output Format</b>: Accuracy report string (e.g., <code>Overall Accuracy: 5/5 Passed (100.0% Correct)</code>)."
        }
    ]

    for comp in components:
        story.append(Paragraph(comp["name"], h2_style))
        story.append(Paragraph(comp["inputs"], body_style))
        story.append(Paragraph(comp["desc"], body_style))
        story.append(Paragraph(comp["outputs"], body_style))
        story.append(Spacer(1, 4))

    # 3. Data Schemas Section
    story.append(Spacer(1, 8))
    story.append(Paragraph("3. Core Data Schemas & Formats", h1_style))

    story.append(Paragraph("<b>MongoDB Policy Document Schema (insurance_db.health_insurance):</b>", h2_style))
    mongo_schema_text = (
        "{\n"
        '  "provider": "hdfc-ergo",\n'
        '  "insurance_name": "hdfc-ergo-optima-secure",\n'
        '  "description": "Flagship product offering 4X coverage benefit.",\n'
        '  "features": {\n'
        '     "maternity-cover": {"rating": "bad", "details": "Not covered in Optima Secure"},\n'
        '     "room-rent-limit": {"rating": "good", "details": "No room rent capping"},\n'
        '     "waiting-period": {"rating": "good", "details": "30 days initial, 36 months PED"}\n'
        "  }\n"
        "}"
    )
    story.append(Paragraph(mongo_schema_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    story.append(Paragraph("<b>Risk Data JSON Schema (data/risk_data.json):</b>", h2_style))
    risk_schema_text = (
        "{\n"
        '  "as_of_year": 2024,\n'
        '  "source": "IRDAI Annual Report FY2023-24",\n'
        '  "data": {\n'
        '    "icici-lombard": {\n'
        '      "display_name": "ICICI Lombard General Insurance",\n'
        '      "CSR": "98.6%", "ICR": "78.4%", "solvency_ratio": "2.62",\n'
        '      "summary": "Strong claim settlement ratio (98.6%) and healthy solvency."\n'
        "    }\n"
        "  }\n"
        "}"
    )
    story.append(Paragraph(risk_schema_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    doc.build(story)
    print("PDF generation complete:", PDF_OUTPUT_PATH)

def generate_markdown():
    md_content = """# Health Insurance Multi-Agent System — Architecture & Documentation

## 1. System Overview & Architecture
The **Health Insurance Recommendation Agent** is a multi-agent GenAI platform built for Indian health insurance analysis. It combines structured MongoDB querying, IRDAI risk data lookups, FAISS vector retrieval with live PDF search fallback, and hybrid conversation memory.

### Architecture Tech Stack:
- **Frontend UI**: Streamlit (Session state, chat history, live tool badges)
- **Backend API**: FastAPI (Asynchronous endpoints, CORS, Pydantic validation)
- **Master Orchestrator**: LangChain ReAct Agent backed by Groq (`llama-3.3-70b-versatile`)
- **Structured Database**: MongoDB Atlas Cloud (`insurance_db.health_insurance`)
- **Unstructured RAG**: FAISS Vector Store + HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **Web Search**: Tavily Search API
- **Evaluation**: Benchmark test suite (`backend/eval_suite.py`)

---

## 2. Detailed Component Specifications

### 1. Streamlit Frontend (`frontend/streamlit_app.py`)
- **Input**: User text query + Session ID in `st.session_state`.
- **Processing**: Calls `POST http://localhost:8000/chat`. Renders response markdown and displays tool badge.
- **Output Format**: Interactive Chat UI with tool badges (`🛠️ Tool Called: compare_policies`).

### 2. FastAPI REST API (`backend/app/main.py`)
- **Input**: `ChatRequest(session_id: str, query: str)` JSON payload.
- **Processing**: Validates input, invokes Master Dispatcher, applies Guardrails validation.
- **Output Format**: JSON `ChatResponse(session_id, query, answer, tools_used)`.

### 3. ReAct Master Dispatcher (`backend/app/dispatcher.py`)
- **Input**: `session_id: str`, `query: str`.
- **Processing**: Loads memory, constructs ReAct prompt with 3 tools (`compare_policies`, `insurer_financial_risk`, `policy_document_qa`). Executes agent loop and captures tool names.
- **Output Format**: Dict `{"answer": str, "tools_used": list[str]}`.

### 4. Text-to-MongoDB Compare Tool (`backend/app/tools/compare_tool.py`)
- **Input**: Natural language comparison query string.
- **Processing**: Prompts `deep_model` to generate single-line PyMongo `find()` code. Validates query safety via `is_query_safe()`. Executes against MongoDB Atlas.
- **Output Format**: Structured feature rating & details comparison string.

### 5. Dynamic Insurer Risk Tool (`backend/app/tools/risk_tool.py`)
- **Input**: Query containing provider/insurer name.
- **Processing**: Extracts provider name via `fuzzy_matcher.py`. Looks up versioned metrics in `data/risk_data.json`. Enforces IRDAI report disclaimer.
- **Output Format**: Formatted risk string with CSR, ICR, Solvency Ratio, and `IRDAI FY2024` disclaimer.

### 6. Centralized Fuzzy Matcher (`backend/app/tools/fuzzy_matcher.py`)
- **Input**: `query: str`, `score_threshold: int = 50`.
- **Processing**: Resolves aliases, calculates `rapidfuzz` partial ratios against canonical registries in `data/policy_names.py`.
- **Output Format**: Tuple `(canonical_provider_name: str, match_score: int)`.

### 7. FAISS Vector Store & PDF Ingest Pipeline (`backend/app/ingestion/pdf_ingest.py`)
- **Input**: PDF URL or path, `provider`, `policy_name`.
- **Processing**: Extracts text (`pdfplumber`), chunks (500 chars), embeds with local `all-MiniLM-L6-v2` model. Appends to `faiss_index/` without overwriting existing index.
- **Output Format**: Boolean success status + FAISS index stored on disk.

### 8. Web Search Agent (`backend/app/ingestion/web_search_agent.py`)
- **Input**: `policy_name: str`.
- **Processing**: Executes Tavily Search for policy PDF, prompts `light_model` to return direct PDF link.
- **Output Format**: Direct PDF URL string or empty string.

### 9. RAG Tool (`backend/app/tools/rag_tool.py`)
- **Input**: Natural language policy query.
- **Processing**: Searches FAISS vector store. If empty, triggers Web Search Agent -> PDF Ingest pipeline -> Re-searches FAISS. Synthesizes answer using `light_model`.
- **Output Format**: Detailed synthesized response string.

### 10. Hybrid Session Memory Manager (`backend/app/memory.py`)
- **Input**: `session_id: str`, turn messages.
- **Processing**: `ConversationSummaryBufferMemory(max_token_limit=300)`. Keeps recent turns verbatim and summarizes older turns using `light_model`.
- **Output Format**: Chat history message objects.

### 11. Guardrails (`backend/app/guardrails.py`)
- **Input**: `query: str`, `raw_answer: str`.
- **Processing**: Validates answer formatting and output non-emptiness.
- **Output Format**: Clean validated answer string.

### 12. Automated Evaluation Benchmark Suite (`backend/eval_suite.py`)
- **Input**: 5 benchmark test dicts.
- **Processing**: Executes tests, verifies tool selection accuracy and answer keywords.
- **Output Format**: Accuracy summary report string (`Overall Accuracy: 5/5 Passed (100.0% Correct)`).

---

## 3. Core Data Schemas

### MongoDB Document Schema (`insurance_db.health_insurance`)
```json
{
  "provider": "hdfc-ergo",
  "insurance_name": "hdfc-ergo-optima-secure",
  "description": "Flagship product offering 4X coverage benefit.",
  "features": {
     "maternity-cover": {"rating": "bad", "details": "Not covered in Optima Secure"},
     "room-rent-limit": {"rating": "good", "details": "No room rent capping"},
     "waiting-period": {"rating": "good", "details": "30 days initial, 36 months PED"}
  }
}
```

### Risk Data Schema (`backend/data/risk_data.json`)
```json
{
  "as_of_year": 2024,
  "source": "IRDAI Annual Report FY2023-24",
  "data": {
    "icici-lombard": {
      "display_name": "ICICI Lombard General Insurance",
      "CSR": "98.6%",
      "ICR": "78.4%",
      "solvency_ratio": "2.62",
      "summary": "Strong claim settlement ratio (98.6%) and healthy solvency."
    }
  }
}
```
"""
    with open(MD_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(md_content)
    print("Markdown documentation generation complete:", MD_OUTPUT_PATH)

if __name__ == "__main__":
    generate_markdown()
    build_pdf()
