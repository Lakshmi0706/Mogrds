import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from collections import Counter
import re  # For cleaning
# Removed difflib, time, and random as they are no longer needed for this logic

# --- Tool Import ---
# This line assumes the 'google_search' tool is available in your environment.
from google_search import google_search

# --- Helper Functions (Modified & Kept) ---

def clean_description(description):
    """Cleans the description for a better Google Search query."""
    if not isinstance(description, str):
        return ""
    cleaned = re.sub(r'\d+', '', description.upper().strip())  # Remove numbers
    # Remove common transactional/location noise words
    cleaned = re.sub(r'\s+(?:INSTORE|PICKUP|ONLINE|\.COM|ACCOUNT SCRAPING|GAS|FUEL|STORE|SHOP|MARKET|INC|LLC|CORP|#)\s+', ' ', cleaned)
    cleaned = re.sub(r'[^\w\s]', '', cleaned) # Remove punctuation
    return ' '.join(cleaned.split())  # Normalize spaces

def get_domain(url):
    """Extracts the netloc from a URL."""
    if url == "Not found" or not url:
        return None
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return None

def get_clean_domains(links_or_sources):
    """Extract and clean domains, filtering out non-retail/social sites."""
    domains = []
    # Expanded list of domains to skip
    skip_these = [
        "facebook", "instagram", "twitter", "linkedin", "youtube", "reddit", "tiktok",
        "wikipedia", "forbes", "bloomberg", "cnn", "wsj", "nytimes", "yelp",
        "tripadvisor", "mapquest", "google", "apple", "microsoft", "foursquare",
        "bbb.org", "yellowpages", "business.site"
    ]
    for link in links_or_sources:
        domain = get_domain(link)
        if domain and not any(skip in domain.lower() for skip in skip_these):
            domains.append(domain)
    return domains

def analyze_domain_uniqueness(domains):
    """
    Determines the top domain and if it's a unique, clear winner.
    'Yes' status requires a domain to be the only one found
    or clearly have more mentions than the second most common domain.
    """
    if not domains:
        return "Not found", "No"
    
    domain_counts = Counter(domains)
    most_common_list = domain_counts.most_common(2)
    top_domain, top_count = most_common_list[0]
    
    # Strict criteria for a "unique" match
    if top_count > 0:
        if len(most_common_list) == 1:
            # Only one domain was found in the search results
            return top_domain, "Yes"
        if top_count > most_common_list[1][1]:
            # The top domain appeared strictly more times than the runner-up
            return top_domain, "Yes"
            
    # If there's a tie or it's otherwise ambiguous, it's not a unique match
    return top_domain, "No"

# --- New Core Logic Function ---

def find_brand_from_google(description):
    """
    Searches Google for the brand description and analyzes results
    for a single, dominant merchant domain.
    """
    if not description:
        return {"retailer": "Not found", "status": "No"}
        
    try:
        # 1. Call the Google Search API
        search_response = google_search.search(queries=[description])
        
        # 2. Extract all source links
        links = [result.source_link for result in search_response if result.source_link]
        
        if not links:
            return {"retailer": "Not found", "status": "No"}
        
        # 3. Clean the domains (filters out social media, news, etc.)
        clean_domains = get_clean_domains(links)
        
        # 4. Analyze for a unique winner
        top_retailer, is_dominant_status = analyze_domain_uniqueness(clean_domains)
        
        return {'retailer': top_retailer, 'status': is_dominant_status}
    
    except Exception as e:
        # Handle potential API errors
        st.warning(f"Error searching for '{description}': {e}")
        return {"retailer": "Error", "status": "No"}

# --- Streamlit App UI ---

st.set_page_config(page_title="Intelligent Brand Validator", page_icon="🧠", layout="centered")

st.title("🧠 Intelligent Brand Validator")
st.caption("Validates brand presence using live Google Search to find a unique merchant match.")

st.header("1. Upload Your File")
uploaded_file = st.file_uploader("Your CSV must have a 'description' column.", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        if 'description' not in df.columns:
            st.error("Upload failed! The CSV must contain a 'description' column.", icon="🚨")
            st.stop()
        
        st.success(f"File uploaded! Found {len(df)} brands to analyze.")
        
        st.header("2. Start Analysis")
        start_btn = st.button("Validate Brand Presence", type="primary", use_container_width=True)
        
        if start_btn:
            with st.spinner("Analyzing... Contacting Google Search API..."):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total = len(df)
                for idx, row in df.iterrows():
                    description = str(row['description'])
                    status_text.text(f"Processing {idx + 1}/{total}: {description[:50]}...")
                    
                    # 1. Clean the description for a better search query
                    cleaned_desc = clean_description(description)
                    
                    # 2. Call the new Google Search-based function
                    # This function encapsulates the API call and analysis
                    search_result = find_brand_from_google(cleaned_desc) 
                    
                    results.append(search_result)
                    
                    # 3. Update progress
                    progress_bar.progress((idx + 1) / total)
                    # No artificial sleep needed; API call provides natural delay
                
                status_text.success("Analysis Complete!", icon="🎉")
            
            # Combine results with original dataframe
            results_df = pd.DataFrame(results)
            df['retailer'] = results_df['retailer']
            df['status'] = results_df['status']
            
            st.header("3. Results")
            st.markdown("status is 'Yes' if Google Search results showed one dominant, unique website.")
            st.dataframe(df, use_container_width=True)
            
            dominant_count = (df['status'] == 'Yes').sum()
            st.metric("Brands with a Unique Presence", f"{dominant_count} / {total}")
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results", csv_data, "brand_validator_results.csv", "text/csv", use_container_width=True)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

else:
    st.info("Please upload a CSV file to get started.")
