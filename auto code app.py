import streamlit as st
from bs4 import BeautifulSoup
import requests
from duckduckgo_search import DDGS
from urllib.parse import urljoin

def find_retailer(description):
    query = description + " official site USA"
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=10))

    for result in results:
        url = result.get("href")
        if not url:
            continue

        # Filter domains (skip Wikipedia, Yelp, etc.)
        blacklist = ["wikipedia.org", "yelp.", "linkedin.", "facebook.", "amazon."]
        if any(b in url for b in blacklist):
            continue

        try:
            page = requests.get(url, timeout=5)
            soup = BeautifulSoup(page.content, "html.parser")

            logos = soup.find_all("img")
            for logo in logos:
                alt_text = logo.get("alt", "").lower()
                classes = " ".join(logo.get("class", [])).lower()

                if "logo" in alt_text or "logo" in classes:
                    logo_url = urljoin(url, logo.get("src"))
                    return logo_url, url
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
