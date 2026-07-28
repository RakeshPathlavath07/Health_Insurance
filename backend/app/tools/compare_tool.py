"""
Compare Tool — Text-to-MongoDB Policy & Feature Comparison
PRIMARY PATH: LLM (deep_model) text-to-PyMongo query generation.
FALLBACK PATH: Deterministic Python MongoDB feature filtering engine.
Logs path execution (llm_success vs llm_fallback with failure_reason) for auditability.
"""
import os
import re
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from langchain_core.prompts import PromptTemplate

# ============================================================
# DEEP MODEL — multi-step reasoning (dispatcher tool routing,
# compare-tool PyMongo query code generation)
# CURRENT: Groq, free tier (llama-3.3-70b-versatile)
# TO REPLACE WITH A DEEP-THINKING MODEL WHEN YOU FIND ONE:
#   1. pip install the new provider's langchain package
#   2. change the import below
#   3. change the class + model name below
#   4. add the new provider's key name to .env
# ============================================================
from langchain_groq import ChatGroq

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")

deep_model = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.0,
    groq_api_key=groq_key
)

MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where()) if MONGODB_URI else None
db = client["insurance_db"] if client else None
collection = db["health_insurance"] if db is not None else None

FORBIDDEN_KEYWORDS = [
    "delete", "drop", "update", "insert", "remove", "$where",
    "eval(", "exec(", "import os", "import sys", "subprocess"
]

FEATURE_KEY_MAP = {
    "waiting": "waiting-period",
    "ped": "waiting-period",
    "room": "room-rent-limit",
    "rent": "room-rent-limit",
    "copay": "co-payment",
    "co-payment": "co-payment",
    "maternity": "maternity-cover",
    "restoration": "restoration-benefit",
    "recharge": "restoration-benefit",
    "day care": "day-care-treatments",
    "bonus": "no-claim-bonus",
    "ncb": "no-claim-bonus",
    "disease": "disease-sub-limit",
    "sublimit": "disease-sub-limit",
    "sub-limit": "disease-sub-limit"
}

POLICY_KEYWORDS = [
    "reassure", "optima", "secure", "supreme", "classic",
    "advait", "companion", "advantage", "comprehensive"
]

COMPARE_QUERY_GEN_PROMPT = """
You are a PyMongo expert for an Indian Health Insurance MongoDB Atlas database.
Database Collection: `collection` (contains documents representing health insurance policies).

Document Schema Example:
{{
  "provider": "icici-lombard" | "niva-bupa" | "care-health" | "hdfc-ergo" | "star-health",
  "insurance_name": "policy-name-slug",
  "features": {{
    "co-payment": {{"rating": "good", "details": "No co-payment for age < 60 years"}},
    "room-rent-limit": {{"rating": "good", "details": "No room rent capping for single private room"}},
    "pre-post-hospitalization": {{"rating": "good", "details": "60 days pre-hospitalization"}},
    "restoration-benefit": {{"rating": "good", "details": "100% restoration"}},
    "day-care-treatments": {{"rating": "good", "details": "All day care procedures covered"}},
    "waiting-period": {{"rating": "average", "details": "30 days initial, 36 months for pre-existing diseases"}},
    "no-claim-bonus": {{"rating": "good", "details": "50% increase in sum insured"}},
    "maternity-cover": {{"rating": "bad", "details": "Not covered"}},
    "disease-sub-limit": {{"rating": "good", "details": "No sub-limits on specific diseases"}}
  }}
}}

Available feature keys: "co-payment", "room-rent-limit", "pre-post-hospitalization", "restoration-benefit", "day-care-treatments", "waiting-period", "no-claim-bonus", "maternity-cover", "disease-sub-limit".

CRITICAL RULE FOR FILTERING:
Always query feature ratings (`"features.<key>.rating": "good"`) or regex on details (`"features.<key>.details": {{"$regex": "no|zero|uncapped", "$options": "i"}}`). NEVER do exact equality matching on "details" strings.

FEW-SHOT EXAMPLES:

Example 1: "Which policies offer zero room rent capping?"
Python Code: list(collection.find({{"features.room-rent-limit.rating": "good"}}))

Example 2: "Compare waiting periods of Niva Bupa ReAssure and Care Supreme"
Python Code: list(collection.find({{"provider": {{"$in": ["niva-bupa", "care-health"]}}}}))

Example 3: "Does ICICI Lombard Max Protect have co-payment?"
Python Code: list(collection.find({{"provider": "icici-lombard"}}))

Example 4: "Which policies include maternity coverage?"
Python Code: list(collection.find({{"features.maternity-cover.rating": {{"$in": ["good", "average"]}}}}))

User Question: "{query}"

Write a single valid Python expression returning a list of matching documents from `collection`.
Return ONLY the raw Python code line (no markdown formatting, no explanations).

Python Code:
"""

