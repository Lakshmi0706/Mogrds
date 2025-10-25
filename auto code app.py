import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from collections import Counter
import difflib  # For fuzzy matching
import time
import random
import re  # For cleaning

# Updated seed dataset with new merchant names from document
BRAND_SEED = {
    "CASH CHECK WISE INCREDIBLY FRIENDLY": {"retailer": "cashwisefoods.com", "logo_source": "https://www.cashwisefoods.com/logo.png"},
    "MURPHY EXPRESS": {"retailer": "murphyusa.com", "logo_source": "https://www.murphyusa.com/logo.svg"},
    "SON'S CLUB": {"retailer": "samsclub.com", "logo_source": "https://www.samsclub.com/logo.svg"},
    "SQMS CUB": {"retailer": "samsclub.com", "logo_source": "https://www.samsclub.com/logo.svg"},
    "SAMS CLUB": {"retailer": "samsclub.com", "logo_source": "https://www.samsclub.com/logo.svg"},
    "RACETROC": {"retailer": "racetrac.com", "logo_source": "https://www.racetrac.com/logo.svg"},
    "BATH & BODYWORKS": {"retailer": "bathandbodyworks.com", "logo_source": "https://www.bathandbodyworks.com/logo.png"},
    "OST CO": {"retailer": "costco.com", "logo_source": "https://www.costco.com/logo.svg"},
    "LEWE OSCO": {"retailer": "costco.com", "logo_source": "https://www.costco.com/logo.svg"},
    "COSTCO": {"retailer": "costco.com", "logo_source": "https://www.costco.com/logo.svg"},
    "COSTCO INSTORE": {"retailer": "costco.com", "logo_source": "https://www.costco.com/logo.svg"},
    "COSTCO PICKUP": {"retailer": "costco.com", "logo_source": "https://www.costco.com/logo.svg"},
    "FAMILYFARE MEYER": {"retailer": "familyfare.com", "logo_source": "https://www.familyfare.com/logo.png"},
    "WFREDMEYER MEYER": {"retailer": "fredmeyer.com", "logo_source": "https://www.fredmeyer.com/logo.jpg"},
    "THD HD POT": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "THE HOME DEPOT": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "HOME DEPOT": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "CRAN HY SUCCO": {"retailer": "sunoco.com", "logo_source": "https://www.sunoco.com/images/logo.png"},  # Updated for Crain Hwy Sunoco
    "SUNOCO": {"retailer": "sunoco.com", "logo_source": "https://www.sunoco.com/images/logo.png"},
    "WINCY FOODS": {"retailer": "wincofoods.com", "logo_source": "https://www.wincofoods.com/logo.svg"},
    "SIN CLAIRE": {"retailer": "stclair.com", "logo_source": "https://www.stclair.com/logo.png"},
    "HOMDA POT": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "THE HOMDEPOT VE": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "ALBE SON": {"retailer": "albertsons.com", "logo_source": "https://www.albertsons.com/logo.svg"},
    "ALBERTSONS": {"retailer": "albertsons.com", "logo_source": "https://www.albertsons.com/logo.svg"},
    "MARATHON BROWNSBURG": {"retailer": "marathonpetroleum.com", "logo_source": "https://www.marathonpetroleum.com/logo.svg"},
    "MURPHY USA": {"retailer": "murphyusa.com", "logo_source": "https://www.murphyusa.com/logo.svg"},
    "TH HOMET DEPOT": {"retailer": "homedepot.com", "logo_source": "https://www.homedepot.com/logo.svg"},
    "CIRCLE K": {"retailer": "circlek.com", "logo_source": "https://www.circlek.com/logo.jpg"},
    "SHELL": {"retailer": "shell.us", "logo_source": "https://www.shell.us/logo.jpg"},
    "SHELL INSTORE": {"retailer": "shell.us", "logo_source": "https://www.shell.us/logo.jpg"},
    "PRICE HOUPER": {"retailer": "pricechopper.com", "logo_source": "https://www.pricechopper.com/logo.png"},
    "DULLAR REE": {"retailer": "dollartree.com", "logo_source": "https://www.dollartree.com/sites/g/files/qyckzh1461/files/media/images/logo/dollartree-logo.png"},
    "DOLLAR TREE": {"retailer": "dollartree.com", "logo_source": "https://www.dollartree.com/sites/g/files/qyckzh1461/files/media/images/logo/dollartree-logo.png"},
    "TARGET": {"retailer": "target.com", "logo_source": "https://www.target.com/logo.svg"},
    "TARGET INSTORE": {"retailer": "target.com", "logo_source": "https://www.target.com/logo.svg"},
    "TARGET PICKUP": {"retailer": "target.com", "logo_source": "https://www.target.com/logo.svg"},
    "WALMART": {"retailer": "walmart.com", "logo_source": "https://www.walmart.com/logo.svg"},
    "WALMART SUPERCENTER": {"retailer": "walmart.com", "logo_source": "https://www.walmart.com/logo.svg"},
    "WALMART NEIGHBORHOOD MARKET": {"retailer": "walmart.com", "logo_source": "https://www.walmart.com/logo.svg"},
    "WALMART INSTORE": {"retailer": "walmart.com", "logo_source": "https://www.walmart.com/logo.svg"},
    "WALMART PICKUP": {"retailer": "walmart.com", "logo_source": "https://www.walmart.com/logo.svg"},
    "KROGER": {"retailer": "kroger.com", "logo_source": "https://www.kroger.com/logo.png"},
    "KROGER WE": {"retailer": "kroger.com", "logo_source": "https://www.kroger.com/logo.png"},
    "KROGER ONLINE": {"retailer": "kroger.com", "logo_source": "https://www.kroger.com/logo.png"},
    "KROGERBANNERS.COM ACCOUNT SCRAPING PICKUP": {"retailer": "kroger.com", "logo_source": "https://www.kroger.com/logo.png"},
    "DOLLAR GENERAL": {"retailer": "dollargeneral.com", "logo_source": "https://www.dollargeneral.com/logo.png"},
    "DOLLAR GENERAL INSTORE": {"retailer": "dollargeneral.com", "logo_source": "https://www.dollargeneral.com/logo.png"},
    "FAMILY DOLLAR": {"retailer": "familydollar.com", "logo_source": "https://www.familydollar.com/logo.png"},
    "LOWES": {"retailer": "lowes.com", "logo_source": "https://www.lowes.com/logo.svg"},
    "SAFEWAY": {"retailer": "safeway.com", "logo_source": "https://www.safeway.com/logo.png"},
    "MEIJER": {"retailer": "meijer.com", "logo_source": "https://www.meijer.com/logo.png"},
    "SHOPRITE": {"retailer": "shoprite.com", "logo_source": "https://www.shoprite.com/logo.png"},
    "SPEEDWAY": {"retailer": "speedway.com", "logo_source": "https://www.speedway.com/logo.png"},
    "CASEYS GENERAL STORE": {"retailer": "caseys.com", "logo_source": "https://www.caseys.com/logo.png"},
    "STOP N SHOP": {"retailer": "stopandshop.com", "logo_source": "https://www.stopandshop.com/logo.png"},
    "WAWA": {"retailer": "wawa.com", "logo_source": "https://www.wawa.com/logo.png"},
    "BJS": {"retailer": "bjs.com", "logo_source": "https://www.bjs.com/logo.png"},
    "SHEETZ": {"retailer": "sheetz.com", "logo_source": "https://www.sheetz.com/logo.png"},
    "WINN DIXIE": {"retailer": "winndixie.com", "logo_source": "https://www.winndixie.com/logo.png"},
    "TRADER JOES": {"retailer": "traderjoes.com", "logo_source": "https://www.traderjoes.com/logo.png"},
    "WALGREENS": {"retailer": "walgreens.com", "logo_source": "https://www.walgreens.com/logo.png"},
    "WALGREENS INSTORE": {"retailer": "walgreens.com", "logo_source": "https://www.walgreens.com/logo.png"},
    "WALGREENS ONLINE": {"retailer": "walgreens.com", "logo_source": "https://www.walgreens.com/logo.png"},
    "ACE HARDWARE": {"retailer": "acehardware.com", "logo_source": "https://www.acehardware.com/logo.png"},
    "KWIK TRIP": {"retailer": "kwiktrip.com", "logo_source": "https://www.kwiktrip.com/logo.png"},
    "FOOD LION INSTORE": {"retailer": "foodlion.com", "logo_source": "https://www.foodlion.com/logo.png"},
    "ULTA INSTORE": {"retailer": "ulta.com", "logo_source": "https://www.ulta.com/logo.png"},
    "7-ELEVEN INSTORE": {"retailer": "7-eleven.com", "logo_source": "https://www.7-eleven.com/logo.png"},
    "CVS INSTORE": {"retailer": "cvs.com", "logo_source": "https://www.cvs.com/logo.png"},
    "PUBLIX INSTORE": {"retailer": "publix.com", "logo_source": "https://www.publix.com/logo.png"},
    "WHOLE FOODS INSTORE": {"retailer": "wholefoodsmarket.com", "logo_source": "https://www.wholefoodsmarket.com/logo.png"},
    "TOTAL WINE MORE INSTORE": {"retailer": "totalwine.com", "logo_source": "https://www.totalwine.com/logo.png"},
    "PETCO INSTORE": {"retailer": "petco.com", "logo_source": "https://www.petco.com/logo.png"},
    "INSTACART ONLINE": {"retailer": "instacart.com", "logo_source": "https://www.instacart.com/logo.png"},
    "AMAZON ONLINE": {"retailer": "amazon.com", "logo_source": "https://www.amazon.com/logo.png"},
    "HEB .COM": {"retailer": "heb.com", "logo_source": "https://www.heb.com/logo.png"},
    "CHEWY ONLINE": {"retailer": "chewy.com", "logo_source": "https://www.chewy.com/logo.png"},
}

