"""
Long-Term User Profile Memory
Manages user preferences (e.g. maternity interest, budget conscious, age group, pre-existing conditions)
stored in MongoDB Atlas collection: insurance_db.user_profile keyed by session_id / user_id.
"""
import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where()) if MONGODB_URI else None
db = client["insurance_db"] if client else None
profile_collection = db["user_profile"] if db is not None else None

PREFERENCE_KEYWORDS = {
    "maternity": ["maternity", "pregnancy", "baby", "newborn"],
    "budget": ["cheap", "affordable", "low cost", "budget", "economical"],
    "senior_citizen": ["senior", "elderly", "parents", "old age", "above 60"],
    "zero_copay": ["zero copay", "no copay", "without copay", "no co-payment"],
    "uncapped_room": ["single room", "suite", "no room capping", "unlimited room"]
}

def get_user_profile(user_id: str) -> dict:
    """Retrieves long-term profile document for a user/session."""
    if profile_collection is None:
        return {}
    try:
        doc = profile_collection.find_one({"user_id": user_id})
        if doc:
            doc.pop("_id", None)
            return doc
    except Exception as e:
        print(f"Error fetching user profile: {e}")
    return {}

def update_user_profile(user_id: str, query: str) -> dict:
    """Opportunistically extracts preferences from user query and updates MongoDB Atlas profile."""
    if profile_collection is None:
        return {}

    query_lower = query.lower()
    extracted_prefs = []

    for pref_key, keywords in PREFERENCE_KEYWORDS.items():
        if any(k in query_lower for k in keywords):
            extracted_prefs.append(pref_key)

    if not extracted_prefs:
        return get_user_profile(user_id)

    try:
        profile_collection.update_one(
            {"user_id": user_id},
            {
                "$addToSet": {"stated_preferences": {"$each": extracted_prefs}},
                "$set": {"last_query": query}
            },
            upsert=True
        )
        return get_user_profile(user_id)
    except Exception as e:
        print(f"Error updating user profile: {e}")
        return get_user_profile(user_id)

def format_profile_for_context(user_id: str) -> str:
    """Formats stated user preferences as a text snippet for LLM dispatcher context."""
    profile = get_user_profile(user_id)
    prefs = profile.get("stated_preferences", [])
    if not prefs:
        return ""
    return f"User Stated Preferences: {', '.join(prefs)}"

if __name__ == "__main__":
    print("=== Testing Long-Term User Profile Memory ===")
    user = "session_demo_123"
    update_user_profile(user, "Looking for a policy with maternity cover and no copay")
    prof = get_user_profile(user)
    print(f"Retrieved MongoDB Profile for '{user}': {prof}")