PATH_LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "compare_tool_paths.log")

def log_compare_path(status: str, query: str, failure_reason: str = None, code_generated: str = None):
    """Logs llm_success or llm_fallback with failure_reason for auditability."""
    try:
        os.makedirs(os.path.dirname(PATH_LOG_FILE), exist_ok=True)
        with open(PATH_LOG_FILE, "a") as f:
            if status == "llm_success":
                f.write(f"llm_success | query='{query}' | code='{code_generated}'\n")
            else:
                f.write(f"llm_fallback | failure_reason='{failure_reason}' | query='{query}' | code='{code_generated}'\n")
    except Exception as e:
        print(f"Logging error: {e}")

def is_query_safe(code_str: str) -> bool:
    """Validates that generated Python string contains no destructive or forbidden commands."""
    code_lower = code_str.lower()
    for forbidden in FORBIDDEN_KEYWORDS:
        if forbidden in code_lower:
            return False
    return True

def extract_target_features(query: str) -> list[str]:
    """Extracts target feature keys mentioned in user query."""
    query_lower = query.lower()
    targets = []
    for keyword, feat_key in FEATURE_KEY_MAP.items():
        if keyword in query_lower and feat_key not in targets:
            targets.append(feat_key)
    return targets

def format_policy_documents(docs: list[dict], target_features: list[str] = None, requires_good_rating: bool = False) -> str:
    """Formats retrieved MongoDB policy documents into clean readable text."""
    if not docs:
        return ""

    output_lines = []
    for doc in docs:
        provider = doc.get("provider", "").upper()
        policy = doc.get("insurance_name", "")
        features = doc.get("features", {})

        if target_features:
            display_features = {k: v for k, v in features.items() if k in target_features}
        else:
            display_features = features

        if not display_features:
            display_features = features

        if requires_good_rating and target_features:
            valid_features = {}
            for feat_name, feat_data in display_features.items():
                if isinstance(feat_data, dict):
                    rating = feat_data.get("rating", "").lower()
                    details = feat_data.get("details", "").lower()
                    if rating == "good" or "no " in details or "zero" in details or "uncapped" in details:
                        valid_features[feat_name] = feat_data
            display_features = valid_features

        if not display_features:
            continue

        output_lines.append(f"• Policy: {policy} (Provider: {provider})")
        for feat_name, feat_data in display_features.items():
            if isinstance(feat_data, dict):
                rating = feat_data.get("rating", "")
                details = feat_data.get("details", "")
                output_lines.append(f"  - {feat_name}: [{rating}] {details}")
        output_lines.append("")

    return "\n".join(output_lines).strip() if output_lines else ""