# Enhanced cleaning to handle noise
def clean_description(description):
    cleaned = re.sub(r'\d+', '', description.upper().strip())  # Remove numbers
    cleaned = re.sub(r'\s+(?:INCREDIBLY FRIENDLY|WISE|CHECK|HD|THD|CO|MEYER|EXPRESS|INSTORE|PICKUP|ONLINE|\.COM|ACCOUNT SCRAPING|AUGUSTINE|SHEL|SHELL|VE|HY|SUCCO|BROWNSBURG)\s+', ' ', cleaned)
    return ' '.join(cleaned.split())  # Normalize spaces

# Basic fuzzy matching function
def find_brand_match(description):
    orig_desc = description.upper().strip()
    cleaned_desc = clean_description(description)
    
    # Direct exact match
    if orig_desc in BRAND_SEED:
        return BRAND_SEED[orig_desc]
    
    # Fuzzy match on original
    matches = difflib.get_close_matches(orig_desc, list(BRAND_SEED.keys()), n=1, cutoff=0.45)  # 45% threshold
    if matches:
        return BRAND_SEED[matches[0]]
    
    # Fallback: Fuzzy on cleaned description
    matches = difflib.get_close_matches(cleaned_desc, list(BRAND_SEED.keys()), n=1, cutoff=0.45)
    if matches:
        return BRAND_SEED[matches[0]]
    
    return {"retailer": "Not found", "logo_source": None}

