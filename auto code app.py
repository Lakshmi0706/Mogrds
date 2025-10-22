[11:24 PM, 10/21/2025] Sai Lakshmi✨: import streamlit as st
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
            return…
[11:31 PM, 10/21/2025] Sai Lakshmi✨: import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from collections import Counter
import time
import random

def search_google_web(description, api_key):
    """Search Google Web for the official retailer website."""
    query = f'"{description}" official website USA'
    params = {"q": query, "engine": "google", "gl": "us", "hl": "en", "api_key": api_key, "num": 10}
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

def search_google_images(description, api_key):
    """Search Google Images for logos related to the description."""
    query = f'"{description}" logo'
    params = {"q": query, "engine": "google_images", "gl": "us", "hl": "en", "api_key": api_key}
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            st.warning(f"Image search error for '{description}': {data['error']}")
            return []
        return [result['source'] for result in data.get("images_results", []) if 'source' in result]
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't connect to image search API: {e}")
        return []

# MODIFIED FUNCTION: Contains the new, expanded list of sites to skip.
def get_clean_domains(links_or_sources):
    """Extract and clean domains, filtering out a comprehensive list of non-retail sites."""
    domains = []
    
    # NEW: Expanded list to filter out more irrelevant domains as requested.
    skip_these = [
        # Major Aggregators & Marketplaces
        "amazon", "ebay", "walmart", "target", "costco", "etsy",
        # Social Media & Content Platforms
        "facebook", "instagram", "twitter", "pinterest", "linkedin", "youtube", "reddit", "tiktok", "quora",
        # News & Information Outlets
        "wikipedia", "forbes", "bloomberg", "reuters", "cnn", "wsj", "nytimes", "businessinsider", "techcrunch",
        # Directories & Review Sites
        "yelp", "tripadvisor", "mapquest", "foursquare",
        # Delivery Services
        "instacart", "doordash", "grubhub", "postmates", "ubereats",
        # Stock Photo/Vector Sites
        "istockphoto", "shutterstock", "freepik", "vecteezy", "gettyimages", "adobestock",
        # Tech Platforms & Payment Systems
        "google", "apple", "microsoft", 
        # Dollar Stores & General Retailers (to find specific brand sites)
        "dollartree", "familydollar", "dollarstore", "biglots",
        # Generic terms that often appear in non-brand domains
        "business", "news", "reviews", "top10", "coupons"
    ]
    
    for link in links_or_sources:
        try:
            domain = urlparse(f"http://{link}").netloc.replace("www.", "")
            if domain and not any(skip in domain.lower() for skip in skip_these):
                domains.append(domain)
        except Exception:
            continue
    return domains

def analyze_domain_uniqueness(domains):
    """Determines the top domain and if it's a unique, clear winner."""
    if not domains:
        return "Not found", "No"
    
    domain_counts = Counter(domains)
    most_common_list = domain_counts.most_common(2)
    top_domain, top_count = most_common_list[0]
    
    is_dominant = "No"
    if top_count > 1:
        if len(most_common_list) == 1 or top_count > most_common_list[1][1]:
            is_dominant = "Yes"
            
    return top_domain, is_dominant

# --- Streamlit App UI ---

st.set_page_config(page_title="Brand Presence Validator", page_icon="✅", layout="centered")

st.title("✅ Brand Presence Validator")
st.caption("Find a retailer's website and check for a unique brand presence using Web and Image search.")

api_key = st.secrets.get("SERPAPI_KEY") if hasattr(st, 'secrets') else None
if not api_key:
    api_key = st.text_input("Enter your SerpAPI API Key", type="password")

st.header("1. Upload Your File")
uploaded_file = st.file_uploader("Your CSV must have a 'description' column.", type=["csv"])

if uploaded_file and api_key:
    try:
        df = pd.read_csv(uploaded_file)
        if 'description' not in df.columns:
            st.error("Upload failed! The CSV must contain a 'description' column.", icon="🚨")
            st.stop()
        
        st.success(f"File uploaded! Found {len(df)} brands to analyze.")
        
        st.header("2. Start Analysis")
        start_btn = st.button("Validate Brand Presence", type="primary", use_container_width=True)
        
        if start_btn:
            with st.spinner("Analyzing... This may take a moment."):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total = len(df)
                for idx, row in df.iterrows():
                    description = row['description']
                    status_text.text(f"Processing {idx + 1}/{total}: {description[:50]}...")
                    
                    # --- NEW COMBINED LOGIC ---
                    # 1. Analyze web search results
                    web_links = search_google_web(description, api_key)
                    web_domains = get_clean_domains(web_links)
                    top_retailer, web_status = analyze_domain_uniqueness(web_domains)

                    # 2. Analyze image search results
                    image_sources = search_google_images(description, api_key)
                    logo_domains = get_clean_domains(image_sources)
                    top_logo_source, image_status = analyze_domain_uniqueness(logo_domains)

                    # 3. Determine final status with "OR" logic
                    final_status = "Yes" if web_status == "Yes" or image_status == "Yes" else "No"
                    
                    # 4. Fallback: If web search failed, use the top logo source as the retailer
                    if top_retailer == "Not found" and top_logo_source != "Not found":
                        top_retailer = top_logo_source
                        
                    results.append({'retailer': top_retailer, 'status': final_status})
                    
                    progress_bar.progress((idx + 1) / total)
                    if idx < total - 1:
                        time.sleep(random.uniform(1.0, 1.5))
                
                status_text.success("Analysis Complete!", icon="🎉")
            
            results_df = pd.DataFrame(results)
            df['retailer'] = results_df['retailer']
            df['status'] = results_df['status']
            
            st.header("3. Results")
            st.markdown("status is 'Yes' if a unique website *OR* a unique logo was found.")
            st.dataframe(df, use_container_width=True)
            
            dominant_count = (df['status'] == 'Yes').sum()
            st.metric("Brands with a Unique Presence", f"{dominant_count} / {total}")
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results as CSV", csv_data, "brand_presence_results.csv", "text/csv", use_container_width=True)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

elif not uploaded_file:
    st.info("Please upload a CSV file to get started.")
elif not api_key:
    st.warning("Please enter your SerpAPI key to enable the analysis.")
