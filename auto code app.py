import streamlit as st
import pandas as pd
import difflib
import time
import random
import re
from fuzzywuzzy import fuzz  # For phonetic and partial ratio matching

# Embedded requirements.txt for reference (create this file separately in the GitHub repository)
# requirements.txt content:
# streamlit==1.39.0
# pandas==2.2.3
# fuzzywuzzy==0.18.0

# Updated seed dataset with more variations
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

# Enhanced cleaning with dynamic normalization
def clean_description(description):
    # Preserve retailer-related patterns and normalize
    cleaned = re.sub(r'[^a-zA-Z0-9\s&]', ' ', description.upper().strip())  # Keep numbers and & for cases like 1stop&shop
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize multiple spaces
    # Remove common noise terms dynamically
    noise_terms = r'\s+(?:INCREDIBLY FRIENDLY|WISE|CHECK|HD|THD|CO|MEYER|EXPRESS|INSTORE|PICKUP|ONLINE|\.COM|ACCOUNT SCRAPING|AUGUSTINE|SHEL|SHELL|VE|HY|SUCCO|BROWNSBURG)\s+'
    cleaned = re.sub(noise_terms, ' ', cleaned)
    # Attempt to split and recombine key terms
    words = cleaned.split()
    if len(words) > 1:
        cleaned = ' '.join(w for w in words if len(w) > 2 or w in ['N', '&'])  # Filter short words except connectors
    return cleaned.strip()

# Convert domain to retailer name
def domain_to_retailer_name(domain):
    if not domain or domain == "Not found":
        return "Not found"
    name = domain.replace("www.", "").replace(".com", "").replace(".us", "").replace("-", " ")
    return ' '.join(word.capitalize() for word in name.split())

# Advanced dynamic fuzzy match
def find_brand_match(description):
    orig_desc = description.upper().strip()
    cleaned_desc = clean_description(description)
    
    # Pass 1: Exact match on original or cleaned description
    if orig_desc in BRAND_SEED:
        return BRAND_SEED[orig_desc]["retailer"], domain_to_retailer_name(BRAND_SEED[orig_desc]["retailer"])
    if cleaned_desc in BRAND_SEED:
        return BRAND_SEED[cleaned_desc]["retailer"], domain_to_retailer_name(BRAND_SEED[cleaned_desc]["retailer"])
    
    # Pass 2: Fuzzy match with very loose cutoff
    seed_keys = list(BRAND_SEED.keys())
    matches = difflib.get_close_matches(cleaned_desc, seed_keys, n=5, cutoff=0.25)  # Very loose cutoff
    if matches:
        best_match = matches[0]
        return BRAND_SEED[best_match]["retailer"], domain_to_retailer_name(BRAND_SEED[best_match]["retailer"])
    
    # Pass 3: Word-by-word fuzzy matching with phonetic similarity
    words = cleaned_desc.split()
    for word in words:
        for seed_key in seed_keys:
            key_words = seed_key.split()
            for key_word in key_words:
                if (fuzz.partial_ratio(word, key_word) > 60 or
                    fuzz.token_set_ratio(word, key_word) > 60 or
                    fuzz.phonetic(word, key_word)):  # Phonetic matching
                    return BRAND_SEED[seed_key]["retailer"], domain_to_retailer_name(BRAND_SEED[seed_key]["retailer"])
    
    # Pass 4: Combination of words if no single match
    for i in range(len(words), 0, -1):
        partial = ' '.join(words[:i])
        matches = difflib.get_close_matches(partial, seed_keys, n=1, cutoff=0.3)
        if matches:
            return BRAND_SEED[matches[0]]["retailer"], domain_to_retailer_name(BRAND_SEED[matches[0]]["retailer"])
    
    return "Not found", "Not found"

# Check if description is vague
def is_vague_description(description):
    cleaned = clean_description(description)
    return len(cleaned) < 3 or not any(c.isalpha() for c in cleaned)

# --- Streamlit App UI ---

st.set_page_config(page_title="Intelligent Brand Validator", page_icon="🧠", layout="centered")

st.title("🧠 Intelligent Brand Validator")
st.caption("Validates retailer names using advanced dynamic fuzzy matching (no API required).")

st.header("1. Upload Your File")
uploaded_file = st.file_uploader("Your CSV must have 'S No' and 'description' columns.", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        if 'S No' not in df.columns or 'description' not in df.columns:
            st.error("Upload failed! The CSV must contain 'S No' and 'description' columns.", icon="🚨")
            st.stop()
        
        st.success(f"File uploaded! Found {len(df)} descriptions to analyze.")
        
        st.header("2. Start Analysis")
        start_btn = st.button("Validate Retailer Presence", type="primary", use_container_width=True)
        
        if start_btn:
            with st.spinner("Analyzing... This may take a moment."):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total = len(df)
                for idx, row in df.iterrows():
                    description = str(row['description'])
                    s_no = row['S No']
                    status_text.text(f"Processing {idx + 1}/{total}: {description[:50]}...")
                    
                    # Check for vague description
                    if is_vague_description(description):
                        results.append({
                            'S No': s_no,
                            'description': description,
                            'retailer': 'Not found',
                            'status': 'Not Okay'
                        })
                        progress_bar.progress((idx + 1) / total)
                        time.sleep(random.uniform(0.2, 0.5))
                        continue
                    
                    # Advanced matching
                    retailer_domain, retailer_name = find_brand_match(description)
                    status = "Okay" if retailer_domain != "Not found" else "Not Okay"
                    
                    results.append({
                        'S No': s_no,
                        'description': description,
                        'retailer': retailer_name,
                        'status': status
                    })
                    
                    progress_bar.progress((idx + 1) / total)
                    time.sleep(random.uniform(0.2, 0.5))
                
                status_text.success("Analysis Complete!", icon="🎉")
            
            results_df = pd.DataFrame(results)
            df = results_df[['S No', 'description', 'retailer', 'status']]
            
            st.header("3. Results")
            st.markdown("status is 'Okay' if a retailer is matched via advanced fuzzy matching. 'Not Okay' for vague or unmatched descriptions.")
            st.dataframe(df, use_container_width=True)
            
            okay_count = (df['status'] == 'Okay').sum()
            st.metric("Descriptions with Valid Retailer", f"{okay_count} / {total}")
            
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Results", csv_data, "retailer_validator_results.csv", "text/csv", use_container_width=True)
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}", icon="🔥")

else:
    st.info("Please upload a CSV file with 'S No' and 'description' columns to get started.")
