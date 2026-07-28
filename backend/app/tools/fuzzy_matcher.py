"""
Centralized Fuzzy Matcher Utility
Matches noisy/user-entered provider and policy names against canonical registries in policy_names.py
"""
import re
from rapidfuzz import process, fuzz
from backend.data.policy_names import PROVIDERS, POLICIES

PROVIDER_ALIASES = {
    "icici": "icici-lombard",
    "lombard": "icici-lombard",
    "niva": "niva-bupa",
    "bupa": "niva-bupa",
    "max bupa": "niva-bupa",
    "care": "care-health",
    "religare": "care-health",
    "hdfc": "hdfc-ergo",
    "ergo": "hdfc-ergo",
    "star": "star-health",
    "tata": "tata-aig",
    "aig": "tata-aig",
    "bajaj": "bajaj-allianz",
    "aditya": "aditya-birla",
    "manipal": "manipal-cigna"
}

def match_provider(query: str, score_threshold: int = 50):
    """
    Extract best matching canonical provider name from query.
    Returns: (canonical_provider_name, match_score) or (None, 0)
    """
    if not query:
        return None, 0

    query_lower = query.lower()

    # Check direct aliases with word boundary regex to prevent "care" matching "medicare"
    for alias, canonical in PROVIDER_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', query_lower):
            return canonical, 100

    # RapidFuzz match using token_set_ratio to prevent substring collision
    match = process.extractOne(query_lower, PROVIDERS, scorer=fuzz.token_set_ratio)
    if match and match[1] >= score_threshold:
        return match[0], match[1]

    return None, 0

def match_policy(query: str, provider: str = None, score_threshold: int = 50):
    """
    Extract best matching canonical policy name from query.
    """
    if not query:
        return None, 0

    query_lower = query.lower()
    candidate_policies = []

    if provider and provider in POLICIES:
        candidate_policies = POLICIES[provider]
    else:
        for pol_list in POLICIES.values():
            candidate_policies.extend(pol_list)

    match = process.extractOne(query_lower, candidate_policies, scorer=fuzz.token_set_ratio)
    if match and match[1] >= score_threshold:
        return match[0], match[1]

    return None, 0

if __name__ == "__main__":
    test_queries = [
        "What is the pre-existing disease waiting period in Tata AIG MediCare policy?",
        "max bupa reassure",
        "religare care supreme",
        "hdfc optima secure",
        "star comprehensive"
    ]
    for q in test_queries:
        prov, p_score = match_provider(q)
        pol, pol_score = match_policy(q, provider=prov)
        print(f"Query: '{q}' -> Provider: {prov} ({p_score}%), Policy: {pol} ({pol_score}%)")
