import streamlit as st
import pandas as pd
from urllib.parse import urlparse
import requests
from collections import Counter
import time
import random

# -------------------------------
# Search Google using SerpAPI
# -------------------------------
def search_google(description, api_key):
    # More specific query for better results
    query = f"buy {description} online site USA"
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
            st.warning(f"API Error: {data['error']}")
            return []
        return [result['link'] for result in data.get("organic_results", [])]
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return []

# -------------------------------
# Extract retailer domains
# -------------------------------
def get_retailer_domains(links):
    skip_these = [
        "amazon", "ebay", "walmart", "wikipedia", "youtube", 
        "facebook", "pinterest", "twitter", "instagram", 
        "reddit", "quora", "yelp", "google", "mapquest", "doordash",
        "linkedin", "tripadvisor", "target", "bestbuy"
    ]
    domains = []
    for link in links:
        domain = urlparse(link).netloc.replace("www.", "")
        if domain and not any(skip in domain.lower() for skip in skip_these):
            # Check if domain looks like a retailer
            if any(keyword in domain.lower() for keyword in ["shop", "store", "mart", "buy", "outlet"]):
                domains.append(domain)
    return domains
