import streamlit as st
import pandas as pd
import re
from googlesearch import search  # pip install googlesearch-python

# Normalize description
def normalize_description(desc):
    desc = desc.lower()
    desc = re.sub(r'[^a-z0-9 ]', '', desc)  # Keep alphanumeric and spaces
    return desc.strip()

# Perform Google search
def find_retailer(desc):
    query = normalize_description(desc)
    exclude_domains = ['facebook.com', 'instagram.com', 'justdial.com', 'wikipedia.org', 'google.com/maps']
    try:
        results = search(query, num_results=10)
        for url in results:
            if any(domain in url for domain in exclude_domains):
                continue
            # If official retailer site found
            if '.com' in url or '.org' in url:
                retailer_name = url.split('//')[-1].split('.')[0].title()
                return retailer_name, 'OK'
        return 'Not Found', 'Not OK'
    except Exception:
        return 'Not Found', 'Not OK'

# Streamlit UI
st.title("Retailer Identification from Description")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    if 'Description' not in df.columns:
        st.error("The uploaded file must contain a 'Description' column.")
    else:
        retailer_names = []
        statuses = []

        for desc in df['Description']:
            retailer, status = find_retailer(str(desc))
            retailer_names.append(retailer)
            statuses.append(status)

        df['Retailer Name'] = retailer_names
        df['Status'] = statuses

        output_file = "retailer_output.xlsx"
        df.to_excel(output_file, index=False)

        st.success("Processing complete. Download the output file below.")
        with open(output_file, "rb") as f:
            st.download_button("Download Output Excel", f, file_name=output_file)