def deterministic_fallback_engine(query: str) -> str:
    """Deterministic Python MongoDB document filtering engine (Fallback Path)."""
    query_lower = query.lower()
    target_features = extract_target_features(query)

    all_docs = list(collection.find({}))
    if not all_docs:
        return "No policies found in database."

    requires_good_rating = any(k in query_lower for k in ["zero", "no capping", "without capping", "no co-payment", "good", "best", "included", "have zero"])
    specific_policy_terms = [k for k in POLICY_KEYWORDS if k in query_lower]

    matching_docs = []
    for doc in all_docs:
        pol_name = doc.get("insurance_name", "").lower()
        prov_name = doc.get("provider", "").lower()

        if specific_policy_terms:
            if any(term in pol_name for term in specific_policy_terms):
                matching_docs.append(doc)
        else:
            prov_tokens = [t for t in prov_name.split("-") if len(t) > 3]
            if any(t in query_lower for t in prov_tokens):
                matching_docs.append(doc)

    if not matching_docs:
        matching_docs = all_docs

    output_lines = []
    for doc in matching_docs:
        provider = doc.get("provider", "").upper()
        policy = doc.get("insurance_name", "")
        features = doc.get("features", {})

        if target_features:
            display_features = {k: v for k, v in features.items() if k in target_features}
        else:
            display_features = features

        if not display_features:
            display_features = features

        if requires_good_rating and target_features:
            valid_features = {}
            for feat_name, feat_data in display_features.items():
                if isinstance(feat_data, dict):
                    rating = feat_data.get("rating", "").lower()
                    details = feat_data.get("details", "").lower()
                    if rating == "good" or "no " in details or "zero" in details or "uncapped" in details:
                        valid_features[feat_name] = feat_data
            display_features = valid_features

        if not display_features:
            continue

        output_lines.append(f"• Policy: {policy} (Provider: {provider})")
        for feat_name, feat_data in display_features.items():
            if isinstance(feat_data, dict):
                rating = feat_data.get("rating", "")
                details = feat_data.get("details", "")
                output_lines.append(f"  - {feat_name}: [{rating}] {details}")
        output_lines.append("")

    return "\n".join(output_lines).strip() if output_lines else "No policies found matching the criteria."

def run_compare_tool(query: str) -> str:
    """
    Executes policy feature comparison query.
    PRIMARY PATH: LLM (deep_model) PyMongo query generation.
    FALLBACK PATH: Deterministic Python MongoDB filtering engine.
    """
    if collection is None:
        return "Database connection error: MongoDB collection not initialized."

    if not is_query_safe(query):
        log_compare_path("llm_fallback", query, failure_reason="safety_blocked", code_generated=query)
        return "Security Alert: Input contains forbidden operations."

    code_clean = ""
    # --- PRIMARY PATH: LLM PyMongo Query Generation ---
    try:
        prompt = PromptTemplate.from_template(COMPARE_QUERY_GEN_PROMPT)
        formatted_prompt = prompt.format(query=query)
        gen_response = deep_model.invoke(formatted_prompt).content.strip()

        code_clean = gen_response
        if "```python" in code_clean:
            code_clean = code_clean.split("```python")[1].split("```")[0].strip()
        elif "```" in code_clean:
            code_clean = code_clean.split("```")[1].split("```")[0].strip()

        print(f"--> [COMPARE TOOL PRIMARY PATH] Generated Code: {code_clean}")

        if not is_query_safe(code_clean) or not ("collection.find" in code_clean or "collection.aggregate" in code_clean):
            log_compare_path("llm_fallback", query, failure_reason="safety_blocked", code_generated=code_clean)
            return deterministic_fallback_engine(query)

        local_scope = {"collection": collection, "list": list}
        retrieved_docs = eval(code_clean, {"__builtins__": None}, local_scope)

        if isinstance(retrieved_docs, list) and len(retrieved_docs) > 0:
            target_features = extract_target_features(query)
            requires_good = any(k in query.lower() for k in ["zero", "no capping", "without capping", "no co-payment", "good", "best", "included", "have zero"])
            formatted_result = format_policy_documents(retrieved_docs, target_features, requires_good)

            if formatted_result:
                log_compare_path("llm_success", query, code_generated=code_clean)
                return formatted_result
            else:
                log_compare_path("llm_fallback", query, failure_reason="empty_results", code_generated=code_clean)
                return deterministic_fallback_engine(query)
        else:
            log_compare_path("llm_fallback", query, failure_reason="empty_results", code_generated=code_clean)
            return deterministic_fallback_engine(query)

    except Exception as e:
        print(f"--> [COMPARE TOOL PRIMARY PATH EXCEPTION]: {e}")
        log_compare_path("llm_fallback", query, failure_reason="execution_error", code_generated=code_clean)
        return deterministic_fallback_engine(query)

if __name__ == "__main__":
    print("=== Testing Compare Tool Primary LLM Path ===")
    q1 = "Which policies offer zero room rent capping?"
    res = run_compare_tool(q1)
    print(f"\nQuery: '{q1}'\nResult:\n{res}")
