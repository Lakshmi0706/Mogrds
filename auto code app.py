from googlesearch import search

# List of company names (like your Excel column A)
companies = [
    "Tata Motors",
    "Infosys",
    "Reliance Industries",
    "HDFC Bank"
]

# Loop through each company and fetch its official website
for company in companies:
    query = company + " official website"
    results = search(query, num=1, stop=1, pause=2)
    for website in results:
        print(f"{company}: {website}")
