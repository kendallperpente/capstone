"""
dog_breed_pipeline.py — Full Dog Breed Pipeline
================================================
Connects three components:
  1. wikipedia_scraper.py  → canonical breed list (names + wiki URLs + RKC slugs)
  2. scrapper.py           → RKC overview + breed-standards pages
  3. rag_module.py / rag.py → dog breed Q&A using the scraped data

Typical usage
-------------
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
import argparse
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Local module imports — single source of truth for all shared logic
# ---------------------------------------------------------------------------
from wikipedia_scraper import WikipediaScraper, normalize_to_rkc_slug
from scrapper import (
    Document,
    RKC_BASE,
    RKC_AZ,
    HEADERS,
    scrape_page_content,
    breed_url_to_standards_url,
    save_documents_to_json as save_documents,
    load_documents_from_json as load_documents,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_FILE = "dog_breeds_rkc.json"

# All known RKC breed groups — used to probe candidate URLs from a slug
RKC_GROUPS = [
    "hound", "gundog", "terrier", "utility",
    "working", "pastoral", "toy", "imported-breeds",
]


# ===========================================================================
# RKC Scraper — two modes
# ===========================================================================

def _rkc_candidate_urls(slug: str) -> List[str]:
    """Return one candidate overview URL per RKC group for a given slug."""
    return [f"{RKC_AZ}breeds/{group}/{slug}/" for group in RKC_GROUPS]


def _build_document(overview_url: str, visited: set) -> Optional[Document]:
    """Scrape one breed's overview + standards pages into a single Document."""
    overview_title, overview_text = scrape_page_content(overview_url, HEADERS, visited)

    standards_url = breed_url_to_standards_url(overview_url)
    standards_title, standards_text = None, None
    if standards_url:
        standards_title, standards_text = scrape_page_content(standards_url, HEADERS, visited)

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


def scrape_rkc_from_wikipedia(wiki_breeds: List[Dict[str, str]]) -> List[Document]:
    """
    For each Wikipedia breed, try every RKC group URL until one resolves.
    Wikipedia drives which breeds to look for on RKC.
    """
    documents: List[Document] = []
    visited: set = set()
    total = len(wiki_breeds)
    print(f"[RKC] Scraping {total} breeds sourced from Wikipedia...\n")

    for i, breed in enumerate(wiki_breeds, 1):
        name = breed["name"]
        slug = breed["rkc_slug"]

        doc = None
        for candidate_url in _rkc_candidate_urls(slug):
            doc = _build_document(candidate_url, visited)
            if doc:
                break

        if doc:
            flags = [k.replace("has_", "") for k in ("has_overview", "has_standards") if doc.meta[k]]
            print(f"  [{i}/{total}] ✓ {name} [{', '.join(flags)}]")
            documents.append(doc)
        else:
            print(f"  [{i}/{total}] ✗ {name} ({slug}) — not found on RKC")

        if i % 50 == 0:
            print(f"\n--- Progress: {i}/{total} processed, {len(documents)} saved ---\n")

    print(f"\n[RKC] Done. {len(documents)}/{total} breeds scraped successfully.\n")
    return documents


def scrape_rkc_standalone() -> List[Document]:
    """
    Scrape the RKC A-Z listing page directly (no Wikipedia needed).
    Delegates to scrapper.scrape_dog_breeds_rkc() to avoid code duplication.
    """
    from scrapper import scrape_dog_breeds_rkc
    return scrape_dog_breeds_rkc()


# ===========================================================================
# RAG query helper
# ===========================================================================

def run_rag_query(question: str, use_scraped_data: bool = True) -> str:
    """
    Run the RAG pipeline from rag_module.py (aliased via rag.py).
    Falls back gracefully if Haystack / OpenAI are unavailable.
    """
    try:
        from rag import get_rag_pipeline
        pipeline = get_rag_pipeline(use_scraped_data=use_scraped_data)
        return pipeline.answer_question(question)
    except ImportError as e:
        return (
            f"RAG pipeline unavailable: {e}\n"
            "Install with: pip install haystack-ai sentence-transformers openai"
        )
    except Exception as e:
        return f"RAG pipeline error: {e}"


# ===========================================================================
# Full pipeline orchestrator
# ===========================================================================

def run_pipeline(
    query: Optional[str] = None,
    force_rescrape: bool = False,
    use_wikipedia: bool = True,
) -> None:
    """
    Orchestrates all stages:
      1. Scrape (Wikipedia → RKC, or RKC standalone) — skipped if JSON cached
      2. Save JSON to OUTPUT_FILE
      3. Optionally answer a query via RAG

    Args:
        query:           Natural-language question for the RAG pipeline.
        force_rescrape:  Re-scrape even if dog_breeds_rkc.json already exists.
        use_wikipedia:   If True, use Wikipedia to drive RKC scraping.
                         If False, scrape the RKC A-Z listing directly.
    """
    print("=" * 60)
    print("DOG BREED PIPELINE")
    print("=" * 60 + "\n")

    # ── Stage 1 & 2: scrape + save ─────────────────────────────────────────
    if force_rescrape or not os.path.exists(OUTPUT_FILE):
        if use_wikipedia:
            print("Mode: Wikipedia → RKC (connected)\n")
            wiki_breeds = WikipediaScraper().scrape()
            documents   = scrape_rkc_from_wikipedia(wiki_breeds)
        else:
            print("Mode: RKC standalone\n")
            documents = scrape_rkc_standalone()

        save_documents(documents, OUTPUT_FILE)
    else:
        print(f"✓ Reusing cached '{OUTPUT_FILE}'  (pass --scrape to refresh)\n")

    # ── Stage 3: RAG query ─────────────────────────────────────────────────
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
        help="Force a fresh scrape (ignores cached dog_breeds_rkc.json)",
    )
    parser.add_argument(
        "--no-wikipedia", action="store_true",
        help="Scrape the RKC A-Z listing directly instead of going via Wikipedia",
    )
    parser.add_argument(
        "--query", type=str, default=None, metavar="QUESTION",
        help='Run a RAG query, e.g. --query "Calm dog for apartment living"',
    )
    args = parser.parse_args()

    run_pipeline(
        query=args.query,
        force_rescrape=args.scrape,
        use_wikipedia=not args.no_wikipedia,
    )