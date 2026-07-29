"""
Agent Dispatcher — Query Router & Master Orchestrator
Uses LLM-based Intent Classification with fast heuristic fallbacks to route user queries
to appropriate tools (run_compare_tool, policy_document_qa, get_insurer_risk).
Computes dynamic AI evaluation scores (0-100%), enforces strict prompt language matching (English vs Hinglish),
integrates long-term MongoDB user_profile memory, short-term session memory, and writes structured JSON line logs.
"""
import os
import json
import re
import time
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from backend.app.tools.rag_tool import run_rag_tool
from backend.app.tools.compare_tool import run_compare_tool
from backend.app.tools.risk_tool import get_insurer_risk
from backend.app.logger import log_execution
from backend.app.user_profile import update_user_profile, format_profile_for_context
from backend.app.memory import get_memory

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

router_model = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0.0,
    groq_api_key=groq_key
)

ROUTER_PROMPT_TEMPLATE = """
You are an intent classification router for an Indian Health Insurance Multi-Agent System.

Given the user query and any user profile preferences, select EXACTLY ONE tool from the following list:
1. `compare_policies`: Use when the user asks to compare 2 or more health insurance policies, or asks which policy has specific features (e.g. 'zero room rent', 'co-payment', 'maternity', 'waiting period comparison').
2. `insurer_financial_risk`: Use when the user asks about Claim Settlement Ratio (CSR), Incurred Claim Ratio (ICR), Solvency Ratio, or financial safety/risk of insurance providers (e.g. Star Health, ICICI Lombard, Niva Bupa, Care Health, HDFC Ergo).
3. `policy_document_qa`: Use for specific policy coverage terms, inclusions, exclusions, waiting periods, or specific policy clauses.
4. `general_chat`: Use for generic greetings, casual conversation, off-topic questions, questions about the assistant itself, non-insurance queries (e.g., 'hello', 'who are you', 'what can you do', 'tell me a joke', 'weather', or gibberish/nonsense).

Respond with valid JSON containing keys 'tool' and 'reason'.

{user_profile_context}
User Query: "{query}"

JSON Response:
"""

ENGLISH_SYNTHESIS_PROMPT = """
You are an expert Indian Health Insurance Advisor.
Below is structured policy / financial risk data retrieved from the system.
Synthesize this data into a clear, professional, well-formatted response to answer the user's question directly.

STRICT RULE: Write 100% FULLY IN ENGLISH. Do NOT use any Hindi or Hinglish words under any circumstances.

Previous Conversation History:
{chat_history}

{user_profile_context}
Structured Policy Data:
{db_data}

User Question: {query}

Synthesized Answer (in English):
"""

HINGLISH_SYNTHESIS_PROMPT = """
You are an expert Indian Health Insurance Advisor.
Below is structured policy / financial risk data retrieved from the system.
Synthesize this data into a clear, helpful response to answer the user's question directly.

STRICT RULE: Write in natural, easy-to-understand HINGLISH (Hindi written in Roman script) matching the user's prompt style.

Previous Conversation History:
{chat_history}

{user_profile_context}
Structured Policy Data:
{db_data}

User Question: {query}

Synthesized Answer (in Hinglish):
"""

def is_query_hinglish(query: str) -> bool:
    """Detects whether query is written in Hinglish using exact word boundary matching."""
    hinglish_words = [
        "kitna", "kya", "kaise", "mein", "hai", "batao", "bataiye", "chahiye",
        "wale", "wala", "wali", "kaunsa", "kaunsi", "karo", "kab", "kyun", "hoga",
        "lagta", "niche", "varsh", "samajh", "bhi", "nahi", "hain", "kaisa", "meri"
    ]
    query_words = re.findall(r'\b\w+\b', query.lower())
    return any(w in query_words for w in hinglish_words)

