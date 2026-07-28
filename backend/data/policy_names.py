"""
Canonical provider and insurance names used across MongoDB queries,
risk tools, and fuzzy matching utilities.
"""

PROVIDERS = [
    "icici-lombard",
    "niva-bupa",
    "care-health",
    "hdfc-ergo",
    "star-health"
]

POLICIES = {
    "icici-lombard": [
        "icici-lombard-max-protect-classic",
        "icici-lombard-health-advait"
    ],
    "niva-bupa": [
        "niva-bupa-reassure-2-0",
        "niva-bupa-health-companion"
    ],
    "care-health": [
        "care-health-care-supreme",
        "care-health-care-advantage"
    ],
    "hdfc-ergo": [
        "hdfc-ergo-optima-secure",
        "hdfc-ergo-my-health-suraksha"
    ],
    "star-health": [
        "star-health-comprehensive",
        "star-health-young-star"
    ]
}
