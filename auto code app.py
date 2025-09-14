import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# ---------- Helper function to extract merchant name ----------
def get_merchant_name(retailer):
    try:
        query = f"{retailer} USA official site"
        url = f"https://www.google.com/search?q={query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Look for the first search result <h3>
        h3 = soup.find("h3")
        if h3:
            merchant = h3.get_text().strip()
            # Clean merchant name
            merchant = re.sub(r"[-|•].*", "", merchant).strip()
            return merchant
        return None
    except Exception:
        return None


# ---------- Streamlit App ----------
st.title("Retailer Finder (CSV Upload + Results Export)")

uploaded_file = st.file_uploader("Upload Retailers CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if "Retailer Name" not in df.columns:
        st.error("CSV must have a column named 'Retailer Name'")
    else:
        st.success(f"Loaded {len(df)} retailers from CSV")

        if st.button("Run Search"):
            results = []
            for retailer in df["Retailer Name"].dropna().unique():
                merchant = get_merchant_name(retailer)
                status = "YES" if merchant else "NO"
                results.append({
                    "Retailer Name": retailer,
                    "Merchant Name": merchant if merchant else "None",
                    "Status": status
                })
            
            results_df = pd.DataFrame(results)
            st.dataframe(results_df)

            # Download button
            csv = results_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name="retailer_results.csv",
                mime="text/csv"
            )
