import streamlit as st
import pandas as pd
from googlesearch import search
from urllib.parse import urlparse

# ---------- Helper Functions ----------
def get_official_site(query):
    """
    Google search to find the first official retailer website
    ignoring social media & wiki-type sites.
    """
    try:
        for url in search(query + " USA", num_results=10):
            url = url.lower()
            if any(ext in url for ext in [".com", ".us", ".net"]):
                if not any(bad in url for bad in ["facebook", "instagram", "wikipedia", 
                                                  "linkedin", "yelp", "twitter", "tiktok"]):
                    return url
    except Exception as e:
        return None
    return None

def extract_name(url):
    """
    Extract clean merchant name from domain.
    Example: www.dollartree.com -> Dollar Tree
    """
    if not url:
        return None
    domain = urlparse(url).netloc
    domain = domain.replace("www.", "").split(".")[0]
    return domain.replace("-", " ").title()

# ---------- Streamlit UI ----------
st.title("Retailer Merchant Finder")

uploaded_file = st.file_uploader("Upload your retailers CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "Retailer Name" not in df.columns:
        st.error("CSV must contain a 'Retailer Name' column.")
    else:
        st.success(f"Loaded {len(df)} retailers from CSV")

        if st.button("Run Search"):
            results = []
            for retailer in df["Retailer Name"]:
                official_site = get_official_site(retailer)
                if official_site:
                    merchant = extract_name(official_site)
                    status = "YES"
                else:
                    merchant = None
                    status = "NO"
                results.append([retailer, merchant, status])

            result_df = pd.DataFrame(results, columns=["Retailer Name", "Merchant Name", "Status"])

            st.dataframe(result_df)

            # Download option
            csv = result_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download Results as CSV", data=csv, file_name="merchant_results.csv", mime="text/csv")