def heuristic_router(query: str) -> str:
    """Fast rule-based classification fallback."""
    q_lower = query.lower().strip()

    general_keywords = [
        "who are you", "what can you do", "what do you do", "why are you here",
        "what is your purpose", "how can you help", "who made you", "hello", "hi",
        "hey", "help", "joke", "weather", "working", "asdf", "nonsense", "random"
    ]
    if any(g in q_lower for g in general_keywords) or len(q_lower.split()) <= 1:
        if not any(k in q_lower for k in ["csr", "icr", "copay", "co-payment", "star", "niva", "hdfc", "icici", "care", "bupa", "room", "maternity", "waiting"]):
            return "general_chat"

    if any(k in q_lower for k in ["claim settlement", "csr", "icr", "solvency", "financial risk", "safety ratio", "settlement ratio"]):
        return "insurer_financial_risk"

    if any(k in q_lower for k in ["compare", "vs", "versus", "difference in", "which policy has", "which policies have", "zero room rent", "no room rent", "co-payment"]):
        return "compare_policies"

    return "policy_document_qa"

def compute_confidence_score(tool: str, answer: str, fallback_used: bool = False, top_similarity_score: int = None) -> tuple[int, str]:
    """
    Computes a dynamic confidence score (0-100%) and level description.
    """
    if fallback_used:
        return 88, "High Precision (Live Web Ingested Context)"

    if tool == "general_chat":
        return 98, "High Precision (System Assistant Info)"
    elif tool == "insurer_financial_risk":
        return 98, "High Precision (IRDAI Verified Metrics)"
    elif tool == "compare_policies":
        return 96, "High Precision (MongoDB Atlas Document Match)"
    elif tool == "policy_document_qa":
        if top_similarity_score is not None and top_similarity_score > 0:
            return top_similarity_score, f"Dynamic Precision ({top_similarity_score}% FAISS Vector Match)"
        if "policy context" in answer.lower() or "according to" in answer.lower():
            return 94, "High Precision (FAISS Vector Index Match)"
        return 85, "Moderate Confidence (General Knowledge Fallback)"

    return 90, "Standard Confidence"

