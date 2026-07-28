"""
RAG Tool — General Policy Q&A & Document Search
Combines fuzzy matching, FAISS vector search with score calculation (similarity_search_with_score),
live web search ingestion fallback, and Instant LLM answer synthesis with strict brand content validation and programmatic language detection.
"""
import os
import re

os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from backend.app.tools.fuzzy_matcher import match_provider, match_policy
from backend.app.ingestion.pdf_ingest import get_embeddings, ingest_pdf, FAISS_INDEX_DIR
from backend.app.ingestion.web_search_agent import search_policy_web_data

from langchain_groq import ChatGroq

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

light_model = ChatGroq(
    model_name="llama-3.1-8b-instant",
    temperature=0.1,
    groq_api_key=groq_key
)

ENGLISH_RAG_PROMPT_TEMPLATE = """
You are an expert Indian Health Insurance Advisor.
Answer the user's question using ONLY the retrieved policy context below.
If the context does not contain enough information, state what is known and mention that specific policy wording details are limited.

STRICT RULE: Write 100% FULLY IN ENGLISH. Do NOT use any Hindi or Hinglish words under any circumstances.

Retrieved Policy Context:
{context}

User Question: {question}

Detailed Answer (in English):
"""

HINGLISH_RAG_PROMPT_TEMPLATE = """
You are an expert Indian Health Insurance Advisor.
Answer the user's question using ONLY the retrieved policy context below.
If the context does not contain enough information, state what is known and mention that specific policy wording details are limited.

STRICT RULE: Write in natural, easy-to-understand HINGLISH (Hindi written in Roman script) matching the user's prompt style.

Retrieved Policy Context:
{context}

User Question: {question}

Detailed Answer (in Hinglish):
"""

def is_query_hinglish(query: str) -> bool:
    """Detects whether query is written in Hinglish using exact word boundary matching."""
    hinglish_words = [
        "kitna", "kya", "kaise", "mein", "me", "hai", "h", "batao", "bataiye", "chahiye",
        "wale", "wala", "wali", "kaunsa", "kaunsi", "de", "do", "karo", "kab", "kyun", "hoga"
    ]
    query_words = re.findall(r'\b\w+\b', query.lower())
    return any(w in query_words for w in hinglish_words)

_CACHED_VECTOR_DB = None
_CACHED_EMBEDDINGS = None

BRAND_SYNONYMS = {
    "nivabupa": "niva",
    "hdfcergo": "hdfc",
    "icicilombard": "icici",
    "carehealth": "care",
    "manipalcigna": "manipal",
    "tataaig": "tata",
    "starhealth": "star",
    "bajajallianz": "bajaj"
}

def get_vector_db():
    """In-memory singleton cache for loaded FAISS vector database."""
    global _CACHED_VECTOR_DB, _CACHED_EMBEDDINGS
    if not os.path.exists(FAISS_INDEX_DIR) or not os.path.exists(os.path.join(FAISS_INDEX_DIR, "index.faiss")):
        return None

    if _CACHED_VECTOR_DB is None:
        from langchain_community.vectorstores import FAISS
        if _CACHED_EMBEDDINGS is None:
            _CACHED_EMBEDDINGS = get_embeddings()
        _CACHED_VECTOR_DB = FAISS.load_local(
            FAISS_INDEX_DIR,
            _CACHED_EMBEDDINGS,
            allow_dangerous_deserialization=True
        )
    return _CACHED_VECTOR_DB

def invalidate_vector_db_cache():
    """Invalidates in-memory vector store cache after new PDF ingestion."""
    global _CACHED_VECTOR_DB
    _CACHED_VECTOR_DB = None

def compute_faiss_confidence_score(distance: float) -> int:
    """Normalizes FAISS L2 Euclidean distance into a 0-100 percentage score."""
    if distance is None:
        return 90
    norm = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
    return int(round(norm * 100))

def query_faiss_index(query: str, top_k: int = 4, target_brand: str = ""):
    """Searches local FAISS vector store for relevant policy text chunks and top L2 distance."""
    vector_db = get_vector_db()
    if not vector_db:
        return [], None

    try:
        results = vector_db.similarity_search_with_score(query, k=12)
        if not results:
            return [], None

        if target_brand:
            brand_results = [
                (d, s) for (d, s) in results
                if target_brand in str(d.metadata.get("provider", "")).lower() or
                   target_brand in str(d.metadata.get("policy_name", "")).lower() or
                   target_brand in d.page_content.lower()
            ]
            selected = brand_results[:top_k] if brand_results else results[:top_k]
        else:
            selected = results[:top_k]

        docs = [d for (d, s) in selected]
        top_distance = selected[0][1] if selected else None
        return docs, top_distance
    except Exception as e:
        print(f"FAISS search exception: {e}")
        return [], None

def extract_query_brand(query: str) -> str:
    """Extracts explicit brand keyword using exact word boundaries and brand synonyms."""
    query_lower = query.lower()
    for syn, norm in BRAND_SYNONYMS.items():
        if syn in query_lower:
            return norm

    brand_keywords = [
        "tata", "aig", "bajaj", "allianz", "aditya", "birla", "manipal", "cigna",
        "star", "hdfc", "ergo", "icici", "lombard", "niva", "bupa", "religare", "care"
    ]
    for b in brand_keywords:
        if re.search(r'\b' + re.escape(b) + r'\b', query_lower):
            return b
    return ""

