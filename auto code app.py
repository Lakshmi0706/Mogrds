import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
 
# Function to search official merchant site
def search_official_site(retailer_name):
    query = f"{retailer_name} USA official site"
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=10)]
    for r in results:
        url = r.get("href", "")
        title = r.get("title", "")
        # Skip unwanted sites
        if any(bad in url for bad in ["facebook.com", "instagram.com", "wikipedia.org", 
                                      "linkedin.com", "yelp.com", "twitter.com"]):
            continue
        return title, url
    return None, None
 
# Streamlit App
st.title("Retailer Finder (CSV Upload + Results Export)")
 
uploaded_file = st.file_uploader("Upload Retailers CSV", type=["csv"])
 
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success(f"Loaded {len(df)} retailers from CSV")
 
    if st.button("Run Search"):
        results = []
        for retailer in df["Retailer Name"].dropna().unique():
            merchant_name, url = search_official_site(retailer)
            if merchant_name:
                status = "YES"
            else:
                status = "NO"
            results.append({
                "Retailer Name": retailer,
                "Merchant Name": merchant_name if merchant_name else "None",
                "Status": status
            })
 
        results_df = pd.DataFrame(results)
        st.write(results_df)
 
        # Download results
        csv = results_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Results as CSV", csv, "retailer_results.csv", "text/csv")
