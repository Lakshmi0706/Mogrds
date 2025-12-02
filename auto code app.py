
import streamlit as st
import pandas as pd
import re
from rapidfuzz import fuzz, process
from io import BytesIO

st.title("Merchant Mapping Tool with Fuzzy Matching (Top 3 Matches)")

uploaded_merchant = st.file_uploader("Upload Merchant List", type=["xlsx"])
uploaded_input = st.file_uploader("Upload Input File", type=["xlsx"])

confidence_threshold = st.slider("Confidence Threshold (%)", 50, 100, 80)

if uploaded_merchant and uploaded_input:
    # Load Merchant List
    merchant_df = pd.read_excel(uploaded_merchant, engine="openpyxl")
    
    # Use the correct column name from your file
    merchant_column = "list"  # This is confirmed from your file
    original_merchants = merchant_df[merchant_column].dropna().astype(str).unique().tolist()

    # Create mapping: UPPERCASE -> Original Name
    merchant_map = {m.upper().strip(): m for m in original_merchants}
    merchant_list = list(merchant_map.keys())  # Uppercase list for matching

    # Load Input File
    input_df = pd.read_excel(uploaded_input, engine="openpyxl")

    if 'Description' not in input_df.columns:
        st.error("Input file must contain a 'Description' column.")
    else:
        # Clean text function
        def clean_text(text):
            text = re.sub(r'[^a-zA-Z0-9 ]', '', str(text))
            return re.sub(r'\s+', ' ', text).strip().upper()

        # Get top matches
        def get_top_matches(text, limit=3):
            matches = process.extract(text, merchant_list, scorer=fuzz.token_sort_ratio, limit=limit)
            # Convert back to original names using merchant_map
            return [(merchant_map[m[0]], round(m[1], 2)) for m in matches]

        # Process data
        output_data = []
        for i, desc in enumerate(input_df['Description'], start=1):
            cleaned_desc = clean_text(desc)
            top_matches = get_top_matches(cleaned_desc)
            top_matches_str = "; ".join([f"{m[0]} ({m[1]}%)" for m in top_matches])
            best_match = top_matches[0][0] if top_matches else "Not Found"
            best_score = top_matches[0][1] if top_matches else 0
            status = "Yes" if best_score >= confidence_threshold else "No"
            output_data.append({
                "S.No": i,
                "Original Description": desc,
                "Top 3 Matches": top_matches_str,
                "Best Match (Merchant Name)": best_match,
                "Confidence Score": f"{best_score}%",
                "Status": status
            })

        output_df = pd.DataFrame(output_data)

        # Display output
        st.write("### Output Preview", output_df)

        # Download button
        output_buffer = BytesIO()
        output_df.to_excel(output_buffer, index=False, engine="openpyxl")
        output_buffer.seek(0)
        st.download_button(
            label="Download Output",
            data=output_buffer,
            file_name="merchant_mapping_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
