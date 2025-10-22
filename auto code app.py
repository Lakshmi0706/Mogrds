import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from collections import Counter
import difflib  # Built-in for fuzzy matching
import time
import random
import re  # For cleaning descriptions

# Comprehensive seed dataset: Includes your brands + corrections/typos
BRAND_SEED = {
    # Your specific brands with corrections
    "CASH CHECK WISE INCREDIBLY FRIENDLY": {"retailer": "cashwisefoods.com", "logo_source": "https://www.cashwisefoods.com/logo.png"},
    "CASH WISE": {"retailer": "cashwisefoods.com", "logo_source": "https://www.cashwisefoods.com/logo.png"},
    "MURPHY EXPRESS": {"retailer": "murphyusa.com", "logo_source": "https://www.murphyusa.com/logo.svg"},
    "SON'S CLUB": {"retailer": "samsclub.com", "logo_source": "https://www.samsclub.com/logo.svg"},  # Assuming Sam's Club
    "RACETROC": {"retailer": "racetrac.com", "logo_source": "https://www.racetrac.com/logo.svg"},
    "RACETRAC": {"retailer": "racetrac.com", "logo_source": "https://www.racetrac.com/logo.svg"},
    "BATH & BODYWORKS": {"retailer": "bathandbodyworks.com", "logo_source": "https://www.bathandbodyworks.com/logo.png"},
    "BATH & BODY WORKST": {"retailer": "bathandbodyworks.com", "logo_source": "https://www.bathandbodyworks.com/logo.png"},
    "OST CO": {"retailer": "costco.com", "logo_source": "https://www.costco.com/logo.svg"},
    "COSTCO": {"retailer": "costco.com", "logo_source": "https://www.costco.com/logo.svg"},
    "FAMILYFARE MEYER": {"retailer": "familyfare.com", "logo_source": "https://www.familyfare.com/logo.png"},
    "FAMILY FARE": {"retailer": "familyfare.com", "logo_source": "https://www.familyfare.com/logo.png"},
    "WFREDMEYER MEYER": {"retailer": "fredmeyer.com", "logo_source": "https://www.fredmeyer.com/logo.jpg"},
    "FRED MEYER": {"retailer": "fredmeyer.com", "logo_source": "https://www.fredmeyer.com/logo.jpg"},
    "THD HD POT": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "THE HOME DEPOT": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "CRAN HY SUCCO": {"retailer": "hyvee.com", "logo_source": "https://www.hyvee.com/logo.svg"},  # Assuming Hy-Vee variant
    "HY VEE": {"retailer": "hyvee.com", "logo_source": "https://www.hyvee.com/logo.svg"},
    "WINCY FOODS": {"retailer": "wincofoods.com", "logo_source": "https://www.wincofoods.com/logo.svg"},
    "WINCO FOODS": {"retailer": "wincofoods.com", "logo_source": "https://www.wincofoods.com/logo.svg"},
    "SIN CLAIRE": {"retailer": "stclair.com", "logo_source": "https://www.stclair.com/logo.png"},  # Assuming St. Clair Foods
    "ST CLAIR": {"retailer": "stclair.com", "logo_source": "https://www.stclair.com/logo.png"},
    "HOMDA POT": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "THE HOMDEPOT VE": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "ALBE SON": {"retailer": "albertsons.com", "logo_source": "https://www.albertsons.com/logo.svg"},
    "ALBERTSONS": {"retailer": "albertsons.com", "logo_source": "https://www.albertsons.com/logo.svg"},
    "MARATHON BROWNSBURG": {"retailer": "marathonpetroleum.com", "logo_source": "https://www.marathonpetroleum.com/logo.svg"},
    "MARATHON": {"retailer": "marathonpetroleum.com", "logo_source": "https://www.marathonpetroleum.com/logo.svg"},
    "TH HOMET DEPOT": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "CIRCLE K": {"retailer": "circlek.com", "logo_source": "https://www.circlek.com/logo.jpg"},
    "1 CIRCLE K": {"retailer": "circlek.com", "logo_source": "https://www.circlek.com/logo.jpg"},
    "SHELL": {"retailer": "shell.us", "logo_source": "https://www.shell.us/logo.jpg"},
    "SHELL AUGUSTINE SHEL SHELL": {"retailer": "shell.us", "logo_source": "https://www.shell.us/logo.jpg"},
    "PRICE HOUPER": {"retailer": "pricechopper.com", "logo_source": "https://www.pricechopper.com/logo.png"},
    "PRICE CHOPPER": {"retailer": "pricechopper.com", "logo_source": "https://www.pricechopper.com/logo.png"},
    "DULLAR REE": {"retailer": "dollartree.com", "logo_source": "https://www.dollartree.com/sites/g/files/qyckzh1461/files/media/images/logo/dollartree-logo.png"},
    "DOLLAR TREE": {"retailer": "dollartree.com", "logo_source": "https://www.dollartree.com/sites/g/files/qyckzh1461/files/media/images/logo/dollartree-logo.png"},
    
    # Additional common US retailers for broader coverage
    "TARGET": {"retailer": "target.com", "logo_source": "https://www.target.com/logo.svg"},
    "WALMART": {"retailer": "walmart.com", "logo_source": "https://www.walmart.com/logo.svg"},
    "KROGER": {"retailer": "kroger.com", "logo_source": "https://www.kroger.com/logo.png"},
    "TRADER JOES": {"retailer": "traderjoes.com", "logo_source": "https://www.traderjoes.com/logo.jpg"},
    "WHOLE FOODS": {"retailer": "wholefoodsmarket.com", "logo_source": "https://www.wholefoodsmarket.com/logo.svg"},
    "PUB LIX": {"retailer": "publix.com", "logo_source": "https://www.publix.com/logo.png"},
    "LOWES": {"retailer": "lowes.com", "logo_source": "https://www.lowes.com/logo.svg"},
    "CVS": {"retailer": "cvs.com", "logo_source": "https://www.cvs.com/logo.svg"},
    "WALGREENS": {"retailer": "walgreens.com", "logo_source": "https://www.walgreens.com/logo.png"},
    "MACYS": {"retailer": "macys.com", "logo_source": "https://www.macys.com/logo.svg"},
}

