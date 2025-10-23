import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from collections import Counter
import difflib  # For fuzzy matching
import time
import re  # For cleaning
from googlesearch import search  # --- IMPORT FOR GOOGLE SEARCH ---

# BRAND_SEED is used to find a "clean" search query
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
    "CRAN HY SUCCO": {"retailer": "hyvee.com", "logo_source": "https://www.hyvee.com/logo.svg"},
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

# Fuzzy matching function to find a CLEAN search query
def find_brand_match_key(description):
    """
    Tries to find a match in BRAND_SEED.
    Returns the MATCHED KEY (e.g., "COSTCO") if found, otherwise None.
    This provides a clean search term for Google.
    """
    orig_desc = description.upper().strip()
    cleaned_desc = clean_description(description)
    
    # Direct exact match
    if orig_desc in BRAND_SEED:
        return orig_desc # Return the matched key
    
    # Fuzzy match on original
    matches = difflib.get_close_matches(orig_desc, list(BRAND_SEED.keys()), n=1, cutoff=0.45)  # 45% threshold
    if matches:
        return matches[0] # Return the matched key
    
    # Fallback: Fuzzy on cleaned description
    matches = difflib.get_close_matches(cleaned_desc, list(BRAND_SEED.keys()), n=1, cutoff=0.45)
    if matches:
        return matches[0] # Return the matched key
    
    return None # No match found

def get_domain(url):
    if not url:
        return None
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return None

def get_clean_domains(links_or_sources):
    """Extract and clean domains, filtering out non-retail sites."""
    domains = []
    # This list is crucial to filter out noise
    skip_these = [
        "facebook", "instagram", "twitter", "linkedin", "youtube", "reddit", "tiktok",
        "wikipedia", "forbes", "bloomberg", "cnn", "wsj", "nytimes", "yelp",
        "tripadvisor", "mapquest", "google", "apple", "microsoft", "foursquare"
    ]
    for link in links_or_sources:
        domain = get_domain(link)
        if domain and not any(skip in domain.lower() for skip in skip_these):
            domains.append(domain)
    return domains

def analyze_domain_uniqueness(domains):
    """Determines the top domain and if it's a unique, clear winner."""
    if not domains:
        return "Not found", "No"
    
    domain_counts = Counter(domains)
    most_common_list = domain_counts.most_common(2)
    top_domain, top_count = most_common_list[0]
    
    is_dominant = "No"
    
    # Check 1: Is there only one unique domain found in the results?
    if len(most_common_list) == 1 and top_count > 0:
        is_dominant = "Yes"
    # Check 2: Is the top domain strictly more common than the second place?
    elif len(most_common_list) > 1 and top_count > most_common_list[1][1]:
        is_dominant = "Yes"
        
    return top_domain, is_dominant

# --- Streamlit App UI ---

st.set_page_config(page_title="Intelligent Brand Validator", page_icon="🧠", layout="centered")

st.title("🧠 Intelligent Brand Validator")
st.caption("Validates brand presence using Google Search, aided by the seed dataset.")

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
        st.warning("This process queries Google live and will be slow to avoid IP blocks.", icon="⏳")
        start_btn = st.button("Validate Brand Presence", type="primary", use_container_width=True)
        
        if start_btn:
            with st.spinner("Analyzing... This will take time as it queries Google live."):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total = len(df)
                for idx, row in df.iterrows():
                    description = str(row['description'])
                    
                    # --- 1. GET SEARCH QUERY ---
                    # Use fuzzy match on BRAND_SEED to get a cleaner search term
                    matched_key = find_brand_match_key(description)
                    
                    if matched_key:
                        search_query = matched_key  # e.g., "COSTCO"
                    else:
                        search_query = clean_description(description) # e.g., "CRAN HY SUCCO"
                    
                    status_text.text(f"Processing {idx + 1}/{total}: Searching for '{search_query}'...")
                    
                    # --- 2. PERFORM GOOGLE SEARCH ---
                    try:
                        # Get top 10 results. pause=2.0 to avoid IP blocks.
                        search_results_links = list(search(search_query, tld="com", num=10, stop=10, pause=2.0))
                    except Exception as e:
                        st.warning(f"Search failed for '{search_query}' (possible rate-limiting): {e}. Skipping.")
                        search_results_links = []
                        time.sleep(5)  # Take a break if we get an error

                    # --- 3. ANALYZE RESULTS ---
                    # Clean the domains, removing social media, news, etc.
                    web_domains = get_clean_domains(search_results_links)
                    
                    # Find the most dominant, unique domain
                    top_retailer, web_status = analyze_domain_uniqueness(web_domains) # web_status is "Yes" or "No"

                    # --- 4. FORMAT OUTPUT ---
                    final_status = "Okay" if web_status == "Yes" else "Not Okay"
                    
                    results.append({'retailer': top_retailer, 'status': final_status})
                    progress_bar.progress((idx + 1) / total)
                
                status_text.success("Analysis Complete!", icon="🎉")
            
            results_df = pd.DataFrame(results)
            df['retailer'] = results_df['retailer']
            df['status'] = results_df['status']
            
            st.header("3. Results")
            st.markdown("status is 'Okay' if a unique website was found in Google Search (excluding social media, news, etc.).")
            st.dataframe(df, use_container_width=True)
            
            dominant_count = (df['status'] == 'Okay').sum()
            st.metric("Brands with a Unique Web Presence (Status 'Okay')", f"{dominant_count} / {total}")
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results", csv_data, "brand_validator_results.csv", "text/csv", use_container_width=True)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

else:
    st.info("Please upload a CSV file to get started.")
