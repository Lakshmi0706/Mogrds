import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from collections import Counter
import time
import random

def search_google(description, api_key):
    """Search for product retailers using natural language query"""
    # Make it sound like a human search
    query = f"where to buy {description} in USA"
    
    params = {
        "q": query,
        "engine": "google",
        "gl": "us",
        "hl": "en",
        "api_key": api_key,
        "num": 10
    }
    
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if "error" in data:
            st.warning(f"Oops! API returned an error: {data['error']}")
            return []
        
        links = [result['link'] for result in data.get("organic_results", [])]
        return links
    
    except requests.exceptions.RequestException as e:
        st.error(f"Couldn't connect to search API: {e}")
        return []

def get_retailer_domains(links):
    """Extract retailer domains from search results"""
    domains = []
    
    # Common sites we want to skip (not actual retailers)
    skip_these = [
        "amazon", "ebay", "walmart", "wikipedia", "youtube", 
        "facebook", "pinterest", "twitter", "instagram", 
        "reddit", "quora", "yelp", "google"
    ]
    
    for link in links:
        domain = urlparse(link).netloc.replace("www.", "")
        
        if domain and not any(skip in domain.lower() for skip in skip_these):
            domains.append(domain)
    
    return domains

def find_top_retailer(domains):
    """Determine the most common retailer and if it's unique"""
    if not domains:
        return "Not found", "No"
    
    domain_counts = Counter(domains)
    most_common_retailer = domain_counts.most_common(1)[0][0]
    
    # It's unique if this retailer dominates the results
    is_unique = "Yes" if len(domain_counts) == 1 else "No"
    
    return most_common_retailer, is_unique

# Page setup
st.set_page_config(page_title="Retailer Finder", page_icon="🛒", layout="wide")

st.title("🛒 Find Unique Retailers for Your Products")
st.write("Upload your product list and I'll help you find which retailers sell them exclusively in the USA")

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Your SerpAPI Key", type="password")
    st.caption("Don't have one? Get it free at [serpapi.com](https://serpapi.com)")
    
    st.divider()
    
    st.markdown("""
    ### How it works
    - Upload a CSV with product descriptions
    - I'll search for each product
    - Find which retailers sell them
    - Tell you if there's a unique/exclusive retailer
    
    *Free tier:* 100 searches per month
    """)

# Main content area
uploaded_file = st.file_uploader(
    "Drop your CSV file here", 
    type=["csv"],
    help="Make sure your file has a column named 'description'"
)

if uploaded_file and api_key:
    try:
        df = pd.read_csv(uploaded_file)
        
        if 'description' not in df.columns:
            st.error("🚫 I need a 'description' column in your CSV file!")
            st.stop()
        
        # Show preview
        st.success(f"Great! I found {len(df)} products to check")
        
        with st.expander("👀 Preview your data"):
            st.dataframe(df.head(), use_container_width=True)
        
        # Warning about API usage
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"This will use around {len(df)} of your monthly API searches")
        with col2:
            start_btn = st.button("🚀 Let's Go!", type="primary", use_container_width=True)
        
        if start_btn:
            retailers = []
            statuses = []
            
            progress = st.progress(0)
            status_msg = st.empty()
            
            for idx, description in enumerate(df['description'], 1):
                # Show what we're working on
                status_msg.info(f"🔍 Searching for: *{description[:60]}{'...' if len(description) > 60 else ''}*")
                
                # Do the search
                search_results = search_google(description, api_key)
                retailer_domains = get_retailer_domains(search_results)
                top_retailer, unique_status = find_top_retailer(retailer_domains)
                
                retailers.append(top_retailer)
                statuses.append(unique_status)
                
                # Update progress
                progress.progress(idx / len(df))
                
                # Human-like delay (random between 1-2 seconds)
                if idx < len(df):
                    time.sleep(random.uniform(1.0, 2.0))
            
            status_msg.success("✅ All done! Here are your results:")
            
            # Build results
            df['Retailer'] = retailers
            df['Exclusive?'] = statuses
            
            # Show results with nice formatting
            st.dataframe(
                df.style.map(
                    lambda x: 'background-color: #d4edda' if x == 'Yes' else '', 
                    subset=['Exclusive?']
                ),
                use_container_width=True
            )
            
            # Stats
            unique_products = sum(1 for s in statuses if s == "Yes")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Products", len(df))
            with col2:
                st.metric("Exclusive Retailers", unique_products)
            with col3:
                st.metric("Multiple Retailers", len(df) - unique_products)
            
            # Download
            st.divider()
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Results as CSV",
                csv_data,
                "retailer_analysis.csv",
                "text/csv",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"Something went wrong: {e}")

elif not uploaded_file:
    st.info("👆 Upload a CSV file to get started")
    
    # Sample data format
    with st.expander("📋 What should my CSV look like?"):
        sample_df = pd.DataFrame({
            'description': [
                'Sony WH-1000XM5 wireless headphones',
                'Nike Air Max 90 sneakers',
                'KitchenAid stand mixer'
            ]
        })
        st.dataframe(sample_df, use_container_width=True)
        st.caption("Just have a 'description' column with your product names")

elif not api_key:
    st.warning("⚠️ Don't forget to add your SerpAPI key in the sidebar!")
