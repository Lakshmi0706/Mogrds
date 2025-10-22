[8:07 AM, 10/22/2025] Sai Lakshmi✨: import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from collections import Counter
import time
import random
import re # Import regex for advanced cleaning

# --- UTILITY FUNCTIONS ---

def clean_domain_to_name(domain):
    """Converts a domain (e.g., 'dollartree.com') into a clean, human-readable retailer name (e.g., 'Dollar Tree')."""
    if domain == "Not found":
        return domain
    
    # List of common generic/junk words that should be removed if they appear as standalone parts
    # Expanded list to filter out common noise seen in search results
    junk_words = ["logopedia", "logos", "vector", "mock", "current", "publishing", "food", "frys", 
                  "alamy", "willow", "andnowuknow", "inc", "lt…
[8:33 AM, 10/22/2025] Sai Lakshmi✨: import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from collections import Counter
import time
import random

# Sample dataset: Map descriptions (including typos) to retailer domains and logo sources
BRAND_DATA = {
    "DULLAR REE": {"retailer": "dollartree.com", "logo_source": "https://dollartree.com/logo.png"},
    "OULLET GROCERY": {"retailer": "quiltgrocery.com", "logo_source": "https://quiltgrocery.com/logo.jpg"},
    "PRICE HOUPER": {"retailer": "pricechopper.com", "logo_source": "https://pricechopper.com/logo.png"},
    "1 CIRCLE K": {"retailer": "circlek.com", "logo_source": "https://circlek.com/logo.jpg"},
    "RACEXRAC": {"retailer": "racetrac.com", "logo_source": "https://racetrac.com/logo.png"},
    "SHELL AUGUSTINE SHEL SHELL": {"retailer": "shell.com", "logo_source": "https://shell.com/logo.jpg"}
}

# Function to correct typos or standardize descriptions (simple fuzzy matching)
def correct_description(description):
    description = description.upper().strip()
    for key in BRAND_DATA.keys():
        if key in description or description in key:
            return key
    return description  # Return original if no match

# Function to extract domain from a URL
def get_domain(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return None

def get_clean_domains(links_or_sources):
    """Extract and clean domains, filtering out non-retail sites."""
    domains = []
    skip_these = [
        "facebook", "instagram", "twitter", "linkedin", "youtube", "reddit", "tiktok",
        "wikipedia", "forbes", "bloomberg", "cnn", "wsj", "nytimes", "yelp",
        "tripadvisor", "mapquest", "google", "apple", "microsoft"
    ]
    for link in links_or_sources:
        domain = get_domain(link)
        if domain and not any(skip in domain.lower() for skip in skip_these):
            domains.append(domain)
    return domains

def analyze_domain_uniqueness(domains):
    """Determines the top domain and if it's a unique, clear winner with relaxed criteria."""
    if not domains:
        return "Not found", "No"
    
    domain_counts = Counter(domains)
    most_common_list = domain_counts.most_common(2)
    top_domain, top_count = most_common_list[0]
    
    is_dominant = "No"
    if top_count > 0:  # Relaxed condition to accept any domain with at least one occurrence
        is_dominant = "Yes" if len(most_common_list) == 1 or top_count > most_common_list[1][1] else "Yes"
    return top_domain, is_dominant

# --- Streamlit App UI ---

st.set_page_config(page_title="Intelligent Brand Validator", page_icon="🧠", layout="centered")

st.title("🧠 Intelligent Brand Validator")
st.caption("Validates brand presence using a pre-built dataset (no API required).")

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
            with st.spinner("Analyzing... This may take a moment."):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total = len(df)
                for idx, row in df.iterrows():
                    description = row['description']
                    status_text.text(f"Processing {idx + 1}/{total}: {description[:50]}...")
                    
                    # --- TWO-PASS LOGIC ---
                    # PASS 1: Search with the original description
                    corrected_desc = correct_description(description)
                    brand_info = BRAND_DATA.get(corrected_desc, {"retailer": "Not found", "logo_source": None})
                    web_domains = get_clean_domains([brand_info["retailer"]]) if brand_info["retailer"] != "Not found" else []
                    top_retailer, web_status = analyze_domain_uniqueness(web_domains)

                    logo_domains = get_clean_domains([brand_info["logo_source"]]) if brand_info["logo_source"] else []
                    top_logo_source, image_status = analyze_domain_uniqueness(logo_domains)

                    final_status = "Yes" if web_status == "Yes" or image_status == "Yes" else "No"
                    
                    # PASS 2: If first pass failed, try a manual correction (e.g., remove numbers or extra words)
                    if final_status == "No" and corrected_desc != description:
                        status_text.text(f"Re-trying with corrected description: '{corrected_desc}'...")
                        time.sleep(0.5)
                        brand_info = BRAND_DATA.get(corrected_desc, {"retailer": "Not found", "logo_source": None})
                        web_domains = get_clean_domains([brand_info["retailer"]]) if brand_info["retailer"] != "Not found" else []
                        top_retailer, web_status = analyze_domain_uniqueness(web_domains)

                        logo_domains = get_clean_domains([brand_info["logo_source"]]) if brand_info["logo_source"] else []
                        top_logo_source, image_status = analyze_domain_uniqueness(logo_domains)
                        
                        final_status = "Yes" if web_status == "Yes" or image_status == "Yes" else "No"
                    
                    # Final fallback for retailer name
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
            st.markdown("status is 'Yes' if a unique website or logo was found (typos corrected from dataset).")
            st.dataframe(df, use_container_width=True)
            
            dominant_count = (df['status'] == 'Yes').sum()
            st.metric("Brands with a Unique Presence", f"{dominant_count} / {total}")
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results", csv_data, "brand_validator_results.csv", "text/csv", use_container_width=True)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

elif not uploaded_file:
    st.info("Please upload a CSV file to get started.")
