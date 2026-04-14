"""
create_db.py — Build dog_breeds.db from DBdata.json
=====================================================
Reads the structured JSON produced by extract_dbdata.py (which has a "name"
field, not "title") and writes it into a SQLite database.

CHANGES vs original:
- JSON_PATH changed from dog_breeds_rkc.json → DBdata.json so it reads the
  file that extract_dbdata.py actually produces (field name: "name").
- Table column "title" is populated from item["name"] to keep the rest of the
  app (which queries the "title" column) working without changes.
- Added exercise_normalized column that maps RKC verbose strings like
  "Up to 1 hour per day" to short tokens ("Low"/"Moderate"/"High") so the
  Streamlit search filters work correctly.
- Kept all original columns; no columns were removed.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

DB_PATH   = "dog_breeds.db"
JSON_PATH = "DBdata.json"   # produced by extract_dbdata.py (field: "name")

# ---------------------------------------------------------------------------
# Exercise string normalisation
# RKC stores verbose strings; the Streamlit filters use Low/Moderate/High.
# ---------------------------------------------------------------------------

EXERCISE_NORMALIZE: Dict[str, str] = {
    "up to 30 minutes per day":        "Low",
    "up to 1 hour per day":            "Low",
    "up to 1 hours per day":           "Low",      # typo variant
    "up to 2 hours per day":           "Moderate",
    "up to 2 hours  per day":          "Moderate", # double-space variant
    "more than 2 hours per day":       "High",
    "more than two hours per day":     "High",
}

def normalize_exercise(raw: str | None) -> str | None:
    """Return Low / Moderate / High (or None if unrecognised)."""
    if not raw:
        return None
    return EXERCISE_NORMALIZE.get(raw.strip().lower())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"JSON file not found: {p}\n"
            "Run extract_dbdata.py first to produce DBdata.json."
        )
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def create_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS breeds")
    cur.execute(
        """
        CREATE TABLE breeds (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            title               TEXT,        -- populated from "name" in DBdata.json
            size                TEXT,
            exercise            TEXT,        -- raw RKC string
            exercise_normalized TEXT,        -- Low / Moderate / High
            grooming            TEXT,
            shedding            TEXT,
            coat_length         TEXT,
            lifespan            TEXT,
            breed_group         TEXT,
            temperament         TEXT,
            overview            TEXT,
            full_text           TEXT,
            rkc_url             TEXT,
            standards_url       TEXT,
            has_overview        INTEGER,
            has_standards       INTEGER
        )
        """
    )
    conn.commit()


def insert_breeds(conn: sqlite3.Connection, data: List[Dict[str, Any]]) -> None:
    cur = conn.cursor()
    inserted = 0

    for item in data:
        # DBdata.json uses "name"; map it to "title" for app compatibility.
        title = item.get("name") or item.get("title")

        raw_exercise = item.get("exercise")
        exercise_normalized = normalize_exercise(raw_exercise)

        cur.execute(
            """
            INSERT INTO breeds (
                title,
                size,
                exercise,
                exercise_normalized,
                grooming,
                shedding,
                coat_length,
                lifespan,
                breed_group,
                temperament,
                overview,
                full_text,
                rkc_url,
                standards_url,
                has_overview,
                has_standards
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                item.get("size"),
                raw_exercise,
                exercise_normalized,
                item.get("grooming"),
                item.get("shedding"),
                item.get("coat_length"),
                item.get("lifespan"),
                item.get("breed_group"),
                item.get("temperament"),
                item.get("overview"),
                item.get("full_text"),
                item.get("rkc_url"),
                item.get("standards_url"),
                1 if item.get("overview") else 0,
                1 if item.get("standards_url") else 0,
            ),
        )
        inserted += 1

    conn.commit()
    print(f"Done! Inserted {inserted} breeds.")
    print(f"Database saved as: {DB_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Reading from: {JSON_PATH}")
    data = load_json(JSON_PATH)
    print(f"Loaded {len(data)} breed records.")

    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        insert_breeds(conn, data)
    finally:
        conn.close()

    # Quick sanity check
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM breeds").fetchone()[0]
    sample = conn.execute(
        "SELECT title, size, exercise, exercise_normalized FROM breeds LIMIT 3"
    ).fetchall()
    conn.close()

    print(f"\nVerification: {count} rows in breeds table.")
    print("Sample rows:")
    for row in sample:
        print(f"  {row}")


if __name__ == "__main__":
    main()
