import requests
from bs4 import BeautifulSoup

url = "https://example.com/"

# Headers to avoid being blocked by some websites
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Send request to website
response = requests.get(url, headers=headers)

# Parse HTML
soup = BeautifulSoup(response.text, "html.parser")

# Example: get page title
title = soup.find("title")
if title:
    print("Page title:", title.text)
else:
    print("No title found")

# Get all links
links = soup.find_all("a")
print(f"\nFound {len(links)} links:")

for i, a in enumerate(links[:10], 1):  # Show first 10 links
    href = a.get("href")
    text = a.get_text(strip=True)
    if href:
        print(f"{i}. {text[:50]}... -> {href}")

print("Web scraping completed!")
