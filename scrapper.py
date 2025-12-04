import requests
from bs4 import BeautifulSoup
import time

def scrape_dog_diseases(base_url="https://en.wikipedia.org/wiki/Category:Dog_diseases"):
    """
    Scrape dog diseases from Wikipedia category page and linked articles.
    Returns a list of disease documents for the RAG pipeline.
    """
    from haystack import Document
    
    documents = []
    visited_urls = set()
    
    # Headers to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    def scrape_article(url, depth=0, max_depth=1):
        """Recursively scrape articles up to max_depth"""
        if url in visited_urls or depth > max_depth:
            return
        
        visited_urls.add(url)
        
        try:
            print(f"Scraping: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Get title
            title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            # Get main content
            content_div = soup.find("div", {"id": "mw-content-text"})
            if content_div:
                # Remove script and style elements
                for script in content_div(["script", "style"]):
                    script.decompose()
                
                # Get all paragraphs
                paragraphs = content_div.find_all("p")
                text = "\n".join([p.get_text(strip=True) for p in paragraphs[:5]])  # First 5 paragraphs
                
                if text.strip():
                    doc = Document(
                        content=text,
                        meta={
                            "title": title,
                            "url": url,
                            "source": "Wikipedia"
                        }
                    )
                    documents.append(doc)
                    print(f"  ✓ Added: {title}")
            
            # Get disease links from category page
            if depth == 0:
                category_links = content_div.find_all("a", href=lambda x: x and "/wiki/" in x and ":" not in x)
                for link in category_links[:10]:  # Limit to first 10 articles
                    disease_url = "https://en.wikipedia.org" + link.get("href")
                    if disease_url not in visited_urls:
                        time.sleep(1)  # Be respectful to the server
                        scrape_article(disease_url, depth + 1, max_depth)
            
        except Exception as e:
            print(f"  ✗ Error scraping {url}: {str(e)}")
    
    # Start scraping from the category page
    scrape_article(base_url, depth=0)
    
    return documents


def save_documents_to_json(documents, filename="dog_diseases.json"):
    """Save scraped documents to a JSON file"""
    import json
    
    data = [
        {
            "title": doc.meta.get("title", "Unknown"),
            "content": doc.content,
            "url": doc.meta.get("url", ""),
            "source": doc.meta.get("source", "")
        }
        for doc in documents
    ]
    
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✓ Saved {len(documents)} documents to {filename}")


if __name__ == "__main__":
    print("Starting to scrape dog diseases from Wikipedia...\n")
    
    # Scrape the data
    docs = scrape_dog_diseases()
    
    print(f"\n✓ Scraped {len(docs)} documents total")
    
    # Save to JSON
    save_documents_to_json(docs)
    
    # Optionally load into RAG pipeline
    try:
        from rag_module import DogHealthRAG
        print("\nTo load these documents into the RAG pipeline, update rag_module.py")
        print("to load from 'dog_diseases.json' instead of the default dataset.")
    except ImportError:
        pass
