import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from urllib.parse import urlparse

# Function to extract domain name as merchant name
def extract_domain_name(url):
    try:
        domain = urlparse(url).netloc
        return domain.replace("www.", "").split(".")[0].capitalize()
    except:
        return "Unknown"

# Function to search for the official site
def search_official_site(retailer_name):
    query = f"{retailer_name} USA official site"
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=10)]
    for r in results:
        url = r.get("href", "")
        if any(bad in url for bad in [
            "facebook.com", "instagram.com", "wikipedia.org", 
            "linkedin.com", "yelp.com", "twitter.com", "pinterest.com"
        ]):
            continue
        return url
    return None

# Streamlit App
st.title("Retailer Finder (CSV Upload + Results Export)")

uploaded_file = st.file_uploader("Upload Retailers CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    if "Retailer Name" not in df.columns:
        st.error("CSV must contain a 'Retailer Name' column.")
    else:
        st.success(f"Loaded {len(df)} retailers from CSV")

        if st.button("Run Search"):
            results = []

            for retailer in df["Retailer Name"].dropna().unique():
                url = search_official_site(retailer)
                merchant_name = extract_domain_name(url) if url else "Not Found"
                results.append({
                    "Retailer Name": retailer,
                    "Merchant Name (Simplified)": merchant_name,
                    "Official Site URL": url if url else "N/A",
                    "Status": "YES" if url else "NO"
                })

            results_df = pd.DataFrame(results)
            st.write("### Search Results", results_df)

            # Download results
            csv = results_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name="retailer_results.csv",
                mime="text/csv"
            )
