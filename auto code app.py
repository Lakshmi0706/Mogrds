import streamlit as st
import pandas as pd
import urllib.parse
from io import BytesIO

EXCLUDED_SITES = ['wikipedia.org', 'facebook.com', 'instagram.com', 'google.com/maps', 'justdial.com']

st.title("Retailer Site Finder via Google Search")

uploaded_file = st.file_uploader("Upload Excel file with 'S No' and 'Description' columns", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    df['Status'] = ''
    df['Retailer Name'] = ''

    st.write("### Instructions")
    st.write("Click the search links below to manually verify each description. After verification, update the status and retailer name.")

    for index, row in df.iterrows():
        description = row['Description']
        query = urllib.parse.quote(description)
        search_url = f"https://www.google.com/search?q={query}"
        st.markdown(f"**{row['S No']} - {description}**")
        st.markdown(f"{search_url}")
        status = st.selectbox(f"Status for '{description}'", ["", "OK"], key=f"status_{index}")
        retailer = st.text_input(f"Retailer Name for '{description}'", key=f"retailer_{index}")
        df.at[index, 'Status'] = status
        df.at[index, 'Retailer Name'] = retailer
        st.markdown("---")

    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    st.download_button(
        label="Download Results",
        data=output.getvalue(),
        file_name="retailer_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
