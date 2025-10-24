import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Load secrets
API_KEY = st.secrets["API_KEY"]
CX = st.secrets["CX"]

st.title("Company Website Finder + Google Search")

# --- Upload CSV ---
uploaded_file = st.file_uploader("Upload a CSV file with company names and descriptions", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("Uploaded Data:", df.head())

    # Check if 'Company' column exists
    if 'Company' not in df.columns:
        st.error("CSV must have a column named 'Company'")
    else:
        # Add a new column for official websites
        df['Official Website'] = ""

        # Fetch websites using Google Custom Search API
        for i, row in df.iterrows():
            company = row['Company']
            query = f"{company} official website"
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}"
            response = requests.get(url).json()
            if "items" in response:
                df.at[i, 'Official Website'] = response["items"][0]["link"]
            else:
                df.at[i, 'Official Website'] = "No result found"

        st.success("Search completed!")

        # Display results
        st.write(df)

        # --- Download Excel ---
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        st.download_button(
            label="Download Results as Excel",
            data=output,
            file_name="company_websites.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- Embedded Google Search Box ---
st.header("Manual Google Search")
html_code = """
https://cse.google.com/cse.js?cx=e2eddc6d351e647af</script>
<div class="gcse-search"></div>
"""
st.components.v1.html(html_code, height=600)