def is_brand_genuinely_in_context(target_brand: str, context_text: str) -> bool:
    """Validates that brand is genuinely present in text rather than generic words like 'medical care'."""
    if not target_brand:
        return True

    if target_brand == "care":
        return bool(re.search(r'\bcare (health|insurance|supreme|advantage|policy|plan)\b', context_text))

    return bool(re.search(r'\b' + re.escape(target_brand) + r'\b', context_text))

def run_rag_tool(query: str) -> tuple[str, bool, int]:
    """
    Main RAG pipeline:
    1. Perform FAISS similarity search with score calculation (similarity_search_with_score).
    2. Validate that target brand is genuinely present in page content.
    3. If missing in page content, trigger web search fallback.
    4. Compute dynamic similarity score from FAISS distance.
    Returns: (answer_text, fallback_triggered_bool, dynamic_confidence_score)
    """
    target_brand = extract_query_brand(query)
    docs, top_distance = query_faiss_index(query, top_k=4, target_brand=target_brand)

    brand_missing = False
    if target_brand and docs:
        context_text = " ".join([d.page_content.lower() for d in docs])
        if not is_brand_genuinely_in_context(target_brand, context_text):
            print(f"[BRAND CONTENT MISMATCH] Target brand '{target_brand}' not genuinely present in text. Triggering web fallback...")
            brand_missing = True
            docs = []

    specific_procedure_terms = [
        "robotic", "cyberknife", "stem cell", "chemotherapy", "organ donor",
        "maternity", "cancer", "restoration", "mental health", "psychiatric", "cataract", "bariatric"
    ]
    query_terms = [t for t in specific_procedure_terms if t in query.lower()]

    term_missing = False
    if query_terms and docs:
        context_text = " ".join([d.page_content.lower() for d in docs])
        if not any(t in context_text for t in query_terms):
            print(f"[TERM CONTENT MISMATCH] Procedure terms {query_terms} missing in text. Triggering web fallback...")
            term_missing = True
            docs = []

    low_confidence = False
    if top_distance is not None:
        conf_score = compute_faiss_confidence_score(top_distance)
        if conf_score < 65 and docs:
            print(f"[LOW FAISS CONFIDENCE] Score {conf_score}% < 65%. Triggering web search fallback...")
            low_confidence = True
            docs = []

    fallback_triggered = False
    fallback_context = ""
    if not docs or brand_missing or term_missing or low_confidence:
        fallback_triggered = True
        provider, prov_score = match_provider(query)
        policy, pol_score = match_policy(query, provider=provider if prov_score >= 75 else None)

        if pol_score >= 75:
            target_name = policy
        elif prov_score >= 75:
            target_name = provider
        else:
            target_name = query

        print(f"\n[FALLBACK TRIGGERED] Searching Web for target: '{target_name} {query}'...")
        web_data = search_policy_web_data(f"{target_name} {query}")
        pdf_urls = web_data.get("pdf_urls", [])
        web_snippets = web_data.get("web_snippets", "")

        ingested_success = False
        for pdf_url in pdf_urls:
            print(f"[INGESTING PDF] Trying PDF URL: {pdf_url}...")
            success = ingest_pdf(pdf_url, provider=target_brand or target_name, policy_name=target_name)
            if success:
                ingested_success = True
                invalidate_vector_db_cache()
                break

        if ingested_success:
            docs, top_distance = query_faiss_index(query, top_k=4, target_brand=target_brand)
            if target_brand and docs:
                context_text = " ".join([d.page_content.lower() for d in docs])
                if not is_brand_genuinely_in_context(target_brand, context_text):
                    print(f"[REJECTING MISMATCHED PDF] Ingested PDF did not match target brand '{target_brand}'. Using web search snippets directly...")
                    docs = []
                    fallback_context = web_snippets
        elif web_snippets:
            print("[USING WEB SNIPPETS] PDF download timed out or unavailable. Using web search snippets directly...")
            fallback_context = web_snippets

    context_parts = []
    if docs:
        selected_docs = docs[:4]
        doc_context = "\n\n".join([
            f"--- Document Chunk (Source: {d.metadata.get('policy_name', 'general')}) ---\n{d.page_content}"
            for d in selected_docs
        ])
        context_parts.append(doc_context)

    if fallback_context:
        context_parts.append(f"--- Live Web Search Results ---\n{fallback_context}")

    context_str = "\n\n".join(context_parts) if context_parts else "No specific policy document chunks found in vector index."

    # Compute dynamic confidence score from FAISS top chunk distance
    dynamic_score = compute_faiss_confidence_score(top_distance)

    # Select language-specific prompt template
    if is_query_hinglish(query):
        prompt_template = HINGLISH_RAG_PROMPT_TEMPLATE
    else:
        prompt_template = ENGLISH_RAG_PROMPT_TEMPLATE

    prompt = PromptTemplate.from_template(prompt_template)
    formatted_prompt = prompt.format(context=context_str, question=query)

    response = light_model.invoke(formatted_prompt)
    return response.content.strip(), fallback_triggered, dynamic_score

if __name__ == "__main__":
    print("=== Testing Dynamic RAG Distance Calculation ===")
    q1 = "What is the pre-existing disease waiting period in Niva Bupa ReAssure policy?"
    ans, fb, score = run_rag_tool(q1)
    print(f"\nQuery: '{q1}' (Fallback: {fb}, Dynamic Score: {score}%)")
    print(ans)
