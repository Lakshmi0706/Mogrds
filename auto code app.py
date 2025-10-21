import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from collections import Counter

# Function to perform Google search using SerpAPI
def search_google(description, api_key):
    query = f"{description}"  # just the description
    params = {
        "q": query,
        "engine": "google",
        "gl": "us",      # restrict to USA
        "hl": "en",      # language English
        "api_key": api_key
    }
    response = requests.get("https://serpapi.com/search", params=params)
    data = response.json()
    links = [result['link'] for result in data.get("organic_results", [])]
    return links

# Function to extract unique retailer domains
def get_unique_domain(links):
    domains = [urlparse(link).netloc for link in links]
    # Filter out unwanted domains like amazon or wikipedia
    retailer_domains = [d for d in domains if "amazon" not in d and "wikipedia" not in d and d]
    return retailer_domains

# Function to get the top retailer (most frequently appearing domain)
def get_top_retailer(domains):
    if not domains:
        return "", "No"
    domain_counts = Counter(domains)
    top_domain, count = domain_counts.most_common(1)[0]
    # If only one unique domain, mark as Yes, else No
    if len(domain_counts) == 1:
        return top_domain, "Yes"
    else:
        return top_domain, "No"

# Streamlit UI
st.title("Retailer Uniqueness Checker")

api_key = st.text_input("Enter your SerpAPI Key")

uploaded_file = st.file_uploader("Upload your description file (CSV with 'description' column)", type=["csv"])

if uploaded_file and api_key:
    df = pd.read_csv(uploaded_file)
    if 'description' not in df.columns:
        st.error("CSV must contain a 'description' column.")
    else:
        retailers = []
        statuses = []
        for desc in df['description']:
            links = search_google(desc, api_key)
            domains = get_unique_domain(links)
            top_retailer, status = get_top_retailer(domains)
            retailers.append(top_retailer)
            statuses.append(status)
        
        df_result = df.copy()
        df_result["retailer"] = retailers
        df_result["status"] = statuses

        st.dataframe(df_result)

        csv = df_result.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results", csv, "retailer_results.csv", "text/csv")
else:
    st.info("Please upload a file and enter your SerpAPI key to proceed.")
