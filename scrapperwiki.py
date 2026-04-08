"""
wikipedia_scraper.py — Wikipedia dog breed list scraper
=======================================================
Extracts breed names, Wikipedia URLs, and RKC-compatible URL slugs.
Imported by: dog_breed_pipeline.py
"""

import re
import requests
from typing import List, Dict


# ---------------------------------------------------------------------------
# Slug helper (shared with dog_breed_pipeline.py)
# ---------------------------------------------------------------------------

def normalize_to_rkc_slug(breed_name: str) -> str:
    """
    Convert a Wikipedia breed name to an RKC-style URL slug.

    Examples:
        "Afghan Hound"        -> "afghan-hound"
        "Poodle (Standard)"   -> "poodle"
        "German Shepherd Dog" -> "german-shepherd-dog"
    """
    name = re.sub(r"\(.*?\)", "", breed_name)   # remove "(Standard)" etc.
    name = name.strip().lower()
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"[^a-z0-9\-]", "", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name


# ---------------------------------------------------------------------------
# Scraper class
# ---------------------------------------------------------------------------

class WikipediaScraper:
    """Scrapes the canonical dog breed list from Wikipedia."""

    URL      = "https://en.wikipedia.org/wiki/List_of_dog_breeds"
    BASE_URL = "https://en.wikipedia.org"
    TIMEOUT  = 10

    # -- internal helpers ----------------------------------------------------

    def _fetch_html(self, url: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=self.TIMEOUT)
        response.raise_for_status()
        return response.text

    def _clean_name(self, name: str) -> str:
        name = re.sub(r"\[\d+\]", "", name)
        name = re.sub(r"\[note \d+\]", "", name)
        return name.strip()

    def _parse_breeds(self, html: str) -> List[Dict[str, str]]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        breeds: List[Dict[str, str]] = []
        seen: set = set()

        for div in soup.find_all("div", {"class": "div-col"}):
            for li in div.find_all("li"):
                link = li.find("a")
                if link and link.get("href", "").startswith("/wiki/"):
                    name = self._clean_name(li.get_text(strip=True))
                    if name and name not in seen:
                        seen.add(name)
                        breeds.append({
                            "name":     name,
                            "wiki_url": f"{self.BASE_URL}{link['href']}",
                            "rkc_slug": normalize_to_rkc_slug(name),
                        })
        return breeds

    # -- public API ----------------------------------------------------------

    def scrape(self) -> List[Dict[str, str]]:
        """
        Fetch and parse the Wikipedia breed list.

        Returns a list of dicts, each with:
            name      — display name, e.g. "Afghan Hound"
            wiki_url  — full Wikipedia URL
            rkc_slug  — RKC-compatible slug, e.g. "afghan-hound"
        """
        print(f"[Wikipedia] Fetching breed list from {self.URL}...")
        html = self._fetch_html(self.URL)
        breeds = self._parse_breeds(html)
        print(f"[Wikipedia] Found {len(breeds)} breeds.\n")
        return breeds

    def fetch_breed_description(self, url: str) -> str:
        """
        Optionally fetch the first meaningful paragraph from a breed's Wikipedia page.
        Returns an empty string on failure.
        """
        from bs4 import BeautifulSoup
        try:
            html = self._fetch_html(url)
            soup = BeautifulSoup(html, "html.parser")
            content = soup.find(id="mw-content-text")
            if content:
                for p in content.find_all("p"):
                    text = p.get_text(strip=True)
                    if len(text) > 50:
                        return text[:500]
        except Exception:
            pass
        return ""


# ---------------------------------------------------------------------------
# Convenience function (mirrors original wikipedia_scraper.py API)
# ---------------------------------------------------------------------------

def scrape_dog_breeds(fetch_descriptions: bool = False) -> List[Dict[str, str]]:
    """
    Convenience wrapper around WikipediaScraper.

    Args:
        fetch_descriptions: If True, fetches a short description for each breed
                            by visiting its Wikipedia page (much slower).
    """
    scraper = WikipediaScraper()
    breeds  = scraper.scrape()

    if fetch_descriptions:
        print("Fetching breed descriptions (this may take a while)...")
        for i, breed in enumerate(breeds):
            breed["description"] = scraper.fetch_breed_description(breed["wiki_url"])
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(breeds)} breeds...")

    return breeds


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    breeds = scrape_dog_breeds()
    print(f"\nFirst 10 breeds:")
    for breed in breeds[:10]:
        print(f"  - {breed['name']}  ({breed['rkc_slug']})")