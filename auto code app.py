import streamlit as st
from bs4 import BeautifulSoup
import requests
from duckduckgo_search import DDGS

def find_retailer(description):
    query = description + " USA"
    # Use DuckDuckGo search instead of googlesearch
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=10))

    for result in results:
        url = result.get("href")
        if not url:
            continue

        try:
            page = requests.get(url, timeout=5)
            soup = BeautifulSoup(page.content, "html.parser")

            logos = soup.find_all("img")
            for logo in logos:
                alt_text = logo.get("alt", "").lower()
                if description.lower() in alt_text:
                    return logo.get("src"), url
        except Exception:
            continue

    return None, None


# Streamlit UI
st.title("Retailer Finder")

description = st.text_input("Enter retailer description")

if st.button("Search"):
    logo_url, retailer_url = find_retailer(description)

    if logo_url:
        st.image(logo_url, caption="Retailer Logo")
        st.write("Retailer URL:", retailer_url)
        st.write("Status:", "Yes ✅")
    else:
        st.write("Status:", "No ❌")
