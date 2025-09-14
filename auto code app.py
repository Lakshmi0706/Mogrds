import streamlit as st
import pandas as pd
import re
from duckduckgo_search import DDGS  # safer than googlesearch

# --- Utility: Clean domain into merchant name ---
def domain_to_merchant(domain: str) -> str:
    domain = domain.lower()
    domain = re.sub(r'^www\.', '', domain)
    name = domain.split('.')[0]  # take part before .com/.net

    # Expand common known short forms
    mapping = {
        "cvs": "CVS Pharmacy",
        "bj": "BJ's Wholesale",
        "bjs": "BJ's Wholesale",
        "kmart": "Kmart",
        "homedepot": "Home Depot",
        "dollartree": "Dollar Tree",
        "foodbazaar": "Food Bazaar",
        "racetrac": "Race Trac",
        "murphyusa": "Murphy USA",
        "sprouts": "Sprouts Farmers Market",
        "frysfood": "Fry's Food Store",
    }
    if name in mapping:
        return mapping[name]

    # Default: title case words
    return name.replace("-", " ").replace("_", " ").title()

# --- Utility: Get first official domain ---
def get_official_domain(query: str) -> str:
    with DDGS() as ddgs:
        results = ddgs.text(query, region="us-en", max_results=10)
        for r in results:
            url = r.get("href", "")
            if any(x in url for x in ["facebook.com", "linkedin.com", "wikipedia.org", "instagram.com", "yelp.com", "reddit.com"]):
                continue
            # Extract domain
            match = re.search(r"https?://([^/]+)/?", url)
            if match:
                return match.group(1)
    return None

# --- Streamlit App ---
st.title("Retailer OCR → Merchant Name Finder")

uploaded_file = st.file_uploader("Upload CSV with 'Retailer Name' column", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Loaded {len(df)} retailers from CSV")

    if st.button("Run Search"):
        results = []

        for retailer in df["Retailer Name"]:
            query = f"{retailer} USA site:.com"
            domain = get_official_domain(query)

            if domain:
                merchant = domain_to_merchant(domain)
                status = "YES"
            else:
                merchant = None
                status = "NO"

            results.append({
                "Retailer Name": retailer,
                "Merchant Name": merchant,
                "Status": status
            })

        results_df = pd.DataFrame(results)
        st.dataframe(results_df)

        # Download option
        st.download_button(
            "Download Results as CSV",
            results_df.to_csv(index=False).encode("utf-8"),
            "merchant_results.csv",
            "text/csv"
        )
