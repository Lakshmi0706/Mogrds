import streamlit as st
import pandas as pd
from difflib import get_close_matches

# Predefined lookup for merchant status
merchant_lookup = {
    "THE JERK SHOP": "OK",
    "UNITED SUPER": "OK",
    "CON 3": "Not OK",
    "ALBERTSONS S": "OK",
    "613 FRESH DELI GROCERY": "Not OK",
    "7ELEVN": "OK",
    "WINNDIXIE": "OK"
}

# Streamlit UI
st.title("Merchant Website Status Checker")
st.write("Enter merchant names below to check if they have a unique website.")

# Text area for user input
user_input = st.text_area("Enter merchant names (one per line):")

if user_input:
    merchant_list = [name.strip() for name in user_input.split("\n") if name.strip()]
    results = []
    for merchant in merchant_list:
        # Try fuzzy matching
        match = get_close_matches(merchant.upper(), merchant_lookup.keys(), n=1, cutoff=0.6)
        if match:
            status = merchant_lookup[match[0]]
        else:
            status = "Not OK"
        results.append({"Merchant Name": merchant, "Status": status})

    df = pd.DataFrame(results)
    st.subheader("Results")
    st.dataframe(df, use_container_width=True)
