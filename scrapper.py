"""
Dog Breed Scraper Module

This module scrapes dog breed information from the Royal Kennel Club website 
(https://www.royalkennelclub.com/search/breeds-a-to-z) and saves the data to JSON format.

The scraped data is used by the RAG pipeline to provide breed recommendations based on user preferences.

Main Functions:
- scrape_dog_breeds_rkc(): Scrapes breed data from Royal Kennel Club
- save_documents_to_json(): Saves scraped documents to JSON file
"""

import requests
from bs4 import BeautifulSoup
import time
import json


def scrape_dog_breeds_rkc(base_url="https://www.royalkennelclub.com/search/breeds-a-to-z"):
    """
    Scrape dog breed information from Royal Kennel Club website.
    
    This function:
    1. Fetches the breeds listing page from Royal Kennel Club
    2. Extracts links to individual breed pages
    3. Scrapes detailed breed information from each page
    4. Returns a list of Document objects formatted for the RAG pipeline
    
    Args:
        base_url (str): The Royal Kennel Club breeds listing URL
        
    Returns:
        list: List of Haystack Document objects containing breed information
    """
    from haystack import Document
    
    documents = []  # List to store scraped breed documents
    visited_urls = set()  # Track visited URLs to avoid duplicates
    
    # HTTP headers to identify as a browser and avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    def scrape_breed_page(url):
        """
        Scrape individual breed page from Royal Kennel Club.
        
        Extracts:
        - Breed name (from h1 tag)
        - Detailed breed information (from main content area)
        - Metadata (URL, source)
        
        Args:
            url (str): The full URL of the breed page to scrape
            
        Returns:
            None (documents are appended to the outer documents list)
        """
        # Skip if already visited (prevents duplicate processing)
        if url in visited_urls:
            return
        
        visited_urls.add(url)
        
        try:
            print(f"Scraping: {url}")
            
            # Fetch the page with timeout to handle slow servers
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract breed name from the h1 tag
            title_tag = soup.find("h1")
            breed_name = title_tag.get_text(strip=True) if title_tag else "Unknown Breed"
            
            # Extract main content - try multiple selectors for flexibility
            content_text = ""
            
            # Try to find main content area (supports various HTML structures)
            main_content = (
                soup.find("main") or 
                soup.find("article") or 
                soup.find("div", class_=lambda x: x and ("content" in x.lower() or "main" in x.lower() or "breed" in x.lower()))
            )
            
            if main_content:
                # Remove non-content elements that would clutter the text
                for element in main_content(["script", "style", "nav", "footer", "header"]):
                    element.decompose()
                
                # Extract paragraphs and text-containing divs
                paragraphs = main_content.find_all(
                    ["p", "div"], 
                    class_=lambda x: x and "text" in x.lower() if x else False
                )
                
                # Fallback: if no tagged paragraphs found, try all paragraphs
                if not paragraphs:
                    paragraphs = main_content.find_all("p")
                
                # Collect text from paragraphs
                text_parts = []
                for p in paragraphs[:15]:  # Limit to first 15 paragraphs to keep content focused
                    text = p.get_text(strip=True)
                    # Only include substantial paragraphs (>30 chars)
                    if len(text) > 30:
                        text_parts.append(text)
                
                # Combine all paragraphs into a single content string
                content_text = "\n\n".join(text_parts)
            
            # Only create document if we have meaningful content
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
    
    
    # ============================================================================
    # MAIN SCRAPING LOGIC: Fetch breeds listing and scrape individual pages
    # ============================================================================
    
    try:
        print(f"Fetching breeds list from: {base_url}")
        response = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract all breed links from the listing page
        # Support multiple URL patterns to handle website changes
        breed_links = []
        
        # Define URL patterns that indicate a breed page
        patterns = [
            lambda x: x and ("/breed/" in x.lower()),
            lambda x: x and ("/breeds/" in x.lower()),
            lambda x: x and ("/dog-breeds/" in x.lower()),
        ]
        
        # Find all links on the page
        all_links = soup.find_all("a", href=True)
        
        # Filter for breed links only
        for link in all_links:
            href = link.get("href")
            text = link.get_text(strip=True)
            
            # Check if link matches any breed pattern
            for pattern in patterns:
                if pattern(href):
                    breed_links.append((href, text))
                    break
        
        # Remove duplicate breed links while preserving order
        unique_links = {}
        for href, text in breed_links:
            # Convert relative URLs to absolute
            if not href.startswith("http"):
                href = "https://www.royalkennelclub.com" + href
            
            # Only add if text is meaningful (actual breed names)
            if text and len(text.strip()) > 0:
                unique_links[href] = text
        
        print(f"\nFound {len(unique_links)} unique breed pages")
        
        # Fallback method if no breed pages found (website structure may have changed)
        if len(unique_links) == 0:
            print("⚠ Warning: No breed pages found. The website structure may have changed.")
            print("Attempting alternative scraping method...")
            
            # Try to find breed items by CSS class patterns
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
        
        print("Starting to scrape individual breed pages...\n")
        
        # Scrape each breed page (limit to prevent overwhelming the server)
        max_breeds = 300  # Highest reasonable limit for comprehensive coverage
        for i, (url, name) in enumerate(list(unique_links.items())[:max_breeds]):
            if i > 0:
                time.sleep(2)  # Respectful delay between requests to the server
            scrape_breed_page(url)
        
        # Notify user if we hit the limit
        if len(unique_links) > max_breeds:
            print(f"\n⚠ Note: Limited to {max_breeds} breeds. Found {len(unique_links)} total.")
            print(f"  To scrape more, increase the 'max_breeds' variable.")
        
    except Exception as e:
        print(f"✗ Error fetching breeds list: {str(e)}")
    
    
    return documents


def save_documents_to_json(documents, filename="dog_breeds_rkc.json"):
    """
    Save scraped breed documents to a JSON file.
    
    Converts Haystack Document objects into a JSON format that can be easily
    loaded by the RAG pipeline for breed recommendations.
    
    Args:
        documents (list): List of Haystack Document objects to save
        filename (str): Output filename (default: dog_breeds_rkc.json)
        
    Returns:
        None (writes directly to file)
    """
    # Convert Document objects to JSON-serializable dictionaries
    data = [
        {
            "title": doc.meta.get("title", "Unknown"),
            "content": doc.content,
            "url": doc.meta.get("url", ""),
            "source": doc.meta.get("source", "Royal Kennel Club")
        }
        for doc in documents
    ]
    
    # Write to JSON file
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Saved {len(documents)} breed documents to {filename}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("DOG BREED SCRAPER - Royal Kennel Club")
    print("Source: https://www.royalkennelclub.com/search/breeds-a-to-z")
    print("Focus: Dog breeds only")
    print("="*60)
    print()
    
    # Scrape breed data from Royal Kennel Club
    docs = scrape_dog_breeds_rkc()
    
    print(f"\n✓ Scraped {len(docs)} breed documents total")
    
    # Save to JSON for use with RAG pipeline
    if docs:
        save_documents_to_json(docs)
    else:
        print("\n⚠ No documents were scraped. Check if the website structure has changed.")
    
    # Usage instructions
    print("\n" + "="*60)
    print("Next Steps:")
    print("1. The scraped data is saved to 'dog_breeds_rkc.json'")
    print("2. Run: streamlit run streamlit_app.py")
    print("3. The RAG pipeline will automatically load the breed data")
    print("="*60)

