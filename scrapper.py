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
    breed_data = {}  # Track breed data with related pages: {breed_url: {content, related_pages, ...}}
    
    # HTTP headers to identify as a browser and avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    def scrape_page(url, is_related_page=False):
        """
        Scrape a page from Royal Kennel Club (breed page or related page).
        
        Extracts:
        - Title (from h1 tag)
        - Detailed information (from main content area)
        - Related/linked URLs (for deeper scraping)
        
        Args:
            url (str): The full URL of the page to scrape
            is_related_page (bool): Whether this is a related/sub-page
            
        Returns:
            tuple: (title, content_text, related_urls_list)
        """
        # Skip if already visited
        if url in visited_urls:
            return None, "", []
        
        visited_urls.add(url)
        found_urls = []
        
        try:
            print(f"Scraping: {url}")
            
            # Fetch the page with timeout
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract title from h1 tag
            title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            # Extract main content
            content_text = ""
            main_content = (
                soup.find("main") or 
                soup.find("article") or 
                soup.find("div", class_=lambda x: x and ("content" in x.lower() or "main" in x.lower() or "breed" in x.lower()))
            )
            
            if main_content:
                # Remove unwanted elements
                for element in main_content(["script", "style", "nav", "footer", "header"]):
                    element.decompose()
                
                # Extract paragraphs
                paragraphs = main_content.find_all(
                    ["p", "div"], 
                    class_=lambda x: x and "text" in x.lower() if x else False
                )
                
                if not paragraphs:
                    paragraphs = main_content.find_all("p")
                
                # Collect text
                text_parts = []
                for p in paragraphs[:15]:
                    text = p.get_text(strip=True)
                    if len(text) > 30:
                        text_parts.append(text)
                
                content_text = "\n\n".join(text_parts)
                
                # Extract related URLs only from main breed pages (not sub-pages)
                if not is_related_page:
                    # Find ALL links in the main content, not just in paragraphs
                    content_links = main_content.find_all("a", href=True)
                    
                    for link in content_links:
                        href = link.get("href")
                        link_text = link.get_text(strip=True)
                        
                        if href and link_text and len(link_text) > 2:  # Avoid single-char links
                            if not href.startswith("http"):
                                href = "https://www.royalkennelclub.com" + href
                            
                            # Filter out navigation/footer links and visited pages
                            if ("royalkennelclub.com" in href and 
                                href not in visited_urls and
                                "#" not in href and  # Avoid anchor-only links
                                href != breed_url):  # Avoid self-links
                                found_urls.append((href, link_text))
                    
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_found_urls = []
                    for url, text in found_urls:
                        if url not in seen:
                            seen.add(url)
                            unique_found_urls.append((url, text))
                    found_urls = unique_found_urls
                    
                    if found_urls:
                        print(f"     → Found {len(found_urls)} related pages")
            
            return title, content_text, found_urls
            
        except Exception as e:
            print(f"  ✗ Error scraping {url}: {str(e)}")
            return None, "", []
    
    
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
        max_related = 100  # Limit related URLs per breed (increased for richer data)
        
        for i, (breed_url, breed_name) in enumerate(list(unique_links.items())[:max_breeds]):
            if i > 0:
                time.sleep(2)  # Respectful delay between requests
            
            # Scrape the main breed page
            title, content, found_urls = scrape_page(breed_url, is_related_page=False)
            
            if title and content and len(content) > 100:
                # Collect content from related pages
                related_contents = []
                related_pages = []
                
                # Scrape related pages (up to limit)
                for j, (related_url, related_text) in enumerate(found_urls[:max_related]):
                    if j > 0:
                        time.sleep(1)  # Shorter delay for related pages
                    
                    rel_title, rel_content, _ = scrape_page(related_url, is_related_page=True)
                    
                    if rel_title and rel_content and len(rel_content) > 30:  # Lower threshold for more related page content
                        related_contents.append(f"\n\n--- {rel_title} ---\n{rel_content}")
                        related_pages.append({"title": rel_title, "url": related_url})
                        print(f"  ✓ Added related page: {rel_title}")
                
                # Combine main content with related content
                combined_content = content
                if related_contents:
                    combined_content += "".join(related_contents)
                
                # Create document with enriched metadata
                doc = Document(
                    content=combined_content,
                    meta={
                        "title": title,
                        "url": breed_url,
                        "source": "Royal Kennel Club",
                        "related_pages_count": len(related_pages),
                        "related_pages": related_pages
                    }
                )
                documents.append(doc)
                print(f"  ✓ Added: {title} (with {len(related_pages)} related pages)")
            else:
                print(f"  ⚠ Skipped: {title} (insufficient content)")
        
        # Notify user if we hit the breed limit
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
            "source": doc.meta.get("source", "Royal Kennel Club"),
            "related_pages_count": doc.meta.get("related_pages_count", 0),
            "related_pages": doc.meta.get("related_pages", [])
        }
        for doc in documents
    ]
    
    # Write to JSON file
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Saved {len(documents)} breed documents to {filename}")


# MAIN EXECUTION

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

