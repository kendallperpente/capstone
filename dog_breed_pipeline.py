"""
Dog Breed Pipeline
==================
Connects three components:
  1. Wikipedia scraper  → canonical breed list (names + wiki URLs)
  2. Royal Kennel Club  → overview + breed-standards pages
  3. RAG pipeline       → dog breed Q&A using scraped data

Typical usage:
    # Full pipeline: scrape everything, then query
    python dog_breed_pipeline.py --scrape --query "I want a calm dog for a small apartment"

    # Skip scraping if dog_breeds_rkc.json already exists
    python dog_breed_pipeline.py --query "Active dog for a family with kids"

    # Scrape only, no query
    python dog_breed_pipeline.py --scrape

    # Scrape via RKC A-Z directly (no Wikipedia)
    python dog_breed_pipeline.py --scrape --no-wikipedia
"""

import os
import re
import json
import time
import argparse
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional Haystack import (Document is used by both scrapers and the RAG)
# ---------------------------------------------------------------------------
try:
    from haystack import Document
    USE_HAYSTACK = True
except ImportError:
    USE_HAYSTACK = False

    class Document:
        def __init__(self, content, meta):
            self.content = content
            self.meta = meta


# ===========================================================================
# SHARED UTILITIES
# ===========================================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}


def fetch_html(url: str, timeout: int = 15, delay: float = 0.5) -> Optional[str]:
    """Fetch a URL and return its HTML, or None on failure."""
    try:
        time.sleep(delay)
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"    ERROR fetching {url}: {e}")
        return None


def normalize_to_rkc_slug(breed_name: str) -> str:
    """
    Convert a Wikipedia breed name to an RKC-style URL slug.

    Examples:
        "Afghan Hound"        -> "afghan-hound"
        "Poodle (Standard)"   -> "poodle"
        "German Shepherd Dog" -> "german-shepherd-dog"
    """
    # Remove parenthetical qualifiers e.g. "(Standard)", "(Miniature)"
    name = re.sub(r"\(.*?\)", "", breed_name)
    name = name.strip().lower()
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"[^a-z0-9\-]", "", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name


def scrape_page_text(url: str, visited: set) -> Tuple[Optional[str], Optional[str]]:
    """
    Scrape title + body text from a single page.
    Returns (title, text), or (None, None) on failure / already-visited.
    """
    if url in visited:
        return None, None
    visited.add(url)

    html = fetch_html(url, delay=1.0)
    if not html:
        return None, None

    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "Unknown"

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    content = ""
    for selector in ["main", "article", "div.content", "div.main-content"]:
        area = soup.select_one(selector)
        if area:
            content = area.get_text(separator=" ", strip=True)
            if len(content) > 200:
                break

    if len(content) < 200:
        paragraphs = soup.find_all("p")
        content = "\n\n".join(
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 20
        )

    return title, content


# ===========================================================================
# STAGE 1 — Wikipedia Scraper
# ===========================================================================

