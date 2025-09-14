import pandas as pd
from duckduckgo_search import DDGS

# Load retailer names from the Excel file
retailer_df = pd.read_excel("retailer.xlsx", engine="openpyxl")
retailer_names = retailer_df.iloc[:, 0].dropna().unique()

# Function to search for merchant name using DuckDuckGo
def get_merchant_name(retailer_name):
    query = f"{retailer_name} USA official site"
    with DDGS() as ddgs:
        results = [r for r in ddgs.text(query, max_results=10)]
    for r in results:
        title = r.get("title", "")
        url = r.get("href", "")
        if any(bad in url for bad in [
            "facebook.com", "instagram.com", "wikipedia.org", 
            "linkedin.com", "yelp.com", "twitter.com", "pinterest.com"
        ]):
            continue
        return title
    return "Not Found"

# Perform search and compile results
results = []
for name in retailer_names:
    merchant = get_merchant_name(name)
    results.append({
        "Retailer Name": name,
        "Merchant Name": merchant
    })

# Create DataFrame and save to CSV
results_df = pd.DataFrame(results)
results_df.to_csv("retailer_merchant_mapping.csv", index=False)

print("Merchant name extraction completed and saved to 'retailer_merchant_mapping.csv'.")

