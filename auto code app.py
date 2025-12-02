import pandas as pd
import re
from difflib import SequenceMatcher
 
# === Load Merchant List ===
merchant_df = pd.read_excel("merchant list.xlsx", sheet_name="fetch", engine="openpyxl")
merchant_list = merchant_df.iloc[:, 0].dropna().astype(str).unique().tolist()
merchant_list = [m.upper().strip() for m in merchant_list]
 
# === Load Input File ===
# Replace 'input.xlsx' with your actual input file name
input_df = pd.read_excel("input.xlsx", engine="openpyxl")
 
# Validate column
if 'Description' not in input_df.columns:
    raise ValueError("Input file must contain a 'Description' column.")
 
# === Clean Text Function ===
def clean_text(text):
    text = re.sub(r'[^a-zA-Z0-9 ]', '', str(text))
    return re.sub(r'\s+', ' ', text).strip().upper()
 
# === Matching Function ===
def get_best_match(text):
    words = text.split()
    best_match = None
    best_score = 0.0
    for merchant in merchant_list:
        merchant_words = merchant.split()
        match_count = sum(1 for w in words if w in merchant_words)
        ratio = SequenceMatcher(None, text, merchant).ratio()
        score = max(ratio, match_count / len(merchant_words))
        if score > best_score:
            best_score = score
            best_match = merchant
    return best_match, best_score
 
# === Process Data ===
output_data = []
for i, desc in enumerate(input_df['Description'], start=1):
    cleaned_desc = clean_text(desc)
    merchant_hint, confidence = get_best_match(cleaned_desc)
    confidence_percent = round(confidence * 100, 2)
    status = "Yes" if merchant_hint and confidence >= 0.8 else "No"
    output_data.append({
        "S.No": i,
        "Original Description": desc,
        "Confidence Score": f"{confidence_percent}%",
        "Merchant List Match": merchant_hint if merchant_hint else "Not Found",
        "Status": status
    })
 
# === Create Output DataFrame ===
output_df = pd.DataFrame(output_data)
 
# === Save Output ===
output_df.to_excel("merchant_mapping_output.xlsx", index=False, engine="openpyxl")
print("Output file generated: merchant_mapping_output.xlsx")
