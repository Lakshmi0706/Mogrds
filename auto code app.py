import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from difflib import SequenceMatcher
from urllib.parse import urlparse

# Hardcoded credentials (use st.secrets for production)
API_KEY = "AIzaSyBYS2Qsc6rES4sKtr3wcz-74V5leOgJaV4"
CX = "e2eddc6d351e647af"

# Domains to exclude
EXCLUDE_DOMAINS = ["facebook.com", "wikipedia.org", "linkedin.com", "instagram.com", "gov", "blogspot"]

st.title("Smart Retailer Website Finder")

# Fuzzy match function
def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def is_official_domain(link, retailer):
    domain = urlparse(link).netloc
    if any(ex in domain for ex in EXCLUDE_DOMAINS):
        return False
    if domain.endswith(".com") and similarity(retailer, domain) > 0.5:
        return True
    return False

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file with company names", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Uploaded Data:", df.head())

    if 'Company' not in df.columns:
        st.error("CSV must have a column named 'Company'")
    else:
        output_df = pd.DataFrame(columns=["S No", "Retailer Name", "Official Website", "Status"])

        for i, row in df.iterrows():
            retailer_name = row['Company']
            query = f"{retailer_name} official site"
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}&num=10"
            response = requests.get(url).json()

            official_site = "No result found"
            status = "NOT OK"
            best_score = 0

            if "items" in response:
                for item in response["items"]:
                    title = item.get("title", "")
                    link = item.get("link", "")
                    domain = urlparse(link).netloc

                    # Skip excluded domains
                    if any(ex in domain for ex in EXCLUDE_DOMAINS):
                        continue

                    # Calculate score based on title + domain match
                    score = max(similarity(retailer_name, title), similarity(retailer_name, domain))
                    if score > best_score and domain.endswith(".com"):
                        best_score = score
                        official_site = link
                        status = "OK"

            output_df.loc[i] = [i + 1, retailer_name, official_site, status]

        st.success("Search completed!")
        st.write(output_df)

        # Download Excel
        output = BytesIO()
        output_df.to_excel(output, index=False)
        output.seek(0)
        st.download_button(
            label="Download Results as Excel",
            data=output,
            file_name="company_websites.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Embedded Google Search Box
st.header("Manual Google Search")
html_code = """
https://cse.google.com/cse.js?cx=e2eddc6d351e647af</script>
<div class="gcse-search"></div>
"""
st.components.v1.html(html_code, height=600)
