import requests
from bs4 import BeautifulSoup
import time
import json

def scrape_dog_breeds_rkc(base_url="https://www.royalkennelclub.com/search/breeds-a-to-z"):
    """
    Scrape dog breed information from Royal Kennel Club breeds A to Z page.
    Returns a list of breed documents for the RAG pipeline.
    Focuses exclusively on dog breeds from Royal Kennel Club.
    """
    from haystack import Document
    
    documents = []
    visited_urls = set()
    
    # Headers to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    def scrape_breed_page(url):
        """Scrape individual breed page"""
        if url in visited_urls:
            return
        
        visited_urls.add(url)
        
        try:
            print(f"Scraping: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Get breed name from title or h1
            title_tag = soup.find("h1")
            breed_name = title_tag.get_text(strip=True) if title_tag else "Unknown Breed"
            
            # Get main content - try different selectors for Royal Kennel Club
            content_text = ""
            
            # Try to find main content area
            main_content = soup.find("main") or soup.find("article") or soup.find("div", class_=lambda x: x and ("content" in x.lower() or "main" in x.lower() or "breed" in x.lower()))
            
            if main_content:
                # Remove script, style, and navigation elements
                for element in main_content(["script", "style", "nav", "footer", "header"]):
                    element.decompose()
                
                # Get all paragraphs and text content
                paragraphs = main_content.find_all(["p", "div"], class_=lambda x: x and "text" in x.lower() if x else False)
                if not paragraphs:
                    paragraphs = main_content.find_all("p")
                
                text_parts = []
                for p in paragraphs[:15]:  # First 15 paragraphs/text blocks
                    text = p.get_text(strip=True)
                    if len(text) > 30:  # Only include substantial text
                        text_parts.append(text)
                
                content_text = "\n\n".join(text_parts)
            
            # If we got meaningful content, create a document
            if content_text.strip() and len(content_text) > 100:
                doc = Document(
                    content=content_text,
                    meta={
                        "title": breed_name,
                        "url": url,
                        "source": "Royal Kennel Club"
                    }
                )
                documents.append(doc)
                print(f"  ✓ Added: {breed_name}")
            else:
                print(f"  ⚠ Skipped (insufficient content): {breed_name}")
            
        except Exception as e:
            print(f"  ✗ Error scraping {url}: {str(e)}")
    
    # Scrape the main breeds listing page
    try:
        print(f"Fetching breeds list from: {base_url}")
        response = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all breed links - look for various patterns
        breed_links = []
        
        # Try multiple patterns to find breed links
        patterns = [
            lambda x: x and ("/breed/" in x.lower()),
            lambda x: x and ("/breeds/" in x.lower()),
            lambda x: x and ("/dog-breeds/" in x.lower()),
        ]
        
        all_links = soup.find_all("a", href=True)
        
        for link in all_links:
            href = link.get("href")
            text = link.get_text(strip=True)
            
            # Check if this matches any breed pattern
            for pattern in patterns:
                if pattern(href):
                    breed_links.append((href, text))
                    break
        
        # Deduplicate links
        unique_links = {}
        for href, text in breed_links:
            if not href.startswith("http"):
                href = "https://www.royalkennelclub.com" + href
            # Only add if text is not empty (actual breed links have names)
            if text and len(text.strip()) > 0:
                unique_links[href] = text
        
        print(f"\nFound {len(unique_links)} unique breed pages")
        
        if len(unique_links) == 0:
            print("⚠ Warning: No breed pages found. The website structure may have changed.")
            print("Attempting alternative scraping method...")
            # Try to extract breed info from the listing page itself
            breed_items = soup.find_all("div", class_=lambda x: x and "breed" in x.lower() if x else False)
            for item in breed_items:
                link = item.find("a", href=True)
                if link:
                    href = link.get("href")
                    text = link.get_text(strip=True)
                    if href and text:
                        if not href.startswith("http"):
                            href = "https://www.royalkennelclub.com" + href
                        unique_links[href] = text
            print(f"Found {len(unique_links)} breed items from alternative method")
        
        print("Starting to scrape breed pages...\n")
        
        # Scrape each breed page (limit to prevent overload)
        max_breeds = 30  # Increased for better coverage
        for i, (url, name) in enumerate(list(unique_links.items())[:max_breeds]):
            if i > 0:
                time.sleep(2)  # Be respectful to the server
            scrape_breed_page(url)
        
        if len(unique_links) > max_breeds:
            print(f"\n⚠ Note: Limited to {max_breeds} breeds. Found {len(unique_links)} total.")
            print(f"  Increase 'max_breeds' variable to scrape more.")
        
    except Exception as e:
        print(f"✗ Error fetching breeds list: {str(e)}")
    
    return documents


def save_documents_to_json(documents, filename="dog_breeds_rkc.json"):
    """
    Save scraped breed documents to a JSON file.
    Focuses exclusively on Royal Kennel Club breed data.
    """
    data = [
        {
            "title": doc.meta.get("title", "Unknown"),
            "content": doc.content,
            "url": doc.meta.get("url", ""),
            "source": doc.meta.get("source", "Royal Kennel Club")
        }
        for doc in documents
    ]
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Saved {len(documents)} breed documents to {filename}")


if __name__ == "__main__":
    print("="*60)
    print("DOG BREED SCRAPER - Royal Kennel Club")
    print("Focus: Dog breeds only (no disease data)")
    print("="*60)
    print()
    
    # Scrape the data
    docs = scrape_dog_breeds_rkc()
    
    print(f"\n✓ Scraped {len(docs)} breed documents total")
    
    # Save to JSON
    if docs:
        save_documents_to_json(docs)
    else:
        print("\n⚠ No documents were scraped. Check the website structure.")
    
    # Note for users
    print("\n" + "="*60)
    print("Usage in RAG Pipeline:")
    print("1. Update rag_module.py to load from 'dog_breeds_rkc.json'")
    print("2. This file contains ONLY breed data from Royal Kennel Club")
    print("3. No disease or Wikipedia data included")
    print("="*60)