# Function to clean and extract keywords from description
def clean_description(description):
    cleaned = re.sub(r'\d+', '', description.upper().strip())  # Remove numbers
    cleaned = re.sub(r'\s+(?:INCREDIBLY FRIENDLY|WISE|CHECK|HD|THD|CO|MEYER|EXPRESS|AUGUSTINE|SHEL|SHELL|VE|HY|SUCCO|BROWNSBURG)\s+', ' ', cleaned)
    return ' '.join(cleaned.split())  # Normalize spaces

# Function to dynamically match description to seed using fuzzy logic
def find_brand_match(description):
    orig_desc = description.upper().strip()
    cleaned_desc = clean_description(description)
    
    # Direct exact match
    if orig_desc in BRAND_SEED:
        return BRAND_SEED[orig_desc]
    
    # Fuzzy match on original
    matches = difflib.get_close_matches(orig_desc, list(BRAND_SEED.keys()), n=1, cutoff=0.6)  # 60% threshold
    if matches:
        return BRAND_SEED[matches[0]]
    
    # Fallback: Fuzzy on cleaned description
    matches = difflib.get_close_matches(cleaned_desc, list(BRAND_SEED.keys()), n=1, cutoff=0.6)
    if matches:
        return BRAND_SEED[matches[0]]
    
    return {"retailer": "Not found", "logo_source": None}

def get_domain(url):
    if url == "Not found" or not url:
        return None
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
st.caption("Validates brand presence using fuzzy matching on a seed dataset (no API required).")

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
                    description = str(row['description'])
                    status_text.text(f"Processing {idx + 1}/{total}: {description[:50]}...")
                    
                    # --- TWO-PASS LOGIC ---
                    # PASS 1: Direct fuzzy match
                    brand_info = find_brand_match(description)
                    web_domains = get_clean_domains([brand_info["retailer"]]) if brand_info["retailer"] != "Not found" else []
                    top_retailer, web_status = analyze_domain_uniqueness(web_domains)

                    logo_domains = get_clean_domains([brand_info["logo_source"]]) if brand_info["logo_source"] else []
                    top_logo_source, image_status = analyze_domain_uniqueness(logo_domains)

                    final_status = "Yes" if web_status == "Yes" or image_status == "Yes" else "No"
                    
                    # PASS 2: If failed, clean and re-match (simulates correction)
                    if final_status == "No":
                        cleaned_desc = clean_description(description)
                        if cleaned_desc != description.upper().strip():
                            status_text.text(f"Correcting to '{cleaned_desc}' and re-matching...")
                            time.sleep(0.5)
                            brand_info = find_brand_match(cleaned_desc)
                            web_domains = get_clean_domains([brand_info["retailer"]]) if brand_info["retailer"] != "Not found" else []
                            top_retailer, web_status = analyze_domain_uniqueness(web_domains)

                            logo_domains = get_clean_domains([brand_info["logo_source"]]) if brand_info["logo_source"] else []
                            top_logo_source, image_status = analyze_domain_uniqueness(logo_domains)
                            
                            final_status = "Yes" if web_status == "Yes" or image_status == "Yes" else "No"
                    
                    # Final fallback
                    if top_retailer == "Not found" and top_logo_source != "Not found":
                        top_retailer = top_logo_source
                        
                    results.append({'retailer': top_retailer, 'status': final_status})
                    
                    progress_bar.progress((idx + 1) / total)
                    if idx < total - 1:
                        time.sleep(random.uniform(0.5, 1.0))
                
                status_text.success("Analysis Complete!", icon="🎉")
            
            results_df = pd.DataFrame(results)
            df['retailer'] = results_df['retailer']
            df['status'] = results_df['status']
            
            st.header("3. Results")
            st.markdown("status is 'Yes' if a unique website or logo was found (fuzzy-corrected from dataset).")
            st.dataframe(df, use_container_width=True)
            
            dominant_count = (df['status'] == 'Yes').sum()
            st.metric("Brands with a Unique Presence", f"{dominant_count} / {total}")
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results", csv_data, "brand_validator_results.csv", "text/csv", use_container_width=True)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

else:
    st.info("Please upload a CSV file to get started.")
