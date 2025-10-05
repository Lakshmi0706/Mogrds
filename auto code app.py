import pandas as pd
from difflib import get_close_matches
import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
from tkinter import Tk
from tkinter.filedialog import askopenfilename

# ------------------------------
# Load or initialize known retailers
# ------------------------------
KNOWN_FILE = "known_retailers.json"

if os.path.exists(KNOWN_FILE):
    with open(KNOWN_FILE, "r") as f:
        KNOWN_RETAILERS = json.load(f)
else:
    KNOWN_RETAILERS = [
        "Walmart", "Target", "Best Buy", "Costco", "Sam's Club", "Dollar Tree", 
        "Dollar General", "Family Dollar", "Home Depot", "Lowe's", "Walgreens",
        "CVS", "Kroger", "Publix", "Aldi", "Trader Joe's", "Whole Foods", 
        "Macy's", "Kohl's", "JCPenney", "Nordstrom", "Sears", "Amazon",
        "IKEA", "Nike", "Adidas", "Apple", "Microsoft Store"
    ]

# ------------------------------
# Search DuckDuckGo for retailer name
# ------------------------------
def search_duckduckgo(query):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://duckduckgo.com/html/?q={query}+official+site"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", {"class": "result__a"}, href=True)
    websites = []
    for link in links:
        href = unquote(link["href"])
        if ".com/us" in href.lower():  # Only consider .com/us
            websites.append(href.split('?')[0])
    return list(set(websites))

# ------------------------------
# Clean retailer name using fuzzy match or DuckDuckGo
# ------------------------------
def clean_retailer_name(input_name):
    if not isinstance(input_name, str) or not input_name.strip():
        return None
    name = input_name.strip().title()
    matches = get_close_matches(name, KNOWN_RETAILERS, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    else:
        print(f"Searching online for '{input_name}'...")
        found_name = search_duckduckgo(input_name)
        if found_name:
            KNOWN_RETAILERS.append(found_name[0].title())
            return found_name[0].title()
        else:
            return None

# ------------------------------
# Process input file and create outputs
# ------------------------------
def process_file(input_file):
    # Detect file type
    if input_file.lower().endswith(".csv"):
        df = pd.read_csv(input_file, header=None, names=["Original_Name"])
    elif input_file.lower().endswith((".xls", ".xlsx")):
        df = pd.read_excel(input_file, header=None, names=["Original_Name"])
    else:
        print("Unsupported file type. Please provide a CSV or Excel file.")
        return
    
    df["Corrected_Name"] = df["Original_Name"].apply(clean_retailer_name)
    
    primary_list = []
    secondary_list = []

    for _, row in df.iterrows():
        original_name = row["Original_Name"]
        corrected_name = row["Corrected_Name"]

        if not corrected_name:
            secondary_list.append({"Original_Name": original_name, "Corrected_Name": None, "Websites": []})
            continue

        websites = search_duckduckgo(corrected_name)
        if len(websites) == 1:
            primary_list.append({"Original_Name": original_name, "Corrected_Name": corrected_name, "Website": websites[0]})
        else:
            secondary_list.append({"Original_Name": original_name, "Corrected_Name": corrected_name, "Websites": websites})

    # Save CSVs
    pd.DataFrame(primary_list).to_csv("primary_retailers.csv", index=False)
    pd.DataFrame(secondary_list).to_csv("secondary_retailers.csv", index=False)
    print("✅ Saved primary_retailers.csv and secondary_retailers.csv")

    # Save updated known retailers
    with open(KNOWN_FILE, "w") as f:
        json.dump(KNOWN_RETAILERS, f, indent=2)
    print("✅ Updated known retailers saved to known_retailers.json")

# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    Tk().withdraw()
    print("Please select the CSV or Excel file containing retailer names...")
    input_file = askopenfilename(filetypes=[("CSV and Excel files", "*.csv *.xls *.xlsx")])
    if not input_file:
        print("No file selected. Exiting.")
        exit()
    process_file(input_file)
