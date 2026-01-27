#!/usr/bin/env python3
"""Test script to demonstrate scraper functionality"""

import requests
from bs4 import BeautifulSoup

# Test the breed listing page
base_url = "https://www.royalkennelclub.com/search/breeds-a-to-z"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

print("="*60)
print("Testing Royal Kennel Club Breed Scraper")
print("="*60)
print(f"\nFetching: {base_url}")

try:
    response = requests.get(base_url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    
    print(f"✓ Page fetched successfully (Status: {response.status_code})")
    print(f"✓ Page size: {len(response.text)} characters")
    
    # Find all links
    all_links = soup.find_all("a", href=True)
    print(f"\n✓ Total links found on page: {len(all_links)}")
    
    # Search for breed links
    breed_patterns = [
        ("/breed/", "Pattern: /breed/"),
        ("/breeds/", "Pattern: /breeds/"),
        ("/dog-breeds/", "Pattern: /dog-breeds/"),
    ]
    
    print("\nSearching for breed links with different patterns:")
    print("-" * 60)
    
    breed_links = []
    for pattern, label in breed_patterns:
        found = []
        for link in all_links:
            href = link.get("href")
            if pattern in href.lower():
                found.append(href)
        
        if found:
            print(f"\n{label}")
            print(f"Found: {len(found)} links")
            breed_links.extend(found)
            # Show first 5 examples
            for i, href in enumerate(found[:5]):
                print(f"  {i+1}. {href[:80]}")
            if len(found) > 5:
                print(f"  ... and {len(found)-5} more")
    
    # Deduplicate
    unique_breeds = set(breed_links)
    print(f"\n{'='*60}")
    print(f"Total unique breed links found: {len(unique_breeds)}")
    print(f"{'='*60}")
    
    if unique_breeds:
        print("\nSample breed URLs:")
        for i, url in enumerate(list(unique_breeds)[:10]):
            full_url = url if url.startswith("http") else f"https://www.royalkennelclub.com{url}"
            print(f"  {i+1}. {full_url}")
    else:
        print("\n⚠ No breed links found. The website structure may have changed.")
        print("\nTrying alternative method - looking for breed-related divs...")
        breed_divs = soup.find_all("div", class_=lambda x: x and "breed" in x.lower() if x else False)
        print(f"Found {len(breed_divs)} breed-related divs")
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test complete!")
print("="*60)
