import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from collections import Counter
import difflib
import time
import random
import re
from googleapiclient.discovery import build

# --- BRAND SEED ---
BRAND_SEED = {
    "DOLLAR TREE": {"retailer": "dollartree.com", "logo_source": "https://www.dollartree.com/sites/g/files/qyckzh1461/files/media/images/logo/dollartree-logo.png"},
    "MURPHY USA": {"retailer": "murphyusa.com", "logo_source": "https://www.murphyusa.com/logo.svg"},
    "FIVE BELOW": {"retailer": "fivebelow.com", "logo_source": "https://www.fivebelow.com/logo.png"},
}

KNOWN_DOMAINS = [entry["retailer"] for entry in BRAND_SEED.values()]

# --- Google Custom Search Setup (Hardcoded Keys) ---
@st.cache_resource
def get_custom_search_service():
    api_key = "AIzaSyBYS2Qsc6rES4sKtr3wcz-74V5leOgJaV4"  # Your API Key
    cse_id = "2eddc6d351e647af"  # Your Search Engine ID
    service = build("customsearch", "v1", developerKey=api_key)
    return service, cse_id

def web_search_for_retailer(description, service, cse_id):
    query = f'"{description}" retailer site'
    try:
        res = service.cse().list(q=query, cx=cse_id, num=1).execute()
        items = res.get("items", [])
        if items:
            top_url = items[0]["link"]
            top_domain = urlparse(top_url).netloc.replace("www.", "")
            for known in KNOWN_DOMAINS:
                if known in top_domain or top_domain in known:
                    return known
        return None
    except Exception as e:
        st.warning(f"Search error for '{description}': {e}. Skipping override.")
        return None

# --- Cleaning & Matching ---
def clean_description(description):
    cleaned = re.sub(r'\d+', '', description.upper().strip())
    cleaned = re.sub(r'\s+(?:INCREDIBLY FRIENDLY|WISE|CHECK|HD|THD|CO|MEYER|EXPRESS|INSTORE|PICKUP|ONLINE|\.COM|ACCOUNT SCRAPING|AUGUSTINE|SHEL|SHELL|VE|HY|SUCCO|BROWNSBURG)\s+', ' ', cleaned)
    return ' '.join(cleaned.split())

def find_brand_match(description):
    orig_desc = description.upper().strip()
    cleaned_desc = clean_description(description)
    if orig_desc in BRAND_SEED:
        return BRAND_SEED[orig_desc]
    matches = difflib.get_close_matches(orig_desc, list(BRAND_SEED.keys()), n=1, cutoff=0.6)
    if matches:
        return BRAND_SEED[matches[0]]
    matches = difflib.get_close_matches(cleaned_desc, list(BRAND_SEED.keys()), n=1, cutoff=0.6)
    if matches:
        return BRAND_SEED[matches[0]]
    return {"retailer": "Not found", "logo_source": None}

def get_domain(url):
    if url == "Not found" or not url:
        return None
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        if domain.endswith(".com"):
            return domain[:-4]
        elif domain.endswith(".us"):
            return domain[:-3]
        return domain
    except:
        return None

def get_clean_domains(links_or_sources):
    domains = []
    skip_these = ["facebook", "instagram", "twitter", "linkedin", "youtube", "reddit", "tiktok", "wikipedia", "forbes", "bloomberg", "cnn", "wsj", "nytimes", "yelp", "tripadvisor", "mapquest", "google", "apple", "microsoft"]
    for link in links_or_sources:
        domain = get_domain(link)
        if domain and not any(skip in domain.lower() for skip in skip_these):
            domains.append(domain)
    return domains

def analyze_domain_uniqueness(domains):
    if not domains:
        return "Not found", "No"
    domain_counts = Counter(domains)
    most_common_list = domain_counts.most_common(2)
    top_domain, top_count = most_common_list[0]
    is_dominant = "Yes" if top_count > 0 and (len(most_common_list) == 1 or top_count > most_common_list[1][1]) else "No"
    return top_domain, is_dominant

# --- Streamlit UI ---
st.set_page_config(page_title="Intelligent Brand Validator", page_icon="🧠", layout="centered")
st.title("🧠 Intelligent Brand Validator")
st.caption("Validates with exact match, fuzzy fallback, and Google Custom Search for accurate 'retailer site' verification.")

st.header("1. Upload Your File")
uploaded_file = st.file_uploader("Your CSV must have a 'description' column.", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        if 'description' not in df.columns:
            st.error("Upload failed! The CSV must contain a 'description' column.", icon="🚨")
            st.stop()
        
        st.success(f"File uploaded! Found {len(df)} brands to analyze.")
        
        service, cse_id = get_custom_search_service()
        
        st.header("2. Start Analysis")
        start_btn = st.button("Validate Brand Presence", type="primary", use_container_width=True)
        
        if start_btn:
            with st.spinner("Analyzing... This may take a moment."):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total = len(df)
                for idx, row in df.iterrows():
                    description = str(row['description'])
                    status_text.text(f"Processing {idx + 1}/{total}: {description[:50]}...")
                    
                    orig_desc = description.upper().strip()
                    if orig_desc in BRAND_SEED:
                        brand_info = BRAND_SEED[orig_desc]
                        final_status = "Yes"
                    else:
                        final_status = "No"
                        brand_info = {"retailer": "Not found", "logo_source": None}
                    
                    if final_status == "No":
                        brand_info = find_brand_match(description)
                        web_domains = get_clean_domains([brand_info["retailer"]]) if brand_info["retailer"] != "Not found" else []
                        top_retailer_temp, web_status = analyze_domain_uniqueness(web_domains)
                        logo_domains = get_clean_domains([brand_info["logo_source"]]) if brand_info["logo_source"] else []
                        top_logo_source, image_status = analyze_domain_uniqueness(logo_domains)
                        final_status = "Yes" if web_status == "Yes" or image_status == "Yes" else "No"
                    
                    top_retailer = get_domain(brand_info["retailer"]) if brand_info["retailer"] != "Not found" else "Not found"
                    
                    if final_status == "No":
                        search_domain = web_search_for_retailer(description, service, cse_id)
                        if search_domain:
                            top_retailer = get_domain(search_domain)
                            final_status = "Yes"
                            st.info(f"Google Search Override: '{description}' matched '{top_retailer}' (top result domain: {search_domain}).")
                    
                    if top_retailer == "Not found" and brand_info.get("logo_source"):
                        top_retailer = get_domain(brand_info["logo_source"])
                    
                    results.append({'retailer': top_retailer, 'status': final_status})
                    
                    progress_bar.progress((idx + 1) / total)
                    if idx < total - 1:
                        time.sleep(random.uniform(0.5, 1.0))
                
                status_text.success("Analysis Complete!", icon="🎉")
            
            results_df = pd.DataFrame(results)
            df['retailer'] = results_df['retailer']
            df['status'] = results_df['status']
            
            st.header("3. Results")
            st.markdown("status is 'Yes' if exact/fuzzy/Google search matches a known official site.")
            st.dataframe(df, use_container_width=True)
            
            dominant_count = (df['status'] == 'Yes').sum()
            st.metric("Brands with a Unique Presence", f"{dominant_count} / {total}")
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results", csv_data, "brand_validator_results.csv", "text/csv", use_container_width=True)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

else:
    st.info("Please upload a CSV file to get started.")