class WikipediaScraper:
    """Scrapes the canonical dog breed list from Wikipedia."""

    URL = "https://en.wikipedia.org/wiki/List_of_dog_breeds"
    BASE_URL = "https://en.wikipedia.org"

    def _clean_name(self, name: str) -> str:
        name = re.sub(r"\[\d+\]", "", name)
        name = re.sub(r"\[note \d+\]", "", name)
        return name.strip()

    def _parse_breeds(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        breeds, seen = [], set()

        for div in soup.find_all("div", {"class": "div-col"}):
            for li in div.find_all("li"):
                link = li.find("a")
                if link and link.get("href", "").startswith("/wiki/"):
                    name = self._clean_name(li.get_text(strip=True))
                    if name and name not in seen:
                        seen.add(name)
                        breeds.append({
                            "name": name,
                            "wiki_url": f"{self.BASE_URL}{link['href']}",
                            "rkc_slug": normalize_to_rkc_slug(name),
                        })
        return breeds

    def scrape(self) -> List[Dict[str, str]]:
        print(f"[Wikipedia] Fetching breed list...")
        html = fetch_html(self.URL, delay=1.0)
        if not html:
            raise RuntimeError("Failed to fetch Wikipedia breed list.")
        breeds = self._parse_breeds(html)
        print(f"[Wikipedia] Found {len(breeds)} breeds.\n")
        return breeds


# ===========================================================================
# STAGE 2 — Royal Kennel Club Scraper
# ===========================================================================

RKC_BASE = "https://www.royalkennelclub.com"
RKC_AZ = f"{RKC_BASE}/search/breeds-a-to-z/"

# All RKC breed groups — used to build candidate URLs from a slug
RKC_GROUPS = [
    "hound", "gundog", "terrier", "utility",
    "working", "pastoral", "toy", "imported-breeds",
]


def rkc_overview_to_standards_url(overview_url: str) -> Optional[str]:
    """
    /search/breeds-a-to-z/breeds/hound/afghan-hound/
        -> /breed-standards/hound/afghan-hound/
    """
    url = overview_url.rstrip("/")
    marker = "/breeds/"
    idx = url.find(marker)
    if idx == -1:
        return None
    remainder = url[idx + len(marker):]
    return f"{RKC_BASE}/breed-standards/{remainder}/"


def rkc_candidate_urls(slug: str) -> List[str]:
    """Return one candidate overview URL per RKC group for the given slug."""
    return [f"{RKC_AZ}breeds/{group}/{slug}/" for group in RKC_GROUPS]


class RKCScraper:
    """
    Scrapes breed overview + breed-standards pages from the Royal Kennel Club.

    Two modes:
      scrape_from_wikipedia_breeds() — Wikipedia list drives which breeds to fetch
      scrape_standalone()            — RKC A-Z listing page drives scraping
    """

    def _build_document(self, overview_url: str, visited: set) -> Optional[Document]:
        """Scrape one breed's overview + standards pages into a single Document."""
        overview_title, overview_text = scrape_page_text(overview_url, visited)

        standards_url = rkc_overview_to_standards_url(overview_url)
        standards_title, standards_text = None, None
        if standards_url:
            standards_title, standards_text = scrape_page_text(standards_url, visited)

        title = overview_title or standards_title or "Unknown Breed"
        parts = []
        if overview_text and len(overview_text) > 100:
            parts.append("=== BREED OVERVIEW ===\n" + overview_text)
        if standards_text and len(standards_text) > 100:
            parts.append("=== BREED STANDARD ===\n" + standards_text)

        if not parts:
            return None

        return Document(
            content="\n\n".join(parts),
            meta={
                "title": title,
                "url": overview_url,
                "standards_url": standards_url or "",
                "source": "Royal Kennel Club",
                "has_overview": bool(overview_text and len(overview_text) > 100),
                "has_standards": bool(standards_text and len(standards_text) > 100),
            },
        )

    def scrape_from_wikipedia_breeds(
        self, wiki_breeds: List[Dict[str, str]]
    ) -> List[Document]:
        """
        For each Wikipedia breed, try every RKC group URL until one resolves.
        This is the "connected" mode — Wikipedia drives RKC scraping.
        """
        documents, visited = [], set()
        total = len(wiki_breeds)
        print(f"[RKC] Scraping {total} breeds sourced from Wikipedia...\n")

        for i, breed in enumerate(wiki_breeds, 1):
            name = breed["name"]
            slug = breed["rkc_slug"]

            doc = None
            for candidate_url in rkc_candidate_urls(slug):
                doc = self._build_document(candidate_url, visited)
                if doc:
                    break  # stop at first group that returns content

            if doc:
                flags = [k for k in ("has_overview", "has_standards") if doc.meta[k]]
                print(f"  [{i}/{total}] ✓ {name} [{', '.join(flags)}]")
                documents.append(doc)
            else:
                print(f"  [{i}/{total}] ✗ {name} ({slug}) — not found on RKC")

            if i % 50 == 0:
                print(f"\n--- Progress: {i}/{total} processed, {len(documents)} saved ---\n")

        print(f"\n[RKC] Done. {len(documents)}/{total} breeds scraped successfully.\n")
        return documents

    def scrape_standalone(self) -> List[Document]:
        """
        Scrape the RKC A-Z listing page directly (no Wikipedia needed).
        Replicates the original rkc_scraper.py behaviour.
        """
        documents, visited = [], set()

        print(f"[RKC] Fetching breed list from {RKC_AZ}...")
        html = fetch_html(RKC_AZ, delay=1.0)
        if not html:
            raise RuntimeError("Failed to fetch RKC breed list.")

        soup = BeautifulSoup(html, "html.parser")
        breed_urls = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/search/breeds-a-to-z/breeds/" in href:
                if not href.startswith("http"):
                    href = RKC_BASE + href
                if href not in breed_urls:
                    breed_urls.append(href)

        print(f"[RKC] Found {len(breed_urls)} breed URLs on A-Z page\n")

        for i, breed_url in enumerate(breed_urls, 1):
            doc = self._build_document(breed_url, visited)
            if doc:
                flags = [k for k in ("has_overview", "has_standards") if doc.meta[k]]
                print(f"  [{i}/{len(breed_urls)}] ✓ {doc.meta['title']} [{', '.join(flags)}]")
                documents.append(doc)
            else:
                print(f"  [{i}/{len(breed_urls)}] ✗ Skipped: {breed_url}")

            if i % 50 == 0:
                print(f"\n--- Progress: {i}/{len(breed_urls)} processed ---\n")

        print(f"\n[RKC] Done. {len(documents)}/{len(breed_urls)} breeds scraped.\n")
        return documents


# ===========================================================================
# STAGE 3 — Persist / Load JSON  (shared with rag.py)
# ===========================================================================

OUTPUT_FILE = "dog_breeds_rkc.json"


def save_documents(documents: List[Document], path: str = OUTPUT_FILE) -> None:
    """Serialize Document list to JSON for later use by the RAG pipeline."""
    data = [
        {
            "title": d.meta.get("title", "Unknown"),
            "content": d.content,
            "url": d.meta.get("url", ""),
            "standards_url": d.meta.get("standards_url", ""),
            "source": d.meta.get("source", "Royal Kennel Club"),
            "has_overview": d.meta.get("has_overview", False),
            "has_standards": d.meta.get("has_standards", False),
        }
        for d in documents
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(documents)} breed documents to '{path}'")


def load_documents(path: str = OUTPUT_FILE) -> List[Document]:
    """Load persisted breed data back into Document objects for the RAG pipeline."""
    with open(path, "r", encoding="utf-8") as f:
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
    print(f"✓ Loaded {len(docs)} breed documents from '{path}'")
    return docs


# ===========================================================================
# STAGE 4 — RAG Query  (delegates to your existing rag.py)
# ===========================================================================

def run_rag_query(question: str, use_scraped_data: bool = True) -> str:
    """
    Import and run the RAG pipeline from rag.py.
    Falls back gracefully if Haystack / OpenAI are unavailable.
    """
    try:
        from rag import get_rag_pipeline
        pipeline = get_rag_pipeline(use_scraped_data=use_scraped_data)
        return pipeline.answer_question(question)
    except ImportError:
        return (
            "RAG pipeline unavailable — rag.py not found or Haystack not installed.\n"
            "Install with: pip install haystack-ai sentence-transformers openai"
        )
    except Exception as e:
        return f"RAG pipeline error: {e}"


# ===========================================================================
# FULL PIPELINE ORCHESTRATOR
# ===========================================================================

def run_pipeline(
    query: Optional[str] = None,
    force_rescrape: bool = False,
    use_wikipedia: bool = True,
) -> None:
    """
    Orchestrates all four stages:
      1. Scrape (Wikipedia → RKC, or RKC standalone) — skipped if JSON already exists
      2. Save JSON
      3. Answer query via RAG (optional)

    Args:
        query:           Natural-language question for the RAG pipeline.
        force_rescrape:  Re-scrape even if dog_breeds_rkc.json already exists.
        use_wikipedia:   If True (default), use Wikipedia to drive RKC scraping.
                         If False, scrape RKC A-Z listing directly.
    """
    print("=" * 60)
    print("DOG BREED PIPELINE")
    print("=" * 60 + "\n")

    # ------------------------------------------------------------------
    # Stage 1 & 2 — Scrape + Save
    # ------------------------------------------------------------------
    if force_rescrape or not os.path.exists(OUTPUT_FILE):
        if use_wikipedia:
            print("Mode: Wikipedia → RKC (connected)\n")
            wiki_breeds = WikipediaScraper().scrape()
            documents = RKCScraper().scrape_from_wikipedia_breeds(wiki_breeds)
        else:
            print("Mode: RKC standalone\n")
            documents = RKCScraper().scrape_standalone()

        save_documents(documents)
    else:
        print(f"✓ Reusing cached '{OUTPUT_FILE}'  (use --scrape to refresh)\n")

    # ------------------------------------------------------------------
    # Stage 3 — RAG Query
    # ------------------------------------------------------------------
    if query:
        print(f"\n{'=' * 60}")
        print(f"RAG QUERY: {query}")
        print("=" * 60 + "\n")
        answer = run_rag_query(question=query, use_scraped_data=True)
        print(answer)


# ===========================================================================
# CLI
# ===========================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Dog Breed Pipeline — scrape Wikipedia + RKC, then query via RAG"
    )
    parser.add_argument(
        "--scrape", action="store_true",
        help="Force a fresh scrape (ignores cached dog_breeds_rkc.json)"
    )
    parser.add_argument(
        "--no-wikipedia", action="store_true",
        help="Scrape RKC A-Z listing directly instead of going via Wikipedia"
    )
    parser.add_argument(
        "--query", type=str, default=None,
        metavar="QUESTION",
        help='Run a RAG query, e.g. --query "Calm dog for apartment living"'
    )
    args = parser.parse_args()

    run_pipeline(
        query=args.query,
        force_rescrape=args.scrape,
        use_wikipedia=not args.no_wikipedia,
    )