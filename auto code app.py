import streamlit as st
import pandas as pd
import re
from googlesearch import search
import tldextract
from io import BytesIO

# Step 1: Clean OCR text dynamically
def clean_ocr_text(text):
    # Remove special characters and normalize spaces
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Step 2: Perform Google search
def find_retailer(desc):
    cleaned = clean_ocr_text(desc)
    query = f"{cleaned} retailer OR store OR brand"
    exclude_domains = ['facebook.com', 'instagram.com', 'justdial.com', 'wikipedia.org', 'google.com/maps']
    try:
        results = search(query, num_results=10)
        for url in results:
            if any(domain in url for domain in exclude_domains):
                continue
            ext = tldextract.extract(url)
            if ext.domain:
                return ext.domain.title(), "OK"
        return "Not Found", "Not OK"
    except Exception:
        return "Not Found", "Not OK"

# Step 3: Streamlit UI
st.title("Retailer Identification from Description (Google Search)")

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
