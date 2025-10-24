import streamlit as st
import requests

# Use secrets for security in production
API_KEY = "AIzaSyBYS2Qsc6rES4sKtr3wcz-74V5leOgJaV4"  # Replace with st.secrets["API_KEY"] in Streamlit Cloud
CX = "e2eddc6d351e647af"  # Replace with st.secrets["CX"]

st.title("Company Website Finder + Google Search")

# --- Section 1: Automated Official Website Fetch ---
st.header("Official Websites for Companies")

companies = ["Tata Motors", "Infosys", "Reliance Industries", "HDFC Bank"]

def get_official_website(company):
    query = f"{company} official website"
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}"
    response = requests.get(url).json()
    if "items" in response:
        return response["items"][0]["link"]
    return "No result found"

for company in companies:
    website = get_official_website(company)
    st.write(f"**{company}**: {website}")

# --- Section 2: Embedded Google Search Box ---
st.header("Search Anything with Google CSE")
html_code = """
<script async srce.com/cse.js?cx=e2eddc6d351e647af</script>
<div class="gcse-search"></div>
"""
st.components.v1.html(html_code, height=600)
