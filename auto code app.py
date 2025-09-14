import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from urllib.parse import urlparse

# --------- Helper functions ---------
def get_official_site(query):
    """Search DuckDuckGo for the official site of a retailer."""
    search_query = f"{query} USA"
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(search_query, max_results=10)]
    for r in results:
        url = r.get("href", "").lower()
        if any(ext in url for ext in [".com", ".us", ".net"]):
            if not any(bad in url for bad in ["facebook", "instagram", "wikipedia", 
                                              "linkedin", "yelp", "twitter", "tiktok"]):
                return url
    return None

def extract_merchant_name(url):
    """Extract merchant name from domain."""
    if not url:
        return None
    domain = urlparse(url).netloc
    domain = domain.replace("www.", "").split(".")[0]
    return domain.replace("-", " ").upper()

# --------- Streamlit app ---------
st.title("Retailer OCR → Merchant Name Finder")

uploaded_file = st.file_uploader("Upload CSV with 'Retailer Name' column", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "Retailer Name" not in df.columns:
        st.error("CSV must contain a 'Retailer Name' column.")
    else:
        st.success(f"Loaded {len(df)} retailers")

        if st.button("Run Search"):
            results = []
            for raw in df["Retailer Name"]:
                site = get_official_site(raw)
                if site:
                    merchant = extract_merchant_name(site)
                    status = "YES"
                else:
                    merchant = None
                    status = "NO"
                results.append([raw, merchant, status])

            result_df = pd.DataFrame(results, columns=["Retailer Name", "Merchant Name", "Status"])
            st.dataframe(result_df)

            # Download option
            csv = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Results as CSV", csv, "merchant_results.csv", "text/csv")
