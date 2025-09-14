import streamlit as st
import pandas as pd
import re
from rapidfuzz import process, fuzz
from duckduckgo_search import DDGS
import json

# -------------------------
# Load expanded retailer dictionary
# -------------------------
@st.cache_data
def load_retailers():
    # You can maintain this as a JSON file with 1000+ retailer names
    # Example: ["Walmart", "Costco", "Sam's Club", ...]
    try:
        with open("retailers.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # fallback mini-list if file not present
        return [
            "Walmart", "Costco", "Sam's Club", "BJ's Wholesale", "Kroger",
            "Safeway", "Albertsons", "Publix", "Meijer", "Target",
            "Dollar Tree", "Dollar General", "Family Dollar",
            "CVS Pharmacy", "Walgreens", "Rite Aid", "Home Depot", "Lowe's"
        ]

KNOWN_RETAILERS = load_retailers()

# -------------------------
# Domain → Merchant Name
# -------------------------
def domain_to_merchant(domain: str) -> str:
    if not domain:
        return None
    domain = domain.lower()
    domain = re.sub(r'^www\.', '', domain)
    base = domain.split('.')[0]

    mapping = {
        "cvs": "CVS Pharmacy",
        "bjs": "BJ's Wholesale",
        "dollartree": "Dollar Tree",
        "racetrac": "RaceTrac",
        "homedepot": "Home Depot",
        "murphyusa": "Murphy USA",
        "sprouts": "Sprouts Farmers Market",
        "frysfood": "Fry's Food Store"
    }
    if base in mapping:
        return mapping[base]

    return base.replace("-", " ").replace("_", " ").title()

# -------------------------
# Fuzzy correction backup
# -------------------------
def fuzzy_correct(name: str) -> str:
    best_match, score, _ = process.extractOne(
        name, KNOWN_RETAILERS, scorer=fuzz.WRatio
    )
    return best_match if score >= 85 else None

# -------------------------
# DuckDuckGo Search
# -------------------------
def get_official_domain(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, region="us-en", max_results=10)
            for r in results:
                url = r.get("href", "")
                if any(x in url for x in [
                    "facebook.com", "linkedin.com", "wikipedia.org",
                    "instagram.com", "yelp.com", "reddit.com"
                ]):
                    continue
                match = re.search(r"https?://([^/]+)/?", url)
                if match:
                    return match.group(1)
    except Exception:
        return None
    return None

# -------------------------
# Streamlit App
# -------------------------
st.title("🛒 Retailer OCR → Merchant Name Finder (Live Search + Dictionary Fallback)")

uploaded_file = st.file_uploader("Upload CSV with 'Retailer Name' column", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Loaded {len(df)} retailers from CSV")

    if st.button("Run Search"):
        results = []

        for retailer in df["Retailer Name"]:
            ocr_input = str(retailer).strip()

            # Step 1: live search
            query = f"{ocr_input} USA site:.com"
            domain = get_official_domain(query)
            merchant = domain_to_merchant(domain) if domain else None

            # Step 2: fallback fuzzy correction
            if not merchant:
                merchant = fuzzy_correct(ocr_input)

            status = "YES" if merchant else "NO"

            results.append({
                "Retailer Name (OCR Input)": ocr_input,
                "Merchant Name": merchant,
                "Status": status
            })

        results_df = pd.DataFrame(results)
        st.dataframe(results_df)

        st.download_button(
            "📥 Download Results as CSV",
            results_df.to_csv(index=False).encode("utf-8"),
            "merchant_results.csv",
            "text/csv"
        )
