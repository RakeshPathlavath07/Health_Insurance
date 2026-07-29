"""
Guardrails — Output Validation Module
Ensures dispatcher outputs adhere to citation facts and safety rules.
"""
import re

KNOWN_BRANDS = {
    "ICICI Lombard": ["icici", "max protect"],
    "Niva Bupa": ["niva bupa", "nivabupa", "reassure", "re-assure", "health companion"],
    "HDFC Ergo": ["hdfc", "optima secure"],
    "Care Health": ["care health", "care supreme"],
    "Star Health": ["star health", "cardiac care"],
    "ManipalCigna": ["manipalcigna", "prohealth"],
    "Tata AIG": ["tata aig", "medicare"],
    "Bajaj Allianz": ["bajaj", "health guard"]
}

def validate_response(query: str, raw_answer: str, tool_data: str = "") -> str:
    """
    Validates final answer output against retrieved tool context.
    Checks whether provider/policy names mentioned in the final answer were actually present
    in the raw tool output or user query. Flags and annotates ungrounded provider references.
    """
    if not raw_answer or not raw_answer.strip():
        return "I apologize, but I could not generate a response. Please rephrase your question."

    if not tool_data or not tool_data.strip():
        return raw_answer

    ans_lower = raw_answer.lower()
    tool_lower = tool_data.lower()
    query_lower = query.lower()

    hallucinated_brands = []
    for brand_display, keywords in KNOWN_BRANDS.items():
        # Check if brand is mentioned in the answer
        mentioned_in_ans = any(kw in ans_lower for kw in keywords)
        if mentioned_in_ans:
            # Check if brand was in retrieved tool data or query
            present_in_context = any(kw in tool_lower or kw in query_lower for kw in keywords)
            if not present_in_context:
                hallucinated_brands.append(brand_display)

    if hallucinated_brands:
        unsupported = ", ".join(hallucinated_brands)
        print(f"[GUARDRAIL HALLUCINATION DETECTED] Answer referenced provider(s) '{unsupported}' absent from retrieved tool context.")
        warning = f"\n\n⚠️ *[Guardrail Note: The response referenced provider details ({unsupported}) that were not present in the retrieved tool context.]*"
        return raw_answer.strip() + warning

    return raw_answer

if __name__ == "__main__":
    print("=== Testing Guardrails Hallucination Check ===")
    test_q = "Compare waiting period for Niva Bupa"
    test_tool_data = "Niva Bupa ReAssure waiting period is 36 months."
    test_hallucinated_ans = "Niva Bupa ReAssure has a 36-month waiting period. Star Health Cardiac Care has a 24-month waiting period."

    validated = validate_response(test_q, test_hallucinated_ans, tool_data=test_tool_data)
    print("\n[VALIDATED OUTPUT]:\n", validated)
