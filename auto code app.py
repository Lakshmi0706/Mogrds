import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from collections import Counter
import time
import random
import re # Import regex for advanced cleaning

# --- UTILITY FUNCTIONS ---

def clean_domain_to_name(domain):
    """Converts a domain (e.g., 'dollartree.com') into a retailer name (e.g., 'Dollar Tree')."""
    if domain == "Not found":
        return domain
    
    # List of common generic/junk words that should be removed if they appear as standalone parts
    # Added "alamy" and "willow" based on your previous screenshot feedback.
    junk_words = ["logopedia", "logos", "vector", "mock", "current", "publishing", "food", "frys", "alamy", "willow"]
    
    # 1. Remove common TLDs (top-level domains)
    name = re.sub(r'\.(com|net|org|co|us|biz|info|io|ai|shop|store|app|inc|ltd)$', '', domain, flags=re.IGNORECASE)
    
    # 2. Replace common separators with space
    name = name.replace('-', ' ').replace('.', ' ')
    
    # 3. Capitalize words (Title Case)
    name_parts = [part.title() for part in name.split()]
    
    # 4. Filter out any remaining junk words from the final name
    final_name_parts = [part for part in name_parts if part.lower() not in junk_words]
    
    final_name = " ".join(final_name_parts)
    
    # Fallback to the title-cased name if filtering was too aggressive but still produced a result
    if not final_name and name.strip():
        return name.title().strip()
    
    # If still empty, return original domain for debugging, or default
    if not final_name:
        return "Not found"
    
    return final_name.strip()

def search_google_web(description, api_key):
    """
    Searches Google Web. Returns a tuple: (list_of_links, corrected_query_string).
    """
    query = f'"{description}" official website USA'
    params = {"q": query, "engine": "google", "gl": "us", "hl": "en", "api_key": api_key, "num": 10}
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            return [], None
        
        links = [result['link'] for result in data.get("organic_results", []) if 'link' in result]
        corrected_query = data.get("search_information", {}).get("query_displayed")
        return links, corrected_query
        
    except requests.exceptions.RequestException:
        return [], None

def search_google_images(description, api_key):
    """
    Searches Google Images. Returns a tuple: (list_of_sources, corrected_query_string).
    """
    query = f'"{description}" logo'
    params = {"q": query, "engine": "google_images", "gl": "us", "hl": "en", "api_key": api_key}
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            return [], None
            
        sources = [result['source'] for result in data.get("images_results", []) if 'source' in result]
        corrected_query = data.get("search_information", {}).get("query_displayed")
        return sources, corrected_query
        
    except requests.exceptions.RequestException:
        return [], None

def get_clean_domains(links_or_sources):
    """Extract and clean domains, filtering out a comprehensive list of non-retail sites."""
    domains = []
    # Expanded list of domain segments to skip
    skip_these = [
        "amazon", "ebay", "walmart", "target", "costco", "etsy", "facebook", "instagram", 
        "twitter", "pinterest", "linkedin", "youtube", "reddit", "tiktok", "quora", "wikipedia", 
        "forbes", "bloomberg", "reuters", "cnn", "wsj", "nytimes", "businessinsider", 
        "techcrunch", "yelp", "tripadvisor", "mapquest", "foursquare", "instacart", 
        "doordash", "grubhub", "postmates", "ubereats", "istockphoto", "shutterstock", 
        "freepik", "vecteezy", "gettyimages", "adobestock", "google", "apple", "microsoft", 
        "dollartree", "familydollar", "dollarstore", "biglots", "business", "news", 
        "reviews", "top10", "coupons", "vectorstock", "logobrand", "logobucket", "logos", 
        "alamy", "willowtree", "andnowuknow", "currentpublishing", "wincofoods", "sunoco" # Added based on results feedback
    ]
    for link in links_or_sources:
        try:
            # Add scheme for robustness
            parsed = urlparse(f"http://{link}")
            domain = parsed.netloc.replace("www.", "")
            
            # Filter: must not be empty, must not start with protocol/noise, and must not contain skip words
            # The domain must contain at least one dot to be a real domain (e.g., 'example.com')
            if (domain and '.' in domain and 
                not domain.startswith('http') and 
                not any(skip in domain.lower() for skip in skip_these)):
                domains.append(domain)
        except Exception:
            continue
    return domains

def analyze_domain_uniqueness(domains):
    """Determines the top domain and if it's a unique, clear winner."""
    clean_domains = [d for d in domains if d]
    
    if not clean_domains:
        return "Not found", "No"
    
    domain_counts = Counter(clean_domains)
    most_common_list = domain_counts.most_common(2)
    top_domain, top_count = most_common_list[0]
    
    is_dominant = "No"
    if top_count > 1:
        # A domain must appear more than once AND be strictly more frequent than the second common domain 
        if len(most_common_list) == 1 or top_count > most_common_list[1][1]:
            is_dominant = "Yes"
            
    return top_domain, is_dominant

