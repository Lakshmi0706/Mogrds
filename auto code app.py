
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
    # Load Merchant List (no header; merchant names are in the first column)
    merchant_df = pd.read_excel(uploaded_merchant, engine="openpyxl", header=None)
    merchant_df.columns = ["Merchant"]  # Rename first column
    original_merchants = (
        merchant_df["Merchant"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    # Utility to clean text consistently
    def clean_text(text: str) -> str:
        text = re.sub(r"[^a-zA-Z0-9 ]", "", str(text))
        return re.sub(r"\s+", " ", text).strip().upper()

    # Precompute cleaned merchant list and a map back to original
    cleaned_merchants = [clean_text(m) for m in original_merchants]
    merchant_map = {cm: orig for cm, orig in zip(cleaned_merchants, original_merchants)}

    # Load Input File (must have 'Description' column)
    input_df = pd.read_excel(uploaded_input, engine="openpyxl")

    if "Description" not in input_df.columns:
        st.error("Input file must contain a 'Description' column.")
    else:
        # Get top matches from RapidFuzz
        def get_top_matches(text: str, limit: int = 3):
            # Using token_sort_ratio to be robust to word order
            matches = process.extract(
                text,
                cleaned_merchants,
                scorer=fuzz.token_sort_ratio,
                limit=limit,
            )
            # Convert cleaned back to original names using merchant_map
            # matches is a list of tuples: (candidate, score, index)
            return [(merchant_map[m[0]], round(m[1], 2)) for m in matches] if matches else []

        output_rows = []
        progress = st.progress(0)
        total = len(input_df)

        for i, desc in enumerate(input_df["Description"], start=1):
            cleaned_desc = clean_text(desc)
            top_matches = get_top_matches(cleaned_desc)

            if top_matches:
                top_matches_str = "; ".join([f"{m[0]} ({m[1]}%)" for m in top_matches])
                best_match = top_matches[0][0]
                best_score = top_matches[0][1]
            else:
                top_matches_str = ""
                best_match = "Not Found"
                best_score = 0

            status = "Yes" if best_score >= confidence_threshold else "No"

            output_rows.append(
                {
                    "S.No": i,
                    "Original Description": desc,
                    "Top 3 Matches": top_matches_str,
                    "Best Match (Merchant Name)": best_match,
                    "Confidence Score": f"{best_score}%",
                    "Status": status,
                }
            )

            progress.progress(i / total)

        output_df = pd.DataFrame(output_rows)

        # Display output
        st.write("### Output Preview")
        st.dataframe(output_df, use_container_width=True)

        # Prepare download
        output_buffer = BytesIO()
        with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
            output_df.to_excel(writer, index=False, sheet_name="Fuzzy Matches")
        output_buffer.seek(0)

        st.download_button(
            label="Download Results (.xlsx            label="Download Results (.xlsx)",
            data=output_buffer,
            file_name="merchant_fuzzy_mapping.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
