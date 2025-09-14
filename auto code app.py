import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from urllib.parse import urlparse
from difflib import SequenceMatcher

# Extract domain name as simplified retailer name
def extract_domain_name(url):
    try:
        domain = urlparse(url).netloc
        return domain.replace("www.", "").split(".")[0].capitalize()
    except:
        return "Unknown"

# Compute similarity score
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# Search for official site and return simplified name if similarity > 0.8
def get_retailer_name(retailer_input):
    query = f"{retailer_input} USA official site"
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=10)]
    for r in results:
        url = r.get("href", "")
        if any(bad in url for bad in [
            "facebook.com", "instagram.com", "wikipedia.org", 
            "linkedin.com", "yelp.com", "twitter.com", "pinterest.com"
        ]):
            continue
        matched_name = extract_domain_name(url)
        if similarity(retailer_input, matched_name) >= 0.8:
            return matched_name
    return None

# Streamlit App
st.title("Retailer Name Matcher (CSV Upload with Fuzzy Matching)")

uploaded_file = st.file_uploader("Upload Retailers CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    if "Retailer Name" not in df.columns:
        st.error("CSV must contain a 'Retailer Name' column.")
    else:
        st.success(f"Loaded {len(df)} retailers from CSV")

        if st.button("Run Matching"):
            results = []

            for retailer in df["Retailer Name"].dropna().unique():
                matched_name = get_retailer_name(retailer)
                status = "YES" if matched_name else "NO"
                results.append({
                    "Input Retailer Name": retailer,
                    "Matched Retailer Name": matched_name if matched_name else "Not Found",
                    "Status": status
                })

            results_df = pd.DataFrame(results)
            st.write("### Matched Retailer Names", results_df)

            # Download results
            csv = results_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name="matched_retailers.csv",
                mime="text/csv"
            )
