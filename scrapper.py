Kendall
 — 
7:08 PM
pip install requests beautifulsoup4
links = soup.find_all("a")

for a in links:
    print(a.get("href"))
headers = {
    "User-Agent": "Mozilla/5.0"
}
response = requests.get(url, headers=headers)
pip install requests beautifulsoup4

import requests
from bs4 import BeautifulSoup

url = "https://example.com/"

#Send request to website
response = requests.get(url)

#Parse HTML
soup = BeautifulSoup(response.text, "html.parser")

#Example: get page title
title = soup.find("title").text

print("Page title:", title)

links = soup.find_all("a")

for a in links:
    print(a.get("href"))

headers = {
    "User-Agent": "Mozilla/5.0"
}
response = requests.get(url, headers=headers)
