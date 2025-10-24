import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from difflib import SequenceMatcher
from urllib.parse import urlparse
import re

# Load merchant list from uploaded Excel
merchant_df = pd.read_excel("merchant list.xlsx", sheet_name=None, engine="openpyxl")
merchant_names = set()
for sheet in merchant_df.values():
    merchant_names.update(sheet.iloc[:, 0].dropna().astype(str).tolist())

# Normalize merchant names
merchant_names_cleaned = [re.sub(r'[^a-zA-Z]', '', name).lower() for name in merchant_names]

# API credentials
API_KEY = "AIzaSyBYS2Qsc6rES4sKtr3wcz-74V5leOgJaV4"
CX = "e2eddc6d351e647af"

# Domains to exclude
EXCLUDE_DOMAINS = ["facebook.com", "wikipedia.org", "linkedin.com", "instagram.com", "gov", "blogspot"]

# Utility functions
def clean_name(name):
    return re.sub(r'[^a-zA-Z]', '', name).lower()

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_match(name):
    name_clean = clean_name(name)
    best_score = 0
    best_match = name
    for merchant in merchant_names_cleaned:
        score = similarity(name_clean, merchant)
        if score > best_score:
            best_score = score
            best_match = merchant
    return best_match, best_score

def calculate_score(retailer, title, snippet, link):
    domain = urlparse(link).netloc.lower()
    retailer_clean = clean_name(retailer)
    score = 0
    if retailer_clean in domain:
        score += 0.7
    score += similarity(retailer, title) * 0.2
    score += similarity(retailer, snippet) * 0.1
    return score

def is_valid_domain(link):
    domain = urlparse(link).netloc.lower()
    return not any(ex in domain for ex in EXCLUDE_DOMAINS)

# Streamlit app
st.title("Retailer Website Finder with Merchant Matching")

uploaded_file = st.file_uploader("Upload a CSV or Excel file with company names", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

    st.write("Uploaded Data:", df.head())

    if 'Company' not in df.columns:
        st.error("File must have a column named 'Company'")
    else:
        output_df = pd.DataFrame(columns=["S No", "Original Name", "Corrected Name", "Official Website", "Status", "Confidence Score"])
        progress = st.progress(0)

        for i, row in df.iterrows():
            original_name = row['Company']
            corrected_name, match_score = find_best_match(original_name)
            query = f"{corrected_name} official site"
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}&num=10"
            response = requests.get(url).json()

            best_site = "No result found"
            best_score = 0
            status = "NOT OK"

            if "items" in response:
                for item in response["items"]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")

                    if is_valid_domain(link):
                        score = calculate_score(corrected_name, title, snippet, link)
                        if score > best_score:
                            best_score = score
                            best_site = link

            if best_score >= 0.6:
                status = "OK"

            output_df.loc[i] = [i + 1, original_name, corrected_name, best_site, status, round(best_score, 2)]
            progress.progress((i + 1) / len(df))

        st.success("Search completed!")
        st.write(output_df)

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
