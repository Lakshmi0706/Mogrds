import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from collections import Counter
import time
import random

def search_google_web(description, api_key):
    """Search Google Web for the official retailer website."""
    query = f'"{description}" official retailer website USA'
    params = {
        "q": query,
        "engine": "google",
        "gl": "us",
        "hl": "en",
        "api_key": api_key,
        "num": 10
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            st.warning(f"Web search error for '{description}': {data['error']}")
            return []
        return [result['link'] for result in data.get("organic_results", []) if 'link' in result]
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't connect to web search API: {e}")
        return []

# NEW FUNCTION: This specifically searches Google Images for logos.
def search_google_images(description, api_key):
    """Search Google Images for logos related to the description."""
    query = f'"{description}" logo'
    params = {
        "q": query,
        "engine": "google_images",
        "gl": "us",
        "hl": "en",
        "api_key": api_key
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            st.warning(f"Image search error for '{description}': {data['error']}")
            return []
        # We extract the 'source' which is the domain the image is from.
        return [result['source'] for result in data.get("images_results", []) if 'source' in result]
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't connect to image search API: {e}")
        return []

def get_clean_domains(links_or_sources):
    """Extract and clean domains from a list of URLs or source names."""
    domains = []
    # This list helps filter out generic sites, improving accuracy for both searches.
    skip_these = [
        "amazon", "ebay", "walmart", "wikipedia", "youtube", "facebook", 
        "pinterest", "twitter", "instagram", "reddit", "quora", "yelp", 
        "google", "linkedin", "forbes", "bloomberg", "reuters", "istockphoto",
        "freepik", "vecteezy", "cnn", "wsj"
    ]
    for link in links_or_sources:
        try:
            # For image sources that are just "domain.com", urlparse works well.
            domain = urlparse(f"http://{link}").netloc.replace("www.", "")
            if domain and not any(skip in domain.lower() for skip in skip_these):
                domains.append(domain)
        except Exception:
            continue
    return domains

# MODIFIED FUNCTION: Renamed for clarity, as it now analyzes both web and image results.
def analyze_domain_uniqueness(domains):
    """Determines the top domain and if it's a unique, clear winner."""
    if not domains:
        return "Not found", "No"
    
    domain_counts = Counter(domains)
    most_common_list = domain_counts.most_common(2)
    top_domain, top_count = most_common_list[0]
    
    is_dominant = "No"
    if top_count > 1: # The logo/site must appear more than once.
        if len(most_common_list) == 1:
            is_dominant = "Yes"
        else:
            second_count = most_common_list[1][1]
            if top_count > second_count: # It must be more common than the runner-up.
                is_dominant = "Yes"
            
    return top_domain, is_dominant

# --- Streamlit App UI (Largely the same) ---

st.set_page_config(page_title="Retailer & Logo Validator", page_icon="🛒", layout="centered")

st.title("🛒 Retailer & Logo Validator")
st.caption("Find a retailer's website and check for a unique brand logo via Google Images.")

api_key = st.secrets.get("SERPAPI_KEY") if hasattr(st, 'secrets') else None
if not api_key:
    api_key = st.text_input("Enter your SerpAPI API Key", type="password")

st.header("1. Upload Your File")
uploaded_file = st.file_uploader("Your CSV file must have a column named 'description'.", type=["csv"])

if uploaded_file and api_key:
    try:
        df = pd.read_csv(uploaded_file)
        if 'description' not in df.columns:
            st.error("Upload failed! Your CSV must contain a 'description' column.", icon="🚨")
            st.stop()
        
        st.success(f"File uploaded! Found {len(df)} products to analyze.")
        
        st.header("2. Start Analysis")
        start_btn = st.button("Find Retailers & Validate Logos", type="primary", use_container_width=True)
        
        if start_btn:
            with st.spinner("Analyzing... This involves two searches per item, so it may take a moment."):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total = len(df)
                for idx, row in df.iterrows():
                    description = row['description']
                    status_text.text(f"Processing {idx + 1}/{total}: {description[:50]}...")
                    
                    # --- UPDATED LOGIC IN MAIN LOOP ---
                    # 1. Perform web search to find the retailer domain
                    web_links = search_google_web(description, api_key)
                    web_domains = get_clean_domains(web_links)
                    top_retailer, _ = analyze_domain_uniqueness(web_domains) # We only need the domain name
                    
                    # 2. Perform image search to determine the logo's uniqueness for the status
                    image_sources = search_google_images(description, api_key)
                    logo_domains = get_clean_domains(image_sources)
                    _, unique_logo_status = analyze_domain_uniqueness(logo_domains) # We only need the "Yes/No" status
                    
                    results.append({'retailer': top_retailer, 'status': unique_logo_status})
                    
                    progress_bar.progress((idx + 1) / total)
                    if idx < total - 1:
                        time.sleep(random.uniform(1.0, 1.5))
                
                status_text.success("Analysis Complete!", icon="✅")
            
            results_df = pd.DataFrame(results)
            df['retailer'] = results_df['retailer']
            df['status'] = results_df['status']
            
            st.header("3. Results")
            st.markdown("status is 'Yes' if a unique logo was found in image search.")
            st.dataframe(df, use_container_width=True)
            
            dominant_count = (df['status'] == 'Yes').sum()
            st.metric("Products with a Unique Logo", f"{dominant_count} / {total}")
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results as CSV", csv_data, "logo_analysis_results.csv", "text/csv", use_container_width=True)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

elif not uploaded_file:
    st.info("Please upload a CSV file to get started.")
elif not api_key:
    st.warning("Please enter your SerpAPI key to enable the analysis.")
