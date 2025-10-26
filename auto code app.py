import streamlit as st
import pandas as pd
import re

# Function to normalize description
def normalize_description(desc):
    desc = desc.lower()
    desc = re.sub(r'[^a-z0-9]', '', desc)  # Remove non-alphanumeric characters
    corrections = {
        'dollrgeneral': 'dollargeneral',
        'dullarree': 'dollartree',
        'dollarree': 'dollartree',
        'dollar genral': 'dollargeneral'
        # Add more common misspellings here
    }
    return corrections.get(desc, desc)

# Simulated manual Google search
def simulate_google_search(normalized_desc):
    retailer_websites = {
        'dollargeneral': 'https://www.dollargeneral.com',
        'dollartree': 'https://www.dollartree.com',
        'walmart': 'https://www.walmart.com',
        'target': 'https://www.target.com'
        # Add more known retailers here
    }
    for key in retailer_websites:
        if key in normalized_desc:
            return key.title(), 'OK'
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
            normalized = normalize_description(str(desc))
            retailer, status = simulate_google_search(normalized)
            retailer_names.append(retailer)
            statuses.append(status)

        df['Retailer Name'] = retailer_names
        df['Status'] = statuses

        output_file = "retailer_output.xlsx"
        df.to_excel(output_file, index=False)

        st.success("Processing complete. Download the output file below.")
        with open(output_file, "rb") as f:
            st.download_button("Download Output Excel", f, file_name=output_file)
