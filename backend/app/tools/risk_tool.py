"""
Insurer Financial Risk Assessment Tool
Retrieves IRDAI FY2024 metric records (CSR, ICR, Solvency Ratios)
for requested insurance providers (or all providers if general query).
"""
import os
import json
import re
from backend.app.tools.fuzzy_matcher import match_provider, PROVIDER_ALIASES

DATA_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/risk_data.json")
)

def load_risk_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"data": {}}

RISK_DATA = load_risk_data().get("data", {})

def extract_all_providers(query: str) -> list[str]:
    """Extracts all matching canonical provider names from query string."""
    query_lower = query.lower()
    found_providers = []
    
    for alias, canonical in PROVIDER_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', query_lower):
            if canonical not in found_providers:
                found_providers.append(canonical)

    if not found_providers:
        prov, score = match_provider(query)
        if prov and score >= 50:
            found_providers.append(prov)

    return found_providers

def get_insurer_risk(query: str) -> str:
    """
    Retrieves financial risk metrics for requested providers.
    If no specific provider is mentioned, returns metrics for ALL insurers in IRDAI records.
    """
    providers = extract_all_providers(query)

    # If no explicit provider mentioned, return ALL insurers for general queries
    if not providers:
        providers = list(RISK_DATA.keys())

    output_blocks = ["--- Insurer Risk & Settlement Metrics (IRDAI FY2024) ---"]
    for prov in providers:
        if prov not in RISK_DATA:
            continue

        metrics = RISK_DATA[prov]
        name = metrics.get("display_name", prov)
        csr = metrics.get("CSR", "N/A")
        icr = metrics.get("ICR", "N/A")
        solvency = metrics.get("solvency_ratio", "N/A")
        assessment = metrics.get("summary", "N/A")

        block = (
            f"Provider: {name}\n"
            f"• Claim Settlement Ratio (CSR): {csr} (Higher is better)\n"
            f"• Incurred Claim Ratio (ICR): {icr} (Ideal range: 65%-90%)\n"
            f"• Solvency Ratio: {solvency} (Regulatory min: 1.5)\n"
            f"Financial Assessment: {assessment}"
        )
        output_blocks.append(block)

    return "\n\n".join(output_blocks).strip()

if __name__ == "__main__":
    print("=== Testing General Financial Risk Metric Query ===")
    q1 = "Which insurers have an Incurred Claim Ratio (ICR) within the ideal range of 65% to 90%?"
    print(f"Query: '{q1}'\n")
    print(get_insurer_risk(q1))
