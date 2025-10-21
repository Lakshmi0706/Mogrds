import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from collections import Counter
import time
import random

def search_google(description, api_key):
    """Search for product retailers using natural language query"""
    # Make it sound like a human search
    query = f"where to buy {description} in USA"
    
    params = {
        "q": query,
        "engine": "google",
        "gl": "us",
        "hl": "en",
        "api_key": api_key,
        "num": 10
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            st.warning(f"Oops! API returned an error: {data['error']}")
            return []
        
        links = [result['link'] for result in data.get("organic_results", [])]
        return links
    
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't connect to search API: {e}")
        return []

def get_retailer_domains(links):
    """Extract retailer domains from search results"""
    domains = []
    
    # Common sites we want to skip (not actual retailers)
    skip_these = [
        "amazon", "ebay", "walmart", "wikipedia", "youtube", 
        "facebook", "pinterest", "twitter", "instagram", 
        "reddit", "quora", "yelp", "google"
    ]
    
    for link in links:
        domain = urlparse(link).netloc.replace("www.", "")
        
        if domain and not any(skip in domain.lower() for skip in skip_these):
            domains.append(domain)
    
    return domains

def find_top_retailer(domains):
    """Determine the most common retailer and if it's unique"""
    if not domains:
        return "Not found", "No"
    
    domain_counts = Counter(domains)
    most_common_retailer = domain_counts.most_common(1)[0][0]
    
    # It's unique if this retailer dominates the results
    is_unique = "Yes" if len(domain_counts) == 1 else "No"
    
    return most_common_retailer, is_unique

# Page setup
st.set_page_config(page_title="Retailer Domain Validator", page_icon="🛒", layout="centered")

st.title("Retailer Domain Validator")

# Get API key from Streamlit secrets or allow manual input as fallback
api_key = None
try:
    api_key = st.secrets.get("SERPAPI_KEY", None)
except:
    pass

# If no secret found, show input field
if not api_key:
    api_key = st.text_input("Enter your SerpAPI API Key", type="password")

# File uploader
st.write("Upload CSV file with 'description' column")
uploaded_file = st.file_uploader(
    "Drag and drop file here", 
    type=["csv"],
    help="Limit 200MB per file • CSV"
)

if uploaded_file and api_key:
    try:
        df = pd.read_csv(uploaded_file)
        
        if 'description' not in df.columns:
            st.error("CSV must contain a 'description' column!")
            st.stop()
        
        # Show preview
        st.success(f"Found {len(df)} products to analyze")
        
        # Start button
        start_btn = st.button("Start Analysis", type="primary", use_container_width=True)
        
        if start_btn:
            retailers = []
            statuses = []
            
            progress = st.progress(0)
            status_msg = st.empty()
            
            for idx, description in enumerate(df['description'], 1):
                # Show what we're working on
                status_msg.text(f"Processing {idx}/{len(df)}: {description[:50]}...")
                
                # Do the search
                search_results = search_google(description, api_key)
                retailer_domains = get_retailer_domains(search_results)
                top_retailer, unique_status = find_top_retailer(retailer_domains)
                
                retailers.append(top_retailer)
                statuses.append(unique_status)
                
                # Update progress
                progress.progress(idx / len(df))
                
                # Human-like delay (random between 1-2 seconds)
                if idx < len(df):
                    time.sleep(random.uniform(1.0, 2.0))
            
            status_msg.success("Processing complete!")
            
            # Build results
            df['retailer'] = retailers
            df['status'] = statuses
            
            # Show results
            st.subheader("Results")
            st.dataframe(df, use_container_width=True)
            
            # Stats
            unique_products = sum(1 for s in statuses if s == "Yes")
            st.metric("Unique Retailers Found", f"{unique_products}/{len(df)}")
            
            # Download
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Results",
                csv_data,
                "retailer_results.csv",
                "text/csv",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"Error: {e}")

else:
    if not uploaded_file:
        st.info("Please upload a CSV file to proceed")
    elif not api_key:
        st.warning("Please enter your SerpAPI key above to start analysis")
