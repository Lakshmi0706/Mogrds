import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS

# Load retailer names from Excel
try:
    retailer_df = pd.read_excel("retailer.xlsx", engine="openpyxl")
    retailer_names = retailer_df.iloc[:, 0].dropna().unique()
except Exception as e:
    st.error(f"Error loading retailer.xlsx: {e}")
    retailer_names = []

# Function to search for merchant name using DuckDuckGo
def get_merchant_name(retailer_name):
    query = f"{retailer_name} USA official site"
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=10)]
    for r in results:
        title = r.get("title", "")
        url = r.get("href", "")
        if any(bad in url for bad in [
            "facebook.com", "instagram.com", "wikipedia.org", 
            "linkedin.com", "yelp.com", "twitter.com", "pinterest.com"
        ]):
            continue
        return title
    return "Not Found"

# Streamlit App
st.title("Retailer Merchant Extractor")

if st.button("Run Merchant Extraction"):
    results = []
    for name in retailer_names:
        merchant = get_merchant_name(name)
        results.append({
            "Retailer Name": name,
            "Merchant Name": merchant
        })

    results_df = pd.DataFrame(results)
    st.write("### Extracted Merchant Names", results_df)

    csv = results_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Results as CSV", csv, "retailer_merchant_mapping.csv", "text/csv")
