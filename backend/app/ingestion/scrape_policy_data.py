"""
Seed script to insert initial policy feature dataset into MongoDB Atlas.
Collection: insurance_db.health_insurance
Contains all 9 planned features:
1. co-payment
2. room-rent-limit
3. pre-post-hospitalization
4. restoration-benefit
5. day-care-treatments
6. waiting-period
7. no-claim-bonus
8. maternity-cover
9. disease-sub-limit
"""
import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

SEED_POLICIES = [
    {
        "provider": "icici-lombard",
        "insurance_name": "icici-lombard-max-protect-classic",
        "description": "Comprehensive health policy with high sum insured and global emergency coverage.",
        "features": {
            "co-payment": {"rating": "good", "details": "No co-payment for age < 60 years"},
            "room-rent-limit": {"rating": "good", "details": "No room rent capping for single private room"},
            "pre-post-hospitalization": {"rating": "good", "details": "60 days pre-hospitalization, 180 days post-hospitalization"},
            "restoration-benefit": {"rating": "good", "details": "100% restoration available once per policy year for any illness"},
            "day-care-treatments": {"rating": "good", "details": "All day care procedures covered up to sum insured"},
            "waiting-period": {"rating": "average", "details": "30 days initial, 36 months for pre-existing diseases (PED)"},
            "no-claim-bonus": {"rating": "good", "details": "50% increase in sum insured per claim-free year up to maximum 100%"},
            "maternity-cover": {"rating": "bad", "details": "Not covered in Classic variant"},
            "disease-sub-limit": {"rating": "good", "details": "No sub-limits on specific diseases or cataract treatments"}
        }
    },
    {
        "provider": "icici-lombard",
        "insurance_name": "icici-lombard-health-advait",
        "description": "Affordable entry-level health plan designed for young individuals and small families.",
        "features": {
            "co-payment": {"rating": "average", "details": "10% co-payment applicable in zone 2/3 hospitals"},
            "room-rent-limit": {"rating": "average", "details": "Capped at 1% of Sum Insured per day for normal room"},
            "pre-post-hospitalization": {"rating": "average", "details": "30 days pre-hospitalization, 60 days post-hospitalization"},
            "restoration-benefit": {"rating": "good", "details": "100% auto-restoration for unrelated illnesses"},
            "day-care-treatments": {"rating": "good", "details": "150+ specified day care procedures covered"},
            "waiting-period": {"rating": "average", "details": "30 days initial, 48 months for pre-existing diseases"},
            "no-claim-bonus": {"rating": "average", "details": "10% increase per claim-free year up to 50%"},
            "maternity-cover": {"rating": "bad", "details": "Not covered"},
            "disease-sub-limit": {"rating": "average", "details": "Cataract capped at 25,000 INR per eye"}
        }
    },
    {
        "provider": "niva-bupa",
        "insurance_name": "niva-bupa-reassure-2-0",
        "description": "Popular policy with Lock-the-Age benefit and carry-forward unutilized sum insured.",
        "features": {
            "co-payment": {"rating": "good", "details": "Zero co-payment across all network hospitals"},
            "room-rent-limit": {"rating": "good", "details": "Any room type covered (including suite room in Platinum plan)"},
            "pre-post-hospitalization": {"rating": "good", "details": "60 days pre-hospitalization, 180 days post-hospitalization"},
            "restoration-benefit": {"rating": "good", "details": "Unlimited automatic restoration for any illness"},
            "day-care-treatments": {"rating": "good", "details": "All day care treatments covered without sub-limits"},
            "waiting-period": {"rating": "good", "details": "30 days initial, 24 months for pre-existing diseases"},
            "no-claim-bonus": {"rating": "good", "details": "ReAssure Forever benefit guarantees cumulative bonus addition"},
            "maternity-cover": {"rating": "average", "details": "Optional add-on available after 24 months waiting period"},
            "disease-sub-limit": {"rating": "good", "details": "No disease sub-limits across modern & robotic surgeries"}
        }
    },
    {
        "provider": "niva-bupa",
        "insurance_name": "niva-bupa-health-companion",
        "description": "Family floater plan offering comprehensive medical coverage and refill benefit.",
        "features": {
            "co-payment": {"rating": "good", "details": "No co-payment across network hospitals"},
            "room-rent-limit": {"rating": "good", "details": "Up to single private room covered"},
            "pre-post-hospitalization": {"rating": "good", "details": "30 days pre-hospitalization, 60 days post-hospitalization"},
            "restoration-benefit": {"rating": "good", "details": "100% refill of base sum insured"},
            "day-care-treatments": {"rating": "good", "details": "All day care procedures covered"},
            "waiting-period": {"rating": "average", "details": "30 days initial, 36 months PED waiting period"},
            "no-claim-bonus": {"rating": "good", "details": "20% bonus per year up to 100%"},
            "maternity-cover": {"rating": "bad", "details": "Not covered"},
            "disease-sub-limit": {"rating": "good", "details": "No capping on specific surgeries or procedures"}
        }
    },
    {
        "provider": "care-health",
        "insurance_name": "care-health-care-supreme",
        "description": "Feature-rich policy with cumulative bonus super and unlimited recharge benefit.",
        "features": {
            "co-payment": {"rating": "good", "details": "No co-payment if age at entry is less than 61 years"},
            "room-rent-limit": {"rating": "good", "details": "No capping on room category"},
            "pre-post-hospitalization": {"rating": "good", "details": "60 days pre-hospitalization, 180 days post-hospitalization"},
            "restoration-benefit": {"rating": "good", "details": "Unlimited automatic recharge of sum insured"},
            "day-care-treatments": {"rating": "good", "details": "500+ day care procedures covered"},
            "waiting-period": {"rating": "good", "details": "30 days initial, 24 months for pre-existing diseases"},
            "no-claim-bonus": {"rating": "good", "details": "50% increase per year up to 500% with Cumulative Bonus Super"},
            "maternity-cover": {"rating": "good", "details": "Covered under optional rider after 24 months"},
            "disease-sub-limit": {"rating": "good", "details": "No sub-limits on disease treatment or joint replacements"}
        }
    },
    {
        "provider": "care-health",
        "insurance_name": "care-health-care-advantage",
        "description": "High sum insured plan offering 1 Crore cover at competitive premiums.",
        "features": {
            "co-payment": {"rating": "good", "details": "No co-payment applicable"},
            "room-rent-limit": {"rating": "good", "details": "Single private room category covered"},
            "pre-post-hospitalization": {"rating": "good", "details": "60 days pre-hospitalization, 90 days post-hospitalization"},
            "restoration-benefit": {"rating": "good", "details": "Automatic restoration of sum insured once per year"},
            "day-care-treatments": {"rating": "good", "details": "All day care procedures covered"},
            "waiting-period": {"rating": "average", "details": "30 days initial, 48 months pre-existing disease waiting period"},
            "no-claim-bonus": {"rating": "good", "details": "10% increase per year up to 50%"},
            "maternity-cover": {"rating": "bad", "details": "Not available"},
            "disease-sub-limit": {"rating": "good", "details": "No sub-limits applicable on cardiac or cancer treatments"}
        }
    },
    {
        "provider": "hdfc-ergo",
        "insurance_name": "hdfc-ergo-optima-secure",
        "description": "Flagship product offering 4X coverage (2X base cover on day 1 + 100% secure benefit + 100% bonus).",
        "features": {
            "co-payment": {"rating": "good", "details": "Zero co-payment across India"},
            "room-rent-limit": {"rating": "good", "details": "No room rent capping or category limits"},
            "pre-post-hospitalization": {"rating": "good", "details": "60 days pre-hospitalization, 180 days post-hospitalization"},
            "restoration-benefit": {"rating": "good", "details": "100% automatic restore for subsequent claims"},
            "day-care-treatments": {"rating": "good", "details": "All day care medical procedures covered"},
            "waiting-period": {"rating": "good", "details": "30 days initial, 36 months PED waiting period (reducible to 24)"},
            "no-claim-bonus": {"rating": "good", "details": "50% increase per year up to 100% with Plus benefit"},
            "maternity-cover": {"rating": "bad", "details": "Not covered in Optima Secure"},
            "disease-sub-limit": {"rating": "good", "details": "No sub-limits or capping on any medical condition"}
        }
    },
    {
        "provider": "star-health",
        "insurance_name": "star-health-comprehensive",
        "description": "Widely popular family policy with built-in maternity, newborn cover, and dental benefits.",
        "features": {
            "co-payment": {"rating": "good", "details": "Nil co-payment for entry age up to 65 years"},
            "room-rent-limit": {"rating": "good", "details": "Single private A/C room allowed"},
            "pre-post-hospitalization": {"rating": "good", "details": "60 days pre-hospitalization, 90 days post-hospitalization"},
            "restoration-benefit": {"rating": "good", "details": "100% automatic restoration upon partial/full exhaustion"},
            "day-care-treatments": {"rating": "good", "details": "All day care procedures covered"},
            "waiting-period": {"rating": "average", "details": "30 days initial, 36 months for pre-existing conditions"},
            "no-claim-bonus": {"rating": "good", "details": "50% increase in 1st year, 10% in subsequent years up to 100%"},
            "maternity-cover": {"rating": "good", "details": "Maternity and newborn covered after 24 months waiting period"},
            "disease-sub-limit": {"rating": "average", "details": "Cataract sub-limit up to 50,000 INR per policy period"}
        }
    }
]

def seed_mongodb():
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI environment variable is missing in .env")

    client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
    db = client["insurance_db"]
    collection = db["health_insurance"]

    collection.delete_many({})
    print("Cleared existing records in 'insurance_db.health_insurance'.")

    result = collection.insert_many(SEED_POLICIES)
    print(f"Successfully inserted {len(result.inserted_ids)} policy documents with all 9 features into MongoDB Atlas!")

    sample = collection.find_one({"provider": "hdfc-ergo"})
    print("\nSample retrieved document (HDFC ERGO):")
    print(f"- Provider: {sample.get('provider')}")
    print(f"- Policy: {sample.get('insurance_name')}")
    print(f"- Features keys: {list(sample.get('features', {}).keys())}")

if __name__ == "__main__":
    seed_mongodb()
