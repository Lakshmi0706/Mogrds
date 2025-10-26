import streamlit as st
import pandas as pd
import re
from duckduckgo_search import DDGS
import tldextract
from io import BytesIO

# Normalize description
def normalize_description(desc):
    desc = re.sub(r'[^a-zA-Z0-9 ]', '', desc)
    return desc.strip()

# Perform DuckDuckGo search
def find_retailer(desc):
    query = f"{normalize_description(desc)} retailer"
    exclude_domains = ['facebook.com', 'instagram.com', 'justdial.com', 'wikipedia.org', 'google.com/maps']
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=10)
            for r in results:
                url = r.get("href", "")
                if any(domain in url for domain in exclude_domains):
                    continue
                ext = tldextract.extract(url)
                if ext.domain:
                    return ext.domain.title(), "OK"
        return "Not Found", "Not OK"
    except Exception:
        return "Not Found", "Not OK"

# Streamlit UI
st.title("Retailer Identification from Description (DuckDuckGo)")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    if 'Description' not in df.columns:
        st.error("The uploaded file must contain a 'Description' column.")
    else:
        retailer_names = []
        statuses = []

        progress_bar = st.progress(0)
        total = len(df)

        for i, desc in enumerate(df['Description']):
            retailer, status = find_retailer(str(desc))
            retailer_names.append(retailer)
            statuses.append(status)
            progress_bar.progress((i + 1) / total)

        df['Retailer Name'] = retailer_names
        df['Status'] = statuses

        # Prepare file for download
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.success("Processing complete. Download the output file below.")
        st.download_button("Download Output Excel", output, file_name="retailer_output.xlsx")
