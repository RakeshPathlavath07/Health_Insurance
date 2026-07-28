"""
Web Search Agent — Finds policy document PDF URLs & live web search snippets using Tavily Search.
Prioritizes official brand PDF links.
"""
import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()
tavily_key = os.getenv("TAVILY_API_KEY")

BRAND_DOMAIN_MAP = {
    "star": "starhealth",
    "care": "careinsurance",
    "hdfc": "hdfcergo",
    "icici": "icicilombard",
    "niva": "nivabupa",
    "tata": "tataaig",
    "bajaj": "bajajallianz"
}

def search_policy_web_data(policy_name: str) -> dict:
    """
    Searches the web for policy details, brochure text, and candidate PDF URLs.
    Returns dict: {"pdf_urls": list[str], "web_snippets": str}
    """
    if not tavily_key:
        print("TAVILY_API_KEY is not set.")
        return {"pdf_urls": [], "web_snippets": ""}

    try:
        tool = TavilySearchResults(max_results=5)
        query = f"{policy_name} health insurance waiting period pre existing disease brochure details"
        results = tool.invoke({"query": query})

        candidate_urls = []
        snippets = []

        query_brand = ""
        for b in BRAND_DOMAIN_MAP.keys():
            if b in policy_name.lower():
                query_brand = b
                break

        if isinstance(results, list):
            for res in results:
                url = res.get("url", "")
                content = res.get("content", "")
                if content:
                    snippets.append(f"Source ({url}):\n{content}")
                if "csccloud.in" in url:
                    continue
                if url.lower().endswith(".pdf") or "pdf" in url.lower():
                    candidate_urls.append(url)

        # Prioritize brand-matching URLs if present
        if query_brand and candidate_urls:
            brand_keyword = BRAND_DOMAIN_MAP.get(query_brand, query_brand)
            matched_urls = [u for u in candidate_urls if brand_keyword in u.lower() or query_brand in u.lower()]
            other_urls = [u for u in candidate_urls if u not in matched_urls]
            candidate_urls = matched_urls + other_urls

        return {
            "pdf_urls": candidate_urls,
            "web_snippets": "\n\n".join(snippets)
        }
    except Exception as e:
        print(f"Web search agent exception: {e}")
        return {"pdf_urls": [], "web_snippets": ""}

def find_policy_pdf_urls(policy_name: str) -> list[str]:
    data = search_policy_web_data(policy_name)
    return data.get("pdf_urls", [])

def find_policy_pdf_url(policy_name: str) -> str:
    urls = find_policy_pdf_urls(policy_name)
    return urls[0] if urls else ""

if __name__ == "__main__":
    print("=== Testing Brand-Prioritized Web Search Data ===")
    data = search_policy_web_data("Star Cancer Care Gold Policy")
    print(f"Candidate PDF URLs: {data['pdf_urls']}")
    print(f"Snippets Preview:\n{data['web_snippets'][:300]}")
