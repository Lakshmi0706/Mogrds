import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from urllib.parse import urlparse
import re

# API credentials
API_KEY = "AIzaSyBYS2Qsc6rES4sKtr3wcz-74V5leOgJaV4"
CX = "e2eddc6d351e647af"

EXCLUDE_DOMAINS = ["facebook.com", "wikipedia.org", "linkedin.com", "instagram.com", "gov", "blogspot"]

# Utility functions
def clean_name(name):
    if pd.isna(name):
        return ""
    return re.sub(r'[^a-zA-Z]', '', str(name)).lower()

def is_valid_domain(link):
    domain = urlparse(link).netloc.lower()
    return not any(ex in domain for ex in EXCLUDE_DOMAINS)

def domain_matches(link, corrected_name):
    domain = urlparse(link).netloc.lower()
    return corrected_name in domain

def title_matches(title, corrected_name):
    return corrected_name in title.lower()

st.title("Retailer Website Finder with Merchant Matching")

# Upload merchant list
merchant_file = st.file_uploader("Upload Merchant List (Excel)", type=["xlsx"])
merchant_names_cleaned = []

if merchant_file:
    merchant_df = pd.read_excel(merchant_file, sheet_name=None, engine="openpyxl")
    merchant_names = set()
    for sheet in merchant_df.values():
        merchant_names.update(sheet.iloc[:, 0].dropna().astype(str).tolist())
    merchant_names_cleaned = [clean_name(name) for name in merchant_names]
    st.success(f"Merchant list loaded with {len(merchant_names_cleaned)} entries.")

def find_best_match(name):
    name_clean = clean_name(name)
    best_score = 0
    best_match = name_clean
    for merchant in merchant_names_cleaned:
        score = sum(ch1 == ch2 for ch1, ch2 in zip(name_clean, merchant)) / max(len(name_clean), len(merchant))
        if score > best_score:
            best_score = score
            best_match = merchant
    return best_match

# Upload company list
uploaded_file = st.file_uploader("Upload Company List (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file and merchant_names_cleaned:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

    st.write("Uploaded Data:", df.head())

    if 'Company' not in df.columns:
        st.error("File must have a column named 'Company'")
    else:
        output_df = pd.DataFrame(columns=["S No", "Original Name", "Corrected Name", "Official Website", "Status"])
        progress = st.progress(0)
        status_text = st.empty()

        total = len(df)

        for i, row in df.iterrows():
            original_name = row['Company']
            corrected_name = find_best_match(original_name)
            query = f"{corrected_name} official site"
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}&num=10"
            response = requests.get(url).json()

            official_site = "No result found"
            status = "NOT OK"

            if "items" in response:
                for item in response["items"]:
                    title = item.get("title", "")
                    link = item.get("link", "")

                    if is_valid_domain(link) and (domain_matches(link, corrected_name) or title_matches(title, corrected_name)):
                        official_site = link
                        status = "OK"
                        break

            output_df.loc[i] = [i + 1, original_name, corrected_name, official_site, status]

            # Update progress
            percent = int(((i + 1) / total) * 100)
            progress.progress((i + 1) / total)
            status_text.text(f"Processing: {i + 1} of {total} ({percent}%)")

        st.success("Search completed!")
        st.write(output_df)

        # Download full results
        output = BytesIO()
        output_df.to_excel(output, index=False)
        output.seek(0)
        st.download_button(
            label="Download All Results as Excel",
            data=output,
            file_name="company_websites.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Download only OK results
        ok_df = output_df[output_df['Status'] == 'OK']
        ok_output = BytesIO()
        ok_df.to_excel(ok_output, index=False)
        ok_output.seek(0)
        st.download_button(
            label="Download Only OK Results",
            data=ok_output,
            file_name="company_websites_OK.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Embedded Google Search Box
st.header("Manual Google Search")
html_code = """
https://cse.google.com/cse.js?cx=e2eddc6d351e647af</script>
<div class="gcse-search"></div>
"""
st.components.v1.html(html_code, height=600)
