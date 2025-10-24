import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from difflib import SequenceMatcher

# Hardcoded credentials (use st.secrets in production)
API_KEY = "AIzaSyBYS2Qsc6rES4sKtr3wcz-74V5leOgJaV4"
CX = "e2eddc6d351e647af"

st.title("Enhanced Company Website Finder")

# Function for fuzzy match
def is_match(retailer, text, threshold=0.6):
    return SequenceMatcher(None, retailer.lower(), text.lower()).ratio() >= threshold

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
            query = f"{retailer_name} official website"
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}&num=5"
            response = requests.get(url).json()

            official_site = "No result found"
            status = "NOT OK"

            if "items" in response:
                for item in response["items"]:
                    title = item.get("title", "")
                    snippet = item.get("snippet", "")
                    link = item.get("link", "")

                    # Check for strong match in title, snippet, or domain
                    if (is_match(retailer_name, title) or is_match(retailer_name, snippet) or is_match(retailer_name, link)):
                        official_site = link
                        status = "OK"
                        break  # Stop at first strong match

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
