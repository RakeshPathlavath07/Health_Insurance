# Health Insurance Recommendation Agent — Build Instructions

## Purpose of this file

This file is the single source of truth for building this project. It describes
what we are building, why, the exact tech decisions already made (with reasons),
and a **strict step-by-step build order**. Each step lists: what it needs as
input, what it must produce, what it hands to the next step, and how to verify
it worked before moving forward.

**Rule for whoever is executing this (human or agent): do NOT jump ahead.
Complete one step fully, show the output, get it verified, then move to the
next numbered step.** Do not generate code for Step 5 while Step 2 is still
unverified.

---

## 1. What we are building (one paragraph)

A multi-agent GenAI system for Indian health insurance. A user asks a natural
language question (compare policies, ask about specific coverage, ask about an
insurer's financial risk, or ask for a recommendation). A **dispatcher agent**
decides which specialized tool(s) should answer it, calls them (possibly more
than one, in sequence), and returns one crisp, reasoned final answer. The system
has conversation memory, a proper backend API, a chat UI, and is deployed live
(not just runnable in a terminal).

---

## 2. Key architecture decisions (already made — don't re-debate these mid-build)

### 2.1 Tech stack — fully free version (₹0 / $0, no card anywhere)

- **Orchestration**: LangChain (ReAct-style agent + tools)
- **LLM: two direct model variables, declared inline per file — same style as
  the original repo** (which just wrote `model = ChatAnthropic(...)` at the
  top of each file). We are **not** building an abstraction layer for this;
  each file that needs an LLM declares its own `light_model` and/or
  `deep_model` variable near the top, same as the original repo did with a
  single `model` variable. What changes is that **every such declaration gets
  a comment block right above it** explaining what it's for and exactly what
  to touch when you swap it later — see the exact comment format in Step 0.
  - **Light model** (used for: simple lookups, RAG final-answer synthesis from
    already-retrieved context, memory summarization): fast, low-reasoning.
  - **Deep model** (used for: dispatcher tool-routing/chaining, compare-tool
    pymongo code generation): needs stronger multi-step reasoning.
  - **Claude/Anthropic is not used to start** — no ongoing free tier, only a
    one-time trial credit. Starting point for both models: **Groq
    (Llama-3.3-70B)**, same free model for both roles, since you don't have a
    specific "deep thinking" free model picked yet. When you find one later
    (e.g. a Gemini thinking-budget model, a DeepSeek reasoning model, etc.),
    you replace just the `deep_model` declaration — the comment above it
    tells you exactly what to change.
- **Structured data**: MongoDB Atlas **M0 free tier** (free forever, 512MB) —
  holds per-policy feature ratings (co-payment, room-rent limit, etc.)
- **Unstructured data / RAG**: FAISS vector store (local, free), embeddings via
  **HuggingFace `all-MiniLM-L6-v2`** (runs locally, no API key needed at all)
- **Web search fallback**: **Tavily free tier** (1,000 credits/month, no card)
- **Backend**: FastAPI (wraps the agent as a real API with sessions)
- **Frontend**: Streamlit (chat UI)
- **Deployment**: MongoDB Atlas (DB, free) + **Render free web service**
  (backend — note: sleeps after inactivity, ~30-60s cold start on first
  request after idle; acceptable for a CV demo link, not for a real product)
  + **Streamlit Community Cloud** (frontend, free for public repos).
  Railway is intentionally **not** used here — it no longer has an ongoing
  free tier (trial-credit only, same issue as Anthropic).

### 2.2 Memory decision — **ConversationSummaryBufferMemory** (hybrid)

Three options were considered:
- *Buffer memory* (keep full raw history): rejected — this project's tool
  outputs (Mongo comparison tables, RAG chunks) are verbose; raw history grows
  fast and burns tokens/cost quickly.
- *Summary memory* (compress everything into a running summary): rejected
  alone — follow-up questions like *"what about waiting period for the second
  one?"* depend on exact entity names (provider, policy name). Pure summarization
  risks losing that precision.
- **Hybrid — ConversationSummaryBufferMemory**: keeps the most recent few turns
  **verbatim** (so exact policy/provider names used a moment ago are preserved)
  and **summarizes older turns** once a token threshold is hit. This is the best
  fit here: cheap on tokens, but doesn't lose the specific entities that
  follow-up questions depend on.

This is **short-term (session) memory**. We are also adding a lightweight
**long-term memory**: a `user_profile` collection in MongoDB keyed by
`user_id`, storing stated preferences (e.g. "wants maternity cover", "budget
conscious") extracted opportunistically from the conversation. This is optional
and built last (Step 10) — the project works fully without it, it's a polish
item for your CV story ("supports both short-term and long-term memory").

### 2.3 Risk tool decision — **dynamic filtering, versioned static data**

The original repo's risk tool ignored the question entirely and returned a
hardcoded dict of all insurers regardless of what was asked. We are fixing this,
but being realistic about what "dynamic" means here:

- **What becomes dynamic**: the tool will extract the provider from the query
  (reusing the same fuzzy-match utility as the RAG tool), look up only that
  provider's ICR/CSR, and return an explicit "no risk data available for X" if
  it's not found — instead of dumping everything and hoping the LLM notices.
- **What stays static-but-versioned**: the underlying ICR/CSR numbers
  themselves. These come from IRDAI's **annual** report — there is no live feed
  to poll, so "real-time dynamic data" isn't a realistic goal. Instead, the data
  file gets an explicit `as_of_year` field, so the system (and you, in an
  interview) can honestly say "data is current as of IRDAI's FY2024 report" — a
  correct answer with an honest freshness disclaimer beats a wrong "live" claim.
- **Optional stretch goal** (only after everything else works): a small
  scheduled script that re-scrapes/re-enters the latest IRDAI report once a
  year and updates the versioned file.

---

## 3. Folder structure (create this first, empty files are fine)

```
health-insurance-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entrypoint
│   │   ├── config.py                # env vars, API keys
│   │   ├── memory.py                 # session memory logic
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── compare_tool.py       # text-to-mongo agent
│   │   │   ├── risk_tool.py          # dynamic risk lookup
│   │   │   └── rag_tool.py           # RAG + fuzzy match + ingestion fallback
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── scrape_policy_data.py # one-time/offline: build Mongo dataset
│   │   │   ├── pdf_ingest.py         # download+chunk+embed a policy PDF
│   │   │   └── web_search_agent.py   # ReAct + web search to find PDF URLs
│   │   ├── dispatcher.py             # the master ReAct orchestrator
│   │   └── guardrails.py             # input/output validation
│   ├── data/
│   │   ├── policy_names.py           # canonical provider/policy name lists
│   │   └── risk_data.json            # versioned ICR/CSR data
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── streamlit_app.py
│   └── requirements.txt
├── faiss_index/                      # generated, gitignored
├── .gitignore
├── README.md
└── INSTRUCTIONS.md                   # this file
```

---

## 4. Build order — one step at a time

For every step below: **do only that step**, run/test it in isolation, paste
the output back for review, then move to the next step.

---

### STEP 0 — Environment setup

**Goal**: a working empty skeleton with dependencies installed.

**Do**:
1. Create the folder structure above.
2. Create a Python virtual environment.
3. Create `backend/requirements.txt` with: `fastapi`, `uvicorn`, `langchain`,
   `langchain-groq`, `langchain-huggingface`, `langchain-community`, `pymongo`,
   `faiss-cpu`, `rapidfuzz`, `pdfplumber`, `python-dotenv`, `pydantic`. Add
   another provider's package later (e.g. `langchain-google-genai`) only when
   you actually swap a model in — no need to install it speculatively now.
   (No `langchain-anthropic` — Claude isn't used, to keep this 100% free.)
4. Create `frontend/requirements.txt` with: `streamlit`, `requests`.
5. Create `.env.example` listing: `GROQ_API_KEY`, `TAVILY_API_KEY`,
   `MONGODB_URI`. Add a new key here (e.g. `GOOGLE_API_KEY`) only when you
   actually add a provider that needs it. (No Anthropic key needed.)
6. Create a MongoDB Atlas free (M0) cluster and get the connection string.
7. Sign up for free Groq and Tavily API keys — no card required for either.

**The comment pattern to use everywhere you declare a model** — this is the
convention for the whole project. Every time a file declares `light_model` or
`deep_model`, it looks like this:

```python
# ============================================================
# LIGHT MODEL — simple, low-reasoning calls (e.g. RAG answer
# synthesis from already-retrieved context, memory summarization)
# CURRENT: Groq, free tier, no card required
# TO REPLACE WITH A DIFFERENT FREE MODEL LATER:
#   1. pip install the new provider's langchain package
#   2. change the import below
#   3. change the class + model name below
#   4. add the new provider's key name to .env (keep GROQ_API_KEY
#      too if other files still use Groq)
# ============================================================
from langchain_groq import ChatGroq
light_model = ChatGroq(model_name='llama-3.3-70b-versatile', temperature=0)


# ============================================================
# DEEP MODEL — multi-step reasoning (e.g. dispatcher tool
# routing/chaining, compare-tool pymongo code generation)
# CURRENT: Groq, free tier (same as light model — no dedicated
# "deep thinking" free model chosen yet)
# TO REPLACE WITH A DEEP-THINKING MODEL WHEN YOU FIND ONE:
#   1. pip install the new provider's langchain package
#      (e.g. langchain-google-genai for a Gemini thinking model)
#   2. change the import below
#   3. change the class + model name below (some providers add
#      extra params here, e.g. Gemini's thinking_budget=... —
#      check that provider's LangChain docs for what's available)
#   4. add the new provider's key name to .env
# ============================================================
from langchain_groq import ChatGroq
deep_model = ChatGroq(model_name='llama-3.3-70b-versatile', temperature=0.2)
```

Every file below that needs an LLM (compare_tool, rag_tool, dispatcher,
memory) declares its own copy of whichever of these two blocks it needs —
exactly like the original repo declared its own `model = ChatAnthropic(...)`
at the top of `main.py`, `general_questions.py`, etc. There's no shared
config file to go hunt through; you always know exactly which model a file is
using by looking at the top of that file.

**Hands off to next step**: a working environment + a live Mongo connection
string in `.env` + the comment-block pattern above ready to paste into any
file that needs a model.

**Verify before proceeding**: (1) run a 3-line Python script that connects to
Mongo Atlas with `pymongo` and prints the list of databases; (2) paste the
`light_model`/`deep_model` blocks into a throwaway test file and confirm
`light_model.invoke("say hi")` and `deep_model.invoke("say hi")` both return a
response. If both work, Step 0 is done.

---

### STEP 1 — Structured data layer (MongoDB)

**Goal**: the `insurance_db.health_insurance` collection populated with policy
feature data, matching the schema the compare tool will expect.

**Input**: nothing external needed yet — start with a small **hand-written**
seed set (5–10 policies across 3–4 providers) rather than scraping first. Scraping
is a separate, later concern.

**Do**:
1. Define the document schema (one document per policy):
   ```
   {
     "provider": "icici-lombard",
     "insurance_name": "icici-lombard-max-protect-classic",
     "description": "...",
     "features": {
        "co-payment": {"rating": "good", "details": "..."},
        "Room-rent-limit": {"rating": "bad", "details": "..."},
        ... (9 features total)
     }
   }
   ```
2. Write `ingestion/scrape_policy_data.py` to insert this seed data into Mongo
   (a simple script with a list of dicts + `collection.insert_many()` is enough
   for now — real scraping comes later as a stretch goal).
3. Create `data/policy_names.py`: two lists/dicts — canonical `provider` names
   and, per provider, canonical `insurance_name` values. This is what the fuzzy
   matcher (Step 4) will match against.

**Hands off to next step**: a populated Mongo collection + canonical name
lists that the risk tool and RAG tool will both depend on.

**Verify**: query Mongo directly (`collection.find_one()`) and confirm the
seed documents look right.

---

### STEP 2 — Risk tool (dynamic)

**Goal**: a tool function that takes a query, extracts the provider, and
returns only that provider's risk data — or an honest "not found."

**Input**: the versioned `data/risk_data.json` (format: `{"as_of_year": 2024,
"data": {"icici-lombard": {"CSR": "...", "ICR": "..."}, ...}}`), and the
canonical provider list from Step 1.

**Do**:
1. Build `risk_tool.py`:
   - Extract a provider name from the input query (simple keyword/fuzzy match
     against the canonical provider list — reuse or pre-build the fuzzy
     matcher here since Step 4 will formalize it).
   - Look up that provider in `risk_data.json`.
   - If found: return provider + CSR + ICR + `as_of_year`.
   - If not found: return a clear string like `"No risk data available for
     <provider>. Data covers: <list of known providers>."`
2. Do **not** wire this into the dispatcher yet — test it standalone by
   calling the function directly with a few sample queries (one known
   provider, one unknown provider, one with a typo).

**Hands off to next step**: a working, input-aware `risk_tool(query) -> str`
function.

**Verify**: run it with 3 queries — a valid known provider, a typo'd provider
name, and a completely unknown provider — and confirm each gives the correct,
distinct response (not the same dump every time, which was the original bug).

---

### STEP 3 — Compare tool (text-to-Mongo agent)

**Goal**: given a natural-language comparison question, generate and safely
execute a MongoDB **read-only** query against Step 1's collection.

**Input**: the Mongo schema from Step 1, the user's question.

**Do**:
1. At the top of `compare_tool.py`, paste the **deep model** comment block
   from Step 0 and declare `deep_model` there — this is the tool where
   reasoning quality matters most (correct, safe query generation), so it
   should always use whichever model you've marked as your "deep" one. Build
   the prompt using `deep_model`: give it the exact schema, the canonical
   provider list, and strict rules (read-only `find()` only, no
   writes/deletes, no verbose output — code only).
2. **Important change from the original repo**: instead of raw `exec()` on
   whatever the LLM returns, add a validation check before running anything:
   - Reject the generated code if it contains any of `delete`, `drop`,
     `update`, `insert`, `remove`, `$where`, `eval(`, `exec(`, `import os`,
     `import sys`, `subprocess`.
   - Only allow it through if it's calling `.find(` / `.find_one(` /
     `.aggregate(` (read-only) on the known `collection` object.
3. Execute the validated code, capture output, return it.

**Hands off to next step**: a working, validated `compare_tool(query) ->
str` function.

**Verify — this step matters more than the others, don't skip it**: run the
*same* 10-15 comparison questions through it at least twice each and log how
often the deep model's generated code (a) fails the safety validation
entirely, (b) runs but errors out (bad field names, wrong syntax), or (c)
works first try. This is the step where whichever free model backs
`deep_model` is most likely to show its limits versus a paid model like
Claude. If the failure rate is high (rough guide: worse than ~1 in 4), don't
push forward blindly — options at that point are: tighten the prompt further
(more explicit few-shot examples of correct queries), add a
retry-with-error-fed-back loop (catch the exception, send it back to the LLM
asking it to fix the query), or replace the `deep_model` declaration at the
top of this file with a different provider (using the comment block as your
checklist) and re-run this same test to compare. Also test with a
deliberately "evil" input like *"delete all data"* phrased as a question, and
confirm the guardrail blocks it rather than the LLM being tricked into
generating a delete.

---

### STEP 4 — Fuzzy matcher + FAISS ingestion pipeline

**Goal**: reusable utilities the RAG tool depends on — matching noisy
provider/policy names, and getting policy text into FAISS.

**Do**:
1. Build the fuzzy-match function properly (using `rapidfuzz`) against
   `data/policy_names.py`, returning matched provider + policy name + scores.
   Replace the ad-hoc version from Step 2 with this one, and update Step 2 to
   import it (don't maintain two copies).
2. Build `pdf_ingest.py`: given a PDF URL, download it, extract text
   (`pdfplumber`), chunk it (`RecursiveCharacterTextSplitter`), embed
   (`all-MiniLM-L6-v2`), and store into FAISS with `provider`/`policy_name`
   metadata.
   - **Fix the original repo's bug here**: the index must be *loaded and
     appended to* if it already exists, not overwritten every call. Check
     `os.path.exists(index_path)` first; load + `add_documents()` if it
     exists, only create fresh if it doesn't.
3. Build `web_search_agent.py`: paste the **light model** comment block at
   the top, declare `light_model` there (fine for this — it's a narrow,
   single-purpose task, not open-ended reasoning), and build a small ReAct
   agent using `light_model` + Tavily whose only job is: given "find the
   latest PDF for policy X", return a PDF URL.

**Hands off to next step**: `fuzzy_match()`, `ingest_pdf()`, and
`find_policy_pdf_url()` — three independent, testable utilities.

**Verify**: manually ingest 1–2 real policy PDFs, confirm FAISS index file is
created, then run a second ingestion and confirm the first policy's data is
still retrievable (i.e. it wasn't overwritten).

---

### STEP 5 — RAG tool ("other questions")

**Goal**: wire Step 4's utilities into the full RAG flow.

**Do**: exactly the flow from the earlier discussion — extract
provider+policy from the query → fuzzy match → search FAISS filtered by
metadata → if empty, use web search agent to find a PDF → ingest it → re-search
→ answer using retrieved chunks as context. At the top of `rag_tool.py`, paste
the **light model** comment block and declare `light_model` there — this is
just synthesizing an answer from context already in hand, not multi-step
reasoning, so it doesn't need `deep_model`.

**Hands off to next step**: a working `rag_tool(query) -> str`.

**Verify**: ask a question about a policy already ingested (fast path), then
ask about a policy that has never been ingested (should trigger the fallback:
search → ingest → answer). Confirm both paths work and the second one is
slower (expected, since it's doing a live web search + PDF download).

---

### STEP 6 — Memory layer

**Goal**: session-based `ConversationSummaryBufferMemory`.

**Do**:
1. Build `memory.py`: a simple `session_id -> memory object` store (an
   in-memory Python dict is fine to start; can move to Redis later if
   deploying at scale, not needed now).
2. At the top of `memory.py`, paste the **light model** comment block and
   declare `light_model` there. Wire `ConversationSummaryBufferMemory`
   (LangChain) with `light_model` (summarization is a relatively simple task
   — no need to spend deep-model capacity/rate-limit budget on it), with a
   token limit (e.g. 1000 tokens before it starts summarizing).
3. This step does **not** touch the dispatcher yet — just get the memory
   object working standalone: feed it a few fake exchanges, print what it
   returns as "context so far," and confirm recent turns are verbatim and
   older ones get summarized once you exceed the threshold.

**Hands off to next step**: a working `get_memory(session_id)` function.

**Verify**: simulate 5+ turns of conversation into one session, check that
early turns get compressed into a summary while the last couple stay exact.

---

### STEP 7 — Dispatcher (the orchestrator)

**Goal**: tie all three tools + memory into the ReAct master agent.

**Do**:
1. At the top of `dispatcher.py`, paste the **deep model** comment block and
   declare `deep_model` there. Build the ReAct agent using `deep_model` + your
   3 tools (compare, risk, RAG), using the same tool-selection prompt logic as
   the original repo (with the updated tool descriptions reflecting the risk
   tool's new behavior).
2. Pass the session's memory context into the agent's input alongside the raw
   query.
3. After getting the agent's answer, save the new exchange back into that
   session's memory.

**Hands off to next step**: a single function
`handle_query(session_id, query) -> answer` — this is everything the API
layer needs.

**Verify**: run 2–3 full conversations manually (including a follow-up
question that depends on memory, e.g. "what about that one's room rent
limit?") and confirm it resolves correctly. Also watch specifically for
tool-selection mistakes here (dispatcher picking the wrong tool, or failing to
chain compare→risk when recommending) — this is the other place, besides
Step 3, where a weaker free deep model's reasoning limits are most likely to
show up. If you see it misrouting often, tightening the ReAct prompt with a
couple of worked examples usually helps more than anything else — or, same as
Step 3, replace the `deep_model` declaration with a different provider and
re-test.

---

### STEP 8 — Guardrails (input/output validation)

**Goal**: a lightweight check before returning the final answer.

**Do**: build `guardrails.py` with one function that checks the final answer
doesn't contain obvious fabricated specifics (e.g. numbers/policy names not
present anywhere in the tool outputs collected during this turn). Keep this
simple — a basic "does the answer only cite policy/provider names that were
actually retrieved this turn" check is enough for a CV project; don't
over-engineer this step.

**Hands off to next step**: `handle_query()` now returns a validated answer.

**Verify**: intentionally feed it a case where you'd expect hallucination
risk (ask about a feature that wasn't retrieved) and see whether the check
catches it.

---

### STEP 9 — FastAPI backend

**Goal**: expose `handle_query()` as a real API.

**Do**: build `app/main.py` with:
- `POST /chat` — body: `{"session_id": str, "query": str}` → response:
  `{"answer": str, "tool_trace": [...]}`
- Basic error handling (try/except around the dispatcher call, return a
  clean 500 with a message instead of crashing)
- CORS enabled for the Streamlit frontend

**Hands off to next step**: a running API at `localhost:8000/chat`.

**Verify**: test with `curl` or Postman — send 2 requests with the same
`session_id` and confirm the second response shows memory of the first.

---

### STEP 10 — Streamlit frontend

**Goal**: a chat UI calling the FastAPI backend.

**Do**: build `streamlit_app.py` — a chat interface (`st.chat_message`,
`st.chat_input`), a generated/stored `session_id` in `st.session_state`, and
optionally a sidebar showing which tool(s) handled the last query (from
`tool_trace`) for explainability.

**Hands off to next step**: a working local app: Streamlit → FastAPI → agent.

**Verify**: full end-to-end conversation through the UI, including a
follow-up question.

---

### STEP 11 — Deployment

**Goal**: a live, shareable link on Streamlit Community Cloud.

**Do**:
1. MongoDB Atlas — confirm access is not IP-restricted to localhost (allow access from anywhere `0.0.0.0/0` so Streamlit Cloud can connect).
2. Deploy Streamlit frontend application to **Streamlit Community Cloud** (connect GitHub repository `RakeshPathlavath07/Health_Insurance`, main file `frontend/streamlit_app.py`, set environment variables — `GROQ_API_KEY`, `TAVILY_API_KEY`, `MONGODB_URI` — in the Streamlit Secrets dashboard).
3. The application runs standalone in-process on Streamlit Community Cloud as a single unified service (executing `dispatcher.route_and_execute()` directly without requiring a separate backend service).

**Verify**: open the Streamlit Cloud URL (`https://healthinsurancesystem.streamlit.app/`) from any device/network and run a full multi-turn conversation.

---

### STEP 12 (optional, do last) — Logging, tracing, eval set, long-term memory

Only after everything above works and is deployed:
- Add structured logging (which tool ran, latency, token usage) — even a
  simple JSON-per-line log file is enough to talk about in an interview.
- Build a small eval set: 10–15 sample questions with expected tool + expected
  answer characteristics, run periodically, track pass/fail.
- Add the long-term `user_profile` memory collection described in section 2.2.

---

## 5. What to tell me at each step

After finishing a step, share: (1) what you built, (2) the actual output you
got when testing it, (3) anything that didn't behave as expected. I'll review
before you move to the next numbered step.
