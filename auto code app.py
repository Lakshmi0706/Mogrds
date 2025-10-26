import streamlit as st
import pandas as pd
import re
from duckduckgo_search import DDGS
import tldextract
from io import BytesIO
from difflib import SequenceMatcher

# Upload merchant list
merchant_file = st.file_uploader("Upload Merchant List Excel", type=["xlsx"])
merchant_list = []

if merchant_file:
    merchant_df = pd.read_excel(merchant_file, sheet_name="fetch", engine="openpyxl")
    # Drop NaN and convert to string before upper()
    merchant_list = merchant_df.iloc[:, 0].dropna().astype(str).unique().tolist()
    merchant_list = [m.upper().strip() for m in merchant_list]

# Function to clean OCR text using merchant list
def clean_ocr_text(text):
    text = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    text = re.sub(r'\s+', ' ', text).strip().upper()
    words = text.split()
    corrected_words = []
    for word in words:
        best_match = word
        highest_ratio = 0.0
        for merchant in merchant_list:
            ratio = SequenceMatcher(None, word, merchant).ratio()
            if ratio > highest_ratio and abs(len(word) - len(merchant)) <= 3:
                highest_ratio = ratio
                best_match = merchant
        corrected_words.append(best_match)
    return ' '.join(corrected_words)

# Perform DuckDuckGo search
def find_retailer(desc):
    query = f"{desc} retailer OR store OR brand"
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
st.title("Retailer Identification with OCR Correction and Merchant List")

uploaded_file = st.file_uploader("Upload Excel File with 'Description' column", type=["xlsx"])

if uploaded_file and merchant_list:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    if 'Description' not in df.columns:
        st.error("The uploaded file must contain a 'Description' column.")
    else:
        retailer_names = []
        statuses = []

        progress_bar = st.progress(0)
        status_text = st.empty()
        total = len(df)

        for i, desc in enumerate(df['Description']):
            cleaned_desc = clean_ocr_text(str(desc))
            retailer, status = find_retailer(cleaned_desc)
            retailer_names.append(retailer)
            statuses.append(status)
            percent_complete = int(((i + 1) / total) * 100)
            progress_bar.progress((i + 1) / total)
            status_text.text(f"Processing {i + 1}/{total} ({percent_complete}%)")

        df['Retailer Name'] = retailer_names
        df['Status'] = statuses

        st.subheader("Preview of Processed Data")
        st.dataframe(df)

        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        st.success("Processing complete. Download the output file below.")
        st.download_button("Download Output Excel", output, file_name="retailer_output.xlsx")