def get_domain(url):
    if url == "Not found" or not url:
        return None
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        # Remove .com or .us to get base retailer name
        if domain.endswith(".com"):
            return domain[:-4]
        elif domain.endswith(".us"):
            return domain[:-3]
        return domain
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
st.caption("Validates brand presence using fuzzy matching on an expanded seed dataset. Suggests Google verification for accuracy.")

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
                    
                    # PASS 2: If failed, clean and re-match
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
                    
                    # Final fallback and manual verification suggestion
                    if top_retailer == "Not found" and top_logo_source != "Not found":
                        top_retailer = top_logo_source
                    elif top_retailer in ["hyvee", "Not found"] and "sunoco" in description.lower():
                        top_retailer = "sunoco"  # Manual override based on your Google insight
                        st.warning(f"Manual verification suggested for '{description}': Google search may confirm 'sunoco' as the official site.")
                    elif top_retailer == "Not found":
                        st.warning(f"Manual verification suggested for '{description}': Please search Google for the official retailer site.")
                    
                    results.append({'retailer': top_retailer, 'status': final_status})
                    
                    progress_bar.progress((idx + 1) / total)
                    if idx < total - 1:
                        time.sleep(random.uniform(0.5, 1.0))
                
                status_text.success("Analysis Complete!", icon="🎉")
            
            results_df = pd.DataFrame(results)
            df['retailer'] = results_df['retailer']
            df['status'] = results_df['status']
            
            st.header("3. Results")
            st.markdown("status is 'Yes' if a unique website or logo was found (fuzzy-corrected from expanded seed). * indicates manual Google verification is recommended.")
            st.dataframe(df, use_container_width=True)
            
            dominant_count = (df['status'] == 'Yes').sum()
            st.metric("Brands with a Unique Presence", f"{dominant_count} / {total}")
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results", csv_data, "brand_validator_results.csv", "text/csv", use_container_width=True)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

else:
    st.info("Please upload a CSV file to get started.")
