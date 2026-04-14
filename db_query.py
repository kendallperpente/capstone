"""
db_query.py — Reusable DB query helpers for dog_breeds.db
==========================================================
Imported by: streamlit_app.py (Match Me page can use query_breeds_from_quiz)
             Any other module that needs structured DB access.

CHANGES vs original:
- Table name corrected from "Breed" (capital B, didn't exist) to "breeds".
- Column names corrected to match the actual schema created by create_db.py:
    name → title, family_friendly → removed (not in schema),
    training_difficulty → removed (not in schema).
- EXERCISE_MAP now maps quiz labels to the exercise_normalized values
  ("Low" / "Moderate" / "High") stored by create_db.py, not to the raw
  RKC verbose strings.
- SIZE_MAP kept; "Small-medium" and "Extra large" still fall back to their
  nearest neighbours since the RKC data only uses Small/Medium/Large/Giant.
- query_breeds_from_quiz() returns dicts with keys that match what
  show_match_me() in streamlit_app.py already expects.
- build_rag_context_from_breeds() and map_quiz_to_db_params() unchanged
  except for the exercise/size mapping corrections above.
"""

import sqlite3
from typing import Any, Dict, List, Optional

DB_PATH = "dog_breeds.db"

# ---------------------------------------------------------------------------
# Mapping tables
# ---------------------------------------------------------------------------

# Maps quiz radio labels → exercise_normalized values in dog_breeds.db.
# create_db.py stores "Low", "Moderate", or "High" in exercise_normalized.
EXERCISE_MAP: Dict[str, str] = {
    "30 min or less":    "Low",
    "~1 hour":           "Low",
    "~2 hours":          "Moderate",
    "More than 2 hours": "High",
    # Streamlit quiz variants (from show_match_me in streamlit_app.py)
    "< 30 minutes":      "Low",
    "30–60 minutes":     "Low",
    "1–2 hours":         "Moderate",
    "2+ hours":          "High",
}

SIZE_MAP: Dict[str, str] = {
    "Small":        "Small",
    "Small-medium": "Small",    # fallback — no "Small-medium" in RKC data
    "Medium":       "Medium",
    "Large":        "Large",
    "Extra large":  "Large",    # fallback — no "Extra large" in RKC data
    "Giant":        "Giant",
}


# ---------------------------------------------------------------------------
# Core query function
# ---------------------------------------------------------------------------

def query_breeds_from_quiz(
    size: Optional[str] = None,
    exercise: Optional[str] = None,   # Low / Moderate / High  (or quiz label)
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """
    Query dog_breeds.db and return a list of breed dicts.

    Parameters
    ----------
    size : str, optional
        One of the SIZE_MAP keys or a raw "Small"/"Medium"/"Large"/"Giant".
        Omit to skip the size filter.
    exercise : str, optional
        A quiz label ("~1 hour", "< 30 minutes" …) or a normalised token
        ("Low", "Moderate", "High"). Omit to skip the exercise filter.
    limit : int
        Maximum number of rows to return.

    Returns
    -------
    List of dicts with keys: title, size, exercise, temperament, overview, rkc_url.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM breeds WHERE 1=1"
    params: List[Any] = []

    if size:
        db_size = SIZE_MAP.get(size, size)
        query += " AND size = ?"
        params.append(db_size)

    if exercise:
        # Accept either a quiz label or a pre-normalised token.
        db_exercise = EXERCISE_MAP.get(exercise, exercise)
        query += " AND exercise_normalized = ?"
        params.append(db_exercise)

    query += " LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "title":       row["title"],
            "size":        row["size"],
            "exercise":    row["exercise"],          # raw RKC string for display
            "temperament": row["temperament"],
            "overview":    row["overview"],
            "rkc_url":     row["rkc_url"],
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# RAG context builder
# ---------------------------------------------------------------------------

def build_rag_context_from_breeds(breeds: List[Dict[str, Any]]) -> str:
    """
    Turn a list of breed dicts into a text block the RAG prompt can use.
    Includes temperament and overview so the LLM has richer context.
    """
    if not breeds:
        return ""
    lines = []
    for b in breeds:
        line = f"- {b['title']} (Size: {b['size']}, Exercise: {b['exercise']}"
        if b.get("temperament"):
            line += f", Temperament: {b['temperament'][:120]}"
        line += ")"
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quiz-answer mapper
# ---------------------------------------------------------------------------

def map_quiz_to_db_params(quiz_answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert raw quiz answer dict (keys match streamlit_app.py form fields)
    into kwargs accepted by query_breeds_from_quiz().

    Dropped keys vs original:
    - family_friendly     — column doesn't exist in the breeds table
    - training_difficulty — column doesn't exist in the breeds table
    """
    raw_size = quiz_answers.get("size")
    size = raw_size if raw_size and raw_size != "No preference" else None

    raw_exercise = quiz_answers.get("exercise")
    exercise = raw_exercise if raw_exercise else None

    return {
        "size":     size,
        "exercise": exercise,
    }


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== db_query.py smoke test ===\n")

    print("All breeds (limit 5):")
    for b in query_breeds_from_quiz(limit=5):
        print(f"  {b['title']} | {b['size']} | {b['exercise']}")

    print("\nSmall + Low exercise (limit 5):")
    for b in query_breeds_from_quiz(size="Small", exercise="Low", limit=5):
        print(f"  {b['title']} | {b['size']} | {b['exercise']}")

    print("\nMedium + Moderate exercise (limit 5):")
    for b in query_breeds_from_quiz(size="Medium", exercise="Moderate", limit=5):
        print(f"  {b['title']} | {b['size']} | {b['exercise']}")
