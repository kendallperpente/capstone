"""
scrapper.py — Royal Kennel Club breed scraper
=============================================
Single source of truth for all RKC scraping logic.
Imported by:  streamlit_app.py, dog_breed_pipeline.py
"""

import json
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional Haystack import — falls back to a plain Document shim
# ---------------------------------------------------------------------------
try:
    from haystack import Document
    USE_HAYSTACK = True
except ImportError:
    USE_HAYSTACK = False

    class Document:
        def __init__(self, content: str, meta: dict):
            self.content = content
            self.meta = meta


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RKC_BASE = "https://www.royalkennelclub.com"
RKC_AZ   = f"{RKC_BASE}/search/breeds-a-to-z/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def scrape_page_content(
    url: str,
    headers: dict,
    visited_urls: set,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Fetch a single page and return (title, body_text).
    Returns (None, None) on failure or if already visited.
    """
    if url in visited_urls:
        return None, None
    visited_urls.add(url)

    try:
        print(f"    GET {url}")
        time.sleep(1)
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "No title found"

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        content_text = ""
        for selector in ["main", "article", "div.content", "div.main-content"]:
            area = soup.select_one(selector)
            if area:
                content_text = area.get_text(separator=" ", strip=True)
                if len(content_text) > 200:
                    break

        if len(content_text) < 200:
            paragraphs = soup.find_all("p")
            content_text = "\n\n".join(
                p.get_text(strip=True)
                for p in paragraphs
                if len(p.get_text(strip=True)) > 20
            )

        return title, content_text

    except Exception as e:
        print(f"    ERROR scraping {url}: {e}")
        return None, None


def breed_url_to_standards_url(breed_url: str) -> Optional[str]:
    """
    Convert a breed overview URL to its breed-standards URL.

    Example:
        .../search/breeds-a-to-z/breeds/hound/afghan-hound/
        -> .../breed-standards/hound/afghan-hound/
    """
    breed_url = breed_url.rstrip("/")
    marker = "/breeds/"
    idx = breed_url.find(marker)
    if idx == -1:
        return None
    remainder = breed_url[idx + len(marker):]
    return f"{RKC_BASE}/breed-standards/{remainder}/"


# ---------------------------------------------------------------------------
# Main scrape entry-point
# ---------------------------------------------------------------------------

def scrape_dog_breeds_rkc(
    base_url: str = RKC_AZ,
) -> List[Document]:
    """
    Scrape all dog breeds from the Royal Kennel Club A-Z listing.
    For each breed, fetches both the overview page and the breed-standards page.

    Returns a list of Document objects (Haystack or shim).
    """
    documents: List[Document] = []
    visited_urls: set = set()

    # ── Step 1: collect breed URLs from the A-Z listing ───────────────────
    print(f"Fetching breeds list from: {base_url}")
    try:
        response = requests.get(base_url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
    except Exception as e:
        print(f"Failed to fetch breed list: {e}")
        return documents

    breed_urls: List[str] = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/search/breeds-a-to-z/breeds/" in href:
            if not href.startswith("http"):
                href = RKC_BASE + href
            if href not in breed_urls:
                breed_urls.append(href)

    print(f"Found {len(breed_urls)} breed URLs\n")

    if not breed_urls:
        print("No breed URLs found — check if the site structure has changed.")
        return documents

    # ── Step 2: scrape overview + standards for each breed ────────────────
    for i, breed_url in enumerate(breed_urls, 1):
        print(f"[{i}/{len(breed_urls)}] {breed_url}")

        overview_title, overview_content = scrape_page_content(
            breed_url, HEADERS, visited_urls
        )

        standards_url = breed_url_to_standards_url(breed_url)
        standards_title, standards_content = None, None
        if standards_url:
            standards_title, standards_content = scrape_page_content(
                standards_url, HEADERS, visited_urls
            )

        title = overview_title or standards_title or "Unknown Breed"

        parts = []
        if overview_content and len(overview_content) > 100:
            parts.append("=== BREED OVERVIEW ===\n" + overview_content)
        if standards_content and len(standards_content) > 100:
            parts.append("=== BREED STANDARD ===\n" + standards_content)

        if parts:
            doc = Document(
                content="\n\n".join(parts),
                meta={
                    "title": title,
                    "url": breed_url,
                    "standards_url": standards_url or "",
                    "source": "Royal Kennel Club",
                    "has_overview": bool(overview_content and len(overview_content) > 100),
                    "has_standards": bool(standards_content and len(standards_content) > 100),
                },
            )
            documents.append(doc)
            flags = [k.replace("has_", "") for k in ("has_overview", "has_standards") if doc.meta[k]]
            print(f"  ✓ {title} [{', '.join(flags)}]")
        else:
            print(f"  ✗ Skipped (insufficient content): {breed_url}")

        if i % 50 == 0:
            print(f"\n--- Progress: {i}/{len(breed_urls)} processed, {len(documents)} saved ---\n")

    return documents


# ---------------------------------------------------------------------------
# JSON persistence helpers (used by streamlit_app.py and dog_breed_pipeline.py)
# ---------------------------------------------------------------------------

def save_documents_to_json(
    documents: List[Document],
    filename: str = "dog_breeds_rkc.json",
) -> None:
    """Serialize a list of Documents to a JSON file."""
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


# Alias so dog_breed_pipeline.py can call save_documents() without changes
save_documents = save_documents_to_json


def load_documents_from_json(
    filename: str = "dog_breeds_rkc.json",
) -> List[Document]:
    """Load persisted breed data back into Document objects."""
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    docs = [
        Document(
            content=item["content"],
            meta={
                "title": item.get("title", "Unknown"),
                "url": item.get("url", ""),
                "source": item.get("source", "Royal Kennel Club"),
            },
        )
        for item in data
    ]
    print(f"✓ Loaded {len(docs)} breed documents from '{filename}'")
    return docs


# Alias for pipeline compatibility
load_documents = load_documents_from_json


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("DOG BREED SCRAPER — Royal Kennel Club (Overview + Standards)")
    print("=" * 60 + "\n")

    docs = scrape_dog_breeds_rkc()
    print(f"\n✓ Scraped {len(docs)} breed documents total")

    if docs:
        save_documents_to_json(docs)
        with_standards = sum(1 for d in docs if d.meta.get("has_standards"))
        print(f"  - {with_standards}/{len(docs)} breeds had a standards page")
    else:
        print("\n⚠  No documents scraped. Check if the website structure has changed.")

    print("\n" + "=" * 60)
    print("Next Steps:")
    print("1. Data saved to 'dog_breeds_rkc.json'")
    print("2. Run: streamlit run streamlit_app.py")
    print("=" * 60)