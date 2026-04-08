import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = "dog_breeds.db"
JSON_PATH = "dog_breeds_rkc.json"


def load_json(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSON file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def create_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        DROP TABLE IF EXISTS breeds
        """
    )
    cur.execute(
        """
        CREATE TABLE breeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            size TEXT,
            exercise TEXT,
            grooming TEXT,
            shedding TEXT,
            coat_length TEXT,
            lifespan TEXT,
            breed_group TEXT,
            temperament TEXT,
            overview TEXT,
            full_text TEXT,
            rkc_url TEXT,
            standards_url TEXT,
            has_overview INTEGER,
            has_standards INTEGER
        )
        """
    )
    conn.commit()


def insert_breeds(conn: sqlite3.Connection, data: List[Dict[str, Any]]) -> None:
    cur = conn.cursor()
    inserted = 0
    for item in data:
        # Adjust keys here if your JSON uses different names
        cur.execute(
            """
            INSERT INTO breeds (
                title,
                size,
                exercise,
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("title"),
                item.get("size"),
                item.get("exercise"),
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


def main() -> None:
    data = load_json(JSON_PATH)
    conn = sqlite3.connect(DB_PATH)
    try:
        create_tables(conn)
        insert_breeds(conn, data)
    finally:
        conn.close()


if __name__ == "__main__":
    main()