# --- Streamlit App UI ---

st.set_page_config(page_title="Intelligent Brand Validator", page_icon="🧠", layout="centered")

st.title("🧠 Intelligent Brand Validator")
st.caption("Retailer names are now displayed in a clean, human-readable format, filtered for junk results.")

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
        
        df['sno'] = range(1, 1 + len(df))
        
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
                    current_sno = row['sno']
                    findings = []
                    
                    status_text.text(f"Processing {current_sno}/{total}: {description[:50]}...")
                    
                    # --- Core Logic Functions ---
                    def run_searches(desc):
                        web_links, web_correction = search_google_web(desc, api_key)
                        web_domains = get_clean_domains(web_links)
                        top_retailer_domain, web_status = analyze_domain_uniqueness(web_domains)

                        image_sources, image_correction = search_google_images(desc, api_key)
                        logo_domains = get_clean_domains(image_sources)
                        top_logo_domain, image_status = analyze_domain_uniqueness(logo_domains)
                        
                        return top_retailer_domain, web_status, top_logo_domain, image_status, web_correction, image_correction

                    # PASS 1: Search with the original description
                    (top_retailer_domain, web_status, top_logo_domain, image_status, 
                     web_correction, image_correction) = run_searches(description)

                    final_status = "Yes" if web_status == "Yes" or image_status == "Yes" else "No"
                    
                    corrected_query = web_correction or image_correction
                    
                    # PASS 2: If first pass failed, try again with Google's corrected query
                    if final_status == "No" and corrected_query and corrected_query.lower() != description.lower():
                        status_text.text(f"Processing {current_sno}/{total}: Correcting to '{corrected_query}'...")
                        time.sleep(0.5) 
                        
                        # Re-run searches with the corrected query
                        (top_retailer_domain, web_status, top_logo_domain, image_status, _, _) = run_searches(corrected_query)
                        
                        final_status = "Yes" if web_status == "Yes" or image_status == "Yes" else "No"
                        
                        findings.append(f"Query corrected from '{description}' to '{corrected_query}'.")

                    # --- Build Final Retailer Name and Findings Message ---
                    
                    # Determine the domain to use (prioritize web retailer if available, otherwise use image source)
                    final_retailer_domain = top_retailer_domain
                    if final_retailer_domain == "Not found" and top_logo_domain != "Not found":
                        final_retailer_domain = top_logo_domain
                        
                    # CRITICAL: Convert the final domain to a human-readable name ONLY if status is Yes and a domain was found
                    if final_status == "Yes" and final_retailer_domain != "Not found":
                         final_retailer_name = clean_domain_to_name(final_retailer_domain)
                    else:
                         # If status is NO, or domain is Not found, retailer name should be Not found
                         final_retailer_name = "Not found"
                        
                    # Update findings with the clean name
                    if final_status == "Yes":
                        if web_status == "Yes" and image_status == "Yes":
                            findings.append(f"Unique presence confirmed by both Website and Logo for '{final_retailer_name}'.")
                        elif web_status == "Yes":
                            findings.append(f"Unique website dominance found for retailer: '{final_retailer_name}'.")
                        elif image_status == "Yes":
                            findings.append(f"Unique logo dominance found for retailer: '{final_retailer_name}'.")
                    else:
                        findings.append("No dominant, unique website or logo was found.")
                        
                    results.append({
                        'sno': current_sno,
                        'retailer': final_retailer_name, 
                        'status': final_status,
                        'findings': " | ".join(findings) 
                    })
                    
                    progress_bar.progress((idx + 1) / total)
                    if idx < total - 1:
                        time.sleep(random.uniform(1.0, 1.5))
                
                status_text.success("Analysis Complete!", icon="🎉")
            
            results_df = pd.DataFrame(results)
            
            # Merge results back into the original DataFrame (using 'sno')
            df_final = df.merge(results_df, on='sno', how='left')

            # FINAL STEP: Select and reorder columns as requested
            output_columns = ['sno', 'description', 'retailer', 'status', 'findings']
            df_final = df_final[output_columns]

            st.header("3. Results")
            st.markdown("status is 'Yes' if a unique website *OR* unique logo was found (typos auto-corrected).")
            st.dataframe(df_final, use_container_width=True)
            
            dominant_count = (df_final['status'] == 'Yes').sum()
            st.metric("Brands with a Unique Presence", f"{dominant_count} / {total}")
            
            csv_data = df_final.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Results as CSV", 
                csv_data, 
                "brand_validator_results.csv", 
                "text/csv", 
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

elif not uploaded_file:
    st.info("Please upload a CSV file to get started.")
elif not api_key:
    st.warning("Please enter your SerpAPI key to enable the analysis.")
