import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

st.title("Retailer Finder (CSV Upload + Results Export)")

# File uploader for CSV
uploaded_file = st.file_uploader("Upload Retailers CSV", type=["csv"])

# Session state to store results
if "results" not in st.session_state:
    st.session_state["results"] = []

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df["Retailer Name"] = df["Retailer Name"].str.upper().str.strip()
    retailer_data = dict(zip(df["Retailer Name"], df["URL"]))

    st.success(f"✅ Loaded {len(retailer_data)} retailers from CSV")

    retailer_desc = st.text_input("Enter retailer description", "")

    if st.button("Search"):
        if retailer_desc.strip() == "":
            st.warning("⚠️ Please enter a retailer description")
        else:
            query = retailer_desc.strip().upper()

            if query in retailer_data:
                url = retailer_data[query]

                try:
                    response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        logo = soup.find("img", {"src": re.compile("logo", re.I)})

                        if logo:
                            logo_url = logo["src"]
                            if logo_url.startswith("//"):
                                logo_url = "https:" + logo_url
                            elif logo_url.startswith("/"):
                                logo_url = url.rstrip("/") + logo_url

                            st.image(logo_url, caption=f"{query} Logo")
                            st.success("Status: Yes ✅")
                            st.write(f"Retailer URL: {url}")
                            status = "Yes ✅"
                        else:
                            st.error("Status: No ❌ (Logo not found)")
                            st.write(f"Retailer URL: {url}")
                            status = "No ❌ (Logo not found)"
                            logo_url = None
                    else:
                        st.error(f"⚠️ Failed to access site. Status code: {response.status_code}")
                        status = "Error"
                        logo_url = None
                except Exception as e:
                    st.error(f"❌ Error fetching data: {str(e)}")
                    status = "Error"
                    logo_url = None

                # Save result in session
                st.session_state["results"].append({
                    "Retailer Name": query,
                    "Retailer URL": url,
                    "Status": status,
                    "Logo URL": logo_url
                })
            else:
                st.error("❌ Retailer not found in uploaded CSV")

    # Show results table
    if st.session_state["results"]:
        results_df = pd.DataFrame(st.session_state["results"])
        st.subheader("Results so far:")
        st.dataframe(results_df)

        # Download buttons
        csv = results_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download Results as CSV", data=csv, file_name="retailer_results.csv", mime="text/csv")

        excel = results_df.to_excel("retailer_results.xlsx", index=False)
        with open("retailer_results.xlsx", "rb") as f:
            st.download_button("⬇️ Download Results as Excel", data=f, file_name="retailer_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("ℹ️ Please upload a CSV file to continue.")
