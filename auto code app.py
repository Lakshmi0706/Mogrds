import streamlit as st
from googlesearch import search
from bs4 import BeautifulSoup
import requests

def find_retailer(description):
    query = description + " USA"
    results = search(query, num_results=10)
    for result in results:
        if "logo" in result:
            page = requests.get(result)
            soup = BeautifulSoup(page.content, 'html.parser')
            logos = soup.find_all('img')
            for logo in logos:
                if description.lower() in logo.get('alt', '').lower():
                    return logo.get('src'), result
    return None, None

description = st.text_input("Enter description")
if st.button("Search"):
    logo_url, retailer_url = find_retailer(description)
    if logo_url:
        st.image(logo_url)
        st.write("Retailer Name:", retailer_url)
        st.write("Status:", "Yes")
    else:
        st.write("Status:", "No")
