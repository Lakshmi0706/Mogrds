import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from collections import Counter
import time
import random

def search_google(description, api_key):
    """Search for product retailers using a more direct, human-like query."""
    # CHANGE: I've made the query more specific to ask for the official retailer.
    # This helps avoid directory and map websites, leading to more accurate results.
    query = f'"{description}" official retailer website USA'
    
    params = {
        "q": query,
        "engine": "google",
        "gl": "us",
        "hl": "en",
        "api_key": api_key,
        "num": 10  # We'll look at the top 10 results
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=20)
        response.raise_for_status()  # This will raise an error for bad responses like 404 or 500
        data = response.json()
        
        if "error" in data:
            st.warning(f"API Error for '{description}': {data['error']}")
            return []
        
        links = [result['link'] for result in data.get("organic_results", []) if 'link' in result]
        return links
    
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't connect to the search API: {e}")
        return []

def get_retailer_domains(links):
    """Extract retailer domains from search results, skipping common non-retail sites."""
    domains = []
    
    # This list is helpful to filter out noise. You can customize it if needed!
    skip_these = [
        "amazon", "ebay", "walmart", "wikipedia", "youtube", 
        "facebook", "pinterest", "twitter", "instagram", 
        "reddit", "quora", "yelp", "google", "linkedin", "forbes"
    ]
    
    for link in links:
        try:
            domain = urlparse(link).netloc.replace("www.", "")
            if domain and not any(skip in domain.lower() for skip in skip_these):
                domains.append(domain)
        except Exception:
            # Ignore malformed URLs
            continue
    
    return domains

def find_top_retailer(domains):
    """Determine the most common retailer and check if it's a clear winner."""
    if not domains:
        return "Not found", "No"
    
    domain_counts = Counter(domains)
    most_common_list = domain_counts.most_common(2)
    
    # The top retailer is the first one in the list
    top_retailer, top_count = most_common_list[0]
    
    # CHANGE: Here's the new, more flexible logic.
    # We'll say the status is "Yes" if the top retailer appears more than once
    # and is more common than the second-place result. This is a much
    # more realistic way to determine the primary retailer.
    is_dominant = "No"
    if top_count > 1:
        if len(most_common_list) == 1:
            # If only one domain was found (and it appeared > 1 times), it's dominant.
            is_dominant = "Yes"
        else:
            # If there's a second-place domain, check if the top one is clearly ahead.
            second_count = most_common_list[1][1]
            if top_count > second_count:
                is_dominant = "Yes"
            
    return top_retailer, is_dominant

# --- Streamlit App UI ---

st.set_page_config(page_title="Retailer Domain Validator", page_icon="🛒", layout="centered")

st.title("🛒 Retailer Domain Validator")
st.caption("Upload a CSV with product descriptions to find their primary online retailer.")

# Get API key from Streamlit secrets or allow manual input
api_key = st.secrets.get("SERPAPI_KEY") if hasattr(st, 'secrets') else None

if not api_key:
    api_key = st.text_input("Enter your SerpAPI API Key", type="password", help="Your key is kept secure.")

# File uploader
st.header("1. Upload Your File")
uploaded_file = st.file_uploader(
    "Your CSV file must have a column named 'description'.", 
    type=["csv"]
)

if uploaded_file and api_key:
    try:
        df = pd.read_csv(uploaded_file)
        
        if 'description' not in df.columns:
            st.error("Upload failed! Your CSV must contain a 'description' column.", icon="🚨")
            st.stop()
        
        st.success(f"File uploaded successfully! Found {len(df)} products to analyze.")
        st.dataframe(df.head(), use_container_width=True)
        
        st.header("2. Start Analysis")
        start_btn = st.button("Find Retailers", type="primary", use_container_width=True)
        
        if start_btn:
            with st.spinner("Analyzing... This may take a few moments."):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total = len(df)
                for idx, row in df.iterrows():
                    description = row['description']
                    status_text.text(f"Processing {idx + 1}/{total}: {description[:50]}...")
                    
                    search_links = search_google(description, api_key)
                    retailer_domains = get_retailer_domains(search_links)
                    top_retailer, status = find_top_retailer(retailer_domains)
                    
                    results.append({'retailer': top_retailer, 'status': status})
                    
                    progress_bar.progress((idx + 1) / total)
                    
                    # A small, random delay makes the process more stable
                    if idx < total - 1:
                        time.sleep(random.uniform(1.0, 1.5))
                
                status_text.success("Analysis Complete!", icon="✅")
            
            # Combine results with original data
            results_df = pd.DataFrame(results)
            df['retailer'] = results_df['retailer']
            df['status'] = results_df['status']
            
            # Show results
            st.header("3. Results")
            st.dataframe(df, use_container_width=True)
            
            # Show summary stats
            dominant_count = (df['status'] == 'Yes').sum()
            st.metric("Dominant Retailers Found", f"{dominant_count} / {total}")
            
            # Download button
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Results as CSV",
                csv_data,
                "retailer_analysis_results.csv",
                "text/csv",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

elif not uploaded_file:
    st.info("Please upload a CSV file to get started.")
elif not api_key:
    st.warning("Please enter your SerpAPI key to enable the analysis.")