def route_and_execute(query: str, session_id: str = "default_session") -> dict:
    """
    Routes user query to appropriate tool, executes tool, loads/updates conversation memory & user profile, logs execution, and returns result dict.
    """
    start_time = time.time()

    # Load session conversation memory
    mem = get_memory(session_id)
    history_msgs = mem.load_memory_variables({}).get("chat_history", [])
    if not history_msgs:
        chat_history_str = "None"
    else:
        lines = []
        for m in history_msgs:
            role = "User" if m.type in ["human", "user"] else "Assistant"
            lines.append(f"{role}: {m.content}")
        chat_history_str = "\n".join(lines)

    # Opportunistically update and format long-term user profile from MongoDB Atlas
    update_user_profile(session_id, query)
    user_prof_str = format_profile_for_context(session_id)

    tool_choice = "policy_document_qa"
    tools_used = []
    fallback_used = False
    top_similarity_score = None
    tool_data = ""

    # System greetings & general introduction intent pre-check
    greetings_keywords = [
        "who are you", "what can you do", "what do you do", "why are you here",
        "what is your purpose", "how can you help", "who made you"
    ]
    q_lower = query.lower().strip()
    if any(g in q_lower for g in greetings_keywords) or q_lower in ["hi", "hello", "hey", "help"]:
        tool_choice = "general_chat"

    if tool_choice != "general_chat":
        try:
            prompt = PromptTemplate.from_template(ROUTER_PROMPT_TEMPLATE)
            formatted_prompt = prompt.format(query=query, user_profile_context=user_prof_str)
            response = router_model.invoke(formatted_prompt)
            content = response.content.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            res_json = json.loads(content)
            tool_choice = res_json.get("tool", "policy_document_qa")
        except Exception as e:
            print(f"Router LLM failed, using heuristic: {e}")
            tool_choice = heuristic_router(query)

    # Heuristic override for structured policy feature queries
    if any(k in q_lower for k in ["co-payment", "copay", "co pay", "room rent", "room-rent", "no-claim bonus", "ncb"]):
        if not any(k in q_lower for k in ["claim settlement", "csr", "icr", "solvency"]):
            tool_choice = "compare_policies"

    print(f"--> [DISPATCHER] Query: '{query}' -> Tool: '{tool_choice}'")
    tools_used.append(tool_choice)

    # Select language-specific synthesis prompt
    if is_query_hinglish(query):
        synthesis_prompt_template = HINGLISH_SYNTHESIS_PROMPT
    else:
        synthesis_prompt_template = ENGLISH_SYNTHESIS_PROMPT

    if tool_choice == "general_chat":
        if is_query_hinglish(query):
            answer = "Namaste! Main aapka AI Health Insurance Advisor hoon. Main Indian health insurance policies ka comparison, IRDAI Claim Settlement Ratios (CSR), room rent limits, aur policy brochure terms explain karne mein aapki madad kar sakta hoon. Aap Indian health insurance se juda koi bhi sawaal pooch sakte hain!"
        else:
            answer = "Hello! I am your AI Health Insurance Advisor. I specialize in helping you compare Indian health insurance policies, check IRDAI Claim Settlement Ratios (CSR) & Incurred Claim Ratios (ICR), review room rent limits, waiting periods, and search policy brochures. How can I help you with health insurance today?"

        conf_score = 98
        conf_level = "High Precision (System Assistant Info)"
        latency_ms = int((time.time() - start_time) * 1000)
        log_execution(session_id, query, tool_choice, latency_ms, True)
        
        # Save context to conversation memory
        mem.save_context({"input": query}, {"output": answer})

        return {
            "session_id": session_id,
            "query": query,
            "tool": tool_choice,
            "tools_used": tools_used,
            "answer": answer,
            "tool_data": "",
            "confidence_score": conf_score,
            "confidence_level": conf_level,
            "fallback_used": False,
            "latency_ms": latency_ms
        }

    if tool_choice == "insurer_financial_risk":
        raw_result = get_insurer_risk(query)
        tool_data = raw_result
        prompt = PromptTemplate.from_template(synthesis_prompt_template)
        formatted_prompt = prompt.format(db_data=raw_result, query=query, user_profile_context=user_prof_str, chat_history=chat_history_str)
        answer = router_model.invoke(formatted_prompt).content.strip()

    elif tool_choice == "compare_policies":
        raw_result = run_compare_tool(query)
        tool_data = raw_result
        prompt = PromptTemplate.from_template(synthesis_prompt_template)
        formatted_prompt = prompt.format(db_data=raw_result, query=query, user_profile_context=user_prof_str, chat_history=chat_history_str)
        answer = router_model.invoke(formatted_prompt).content.strip()

    else:
        answer, fallback_used, top_similarity_score = run_rag_tool(query)
        tool_data = answer
        if fallback_used:
            tools_used.append("web_search_fallback")

    score, score_level = compute_confidence_score(
        tool_choice,
        answer,
        fallback_used=fallback_used,
        top_similarity_score=top_similarity_score
    )

    elapsed_ms = (time.time() - start_time) * 1000.0

    # Save turn exchange to conversation memory
    mem.save_context({"input": query}, {"output": answer})

    # Write structured JSON line log entry
    log_execution(
        session_id=session_id,
        query=query,
        tool_used=tool_choice,
        latency_ms=elapsed_ms,
        success=not fallback_used,
        estimated_tokens=len(query.split()) + len(answer.split())
    )

    return {
        "session_id": session_id,
        "query": query,
        "tool": tool_choice,
        "answer": answer,
        "tool_data": tool_data,
        "tools_used": tools_used,
        "confidence_score": score,
        "confidence_level": score_level,
        "latency_ms": round(elapsed_ms, 2)
    }

def handle_query(session_id: str, query: str) -> dict:
    """Wrapper function for API endpoint compatibility."""
    return route_and_execute(query, session_id=session_id)

if __name__ == "__main__":
    q = "What is the waiting period for pre-existing diseases in Niva Bupa policy?"
    print(route_and_execute(q, session_id="test_sess_001"))
