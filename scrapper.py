import requests
from bs4 import BeautifulSoup
import time
import json

# If you're using Haystack, keep this import. Otherwise the script works without it.
try:
    from haystack import Document
    USE_HAYSTACK = True
except ImportError:
    USE_HAYSTACK = False
    class Document:
        def __init__(self, content, meta):
            self.content = content
            self.meta = meta


def scrape_page_content(url, headers, visited_urls):
    """Scrape a single page and return (title, content_text). Returns (None, None) on failure."""
    if url in visited_urls:
        return None, None
    visited_urls.add(url)

    try:
        print(f"    GET {url}")
        time.sleep(1)
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        content_text = ""
        for selector in ['main', 'article', 'div.content', 'div.main-content']:
            area = soup.select_one(selector)
            if area:
                content_text = area.get_text(separator=' ', strip=True)
                if len(content_text) > 200:
                    break

        if len(content_text) < 200:
            paragraphs = soup.find_all('p')
            content_text = '\n\n'.join(
                p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20
            )

        return title, content_text

    except Exception as e:
        print(f"    ERROR scraping {url}: {e}")
        return None, None


def breed_url_to_standards_url(breed_url):
    """
    Convert a breed overview URL to its breed standards URL.

    Example:
      Input:  https://www.royalkennelclub.com/search/breeds-a-to-z/breeds/hound/afghan-hound/
      Output: https://www.royalkennelclub.com/breed-standards/hound/afghan-hound/
    """
    # Strip trailing slash, then split on '/breeds/'
    # Everything after '/breeds/' is the group/breed-slug path
    breed_url = breed_url.rstrip('/')
    marker = '/breeds/'
    idx = breed_url.find(marker)
    if idx == -1:
        return None  # Can't determine standards URL
    remainder = breed_url[idx + len(marker):]  # e.g. "hound/afghan-hound"
    return f"https://www.royalkennelclub.com/breed-standards/{remainder}/"


def scrape_dog_breeds_rkc(base_url="https://www.royalkennelclub.com/search/breeds-a-to-z/"):
    documents = []
    visited_urls = set()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    # ------------------------------------------------------------------
    # Step 1: Collect all breed URLs from the A-Z listing page
    # ------------------------------------------------------------------
    print(f"Fetching breeds list from: {base_url}")
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Failed to fetch breed list: {e}")
        return documents

    breed_urls = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/search/breeds-a-to-z/breeds/' in href:
            if not href.startswith('http'):
                href = 'https://www.royalkennelclub.com' + href
            if href not in breed_urls:
                breed_urls.append(href)

    print(f"Found {len(breed_urls)} breed URLs\n")

    if not breed_urls:
        print("No breed URLs found - check if the site structure has changed.")
        return documents

    # ------------------------------------------------------------------
    # Step 2: For each breed, scrape BOTH the overview and standards page
    # ------------------------------------------------------------------
    for i, breed_url in enumerate(breed_urls, 1):
        print(f"[{i}/{len(breed_urls)}] {breed_url}")

        # --- Overview page ---
        overview_title, overview_content = scrape_page_content(breed_url, headers, visited_urls)

        # --- Breed standards page ---
        standards_url = breed_url_to_standards_url(breed_url)
        standards_title, standards_content = (None, None)
        if standards_url:
            standards_title, standards_content = scrape_page_content(standards_url, headers, visited_urls)

        # --- Combine and save ---
        title = overview_title or standards_title or "Unknown Breed"

        combined_content_parts = []
        if overview_content and len(overview_content) > 100:
            combined_content_parts.append("=== BREED OVERVIEW ===\n" + overview_content)
        if standards_content and len(standards_content) > 100:
            combined_content_parts.append("=== BREED STANDARD ===\n" + standards_content)

        if combined_content_parts:
            combined_content = "\n\n".join(combined_content_parts)
            doc = Document(
                content=combined_content,
                meta={
                    "title": title,
                    "url": breed_url,
                    "standards_url": standards_url or "",
                    "source": "Royal Kennel Club",
                    "has_overview": bool(overview_content and len(overview_content) > 100),
                    "has_standards": bool(standards_content and len(standards_content) > 100),
                }
            )
            documents.append(doc)
            flags = []
            if doc.meta["has_overview"]:
                flags.append("overview")
            if doc.meta["has_standards"]:
                flags.append("standards")
            print(f"  ✓ {title} [{', '.join(flags)}]")
        else:
            print(f"  ✗ Skipped (insufficient content): {breed_url}")

        if i % 50 == 0:
            print(f"\n--- Progress: {i}/{len(breed_urls)} processed, {len(documents)} saved ---\n")

    return documents


def save_documents_to_json(documents, filename="dog_breeds_rkc.json"):
    data = [
        {
            "title": doc.meta.get("title", "Unknown"),
            "content": doc.content,
            "url": doc.meta.get("url", ""),
            "standards_url": doc.meta.get("standards_url", ""),
            "source": doc.meta.get("source", "Royal Kennel Club"),
            "has_overview": doc.meta.get("has_overview", False),
            "has_standards": doc.meta.get("has_standards", False),
        }
        for doc in documents
    ]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved {len(documents)} breed documents to {filename}")


if __name__ == "__main__":
    print("=" * 60)
    print("DOG BREED SCRAPER - Royal Kennel Club (Overview + Standards)")
    print("=" * 60 + "\n")

    docs = scrape_dog_breeds_rkc()
    print(f"\n✓ Scraped {len(docs)} breed documents total")

    if docs:
        save_documents_to_json(docs)
        # Summary
        with_standards = sum(1 for d in docs if d.meta.get("has_standards"))
        print(f"  - {with_standards}/{len(docs)} breeds had a standards page")
    else:
        print("\n⚠ No documents scraped. Check if the website structure has changed.")

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("1. Data saved to 'dog_breeds_rkc.json'")
    print("2. Run: streamlit run streamlit_app.py")
    print("=" * 60)