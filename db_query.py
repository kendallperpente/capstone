import sqlite3

DB_PATH = "dog_breeds.db"

# Maps the quiz radio options (from streamlit_app.py) to the exercise strings
# stored in dog_breeds_rkc.json / dog_breeds.db
EXERCISE_MAP = {
    "30 min or less":    "Up to 30 minutes per day",
    "~1 hour":           "Up to 1 hour per day",
    "~2 hours":          "Up to 2 hours per day",
    "More than 2 hours": "More than 2 hours per day",
}

SIZE_MAP = {
    "Small":        "Small",
    "Small-medium": "Small",   # fallback to Small — no "Small-medium" in RKC data
    "Medium":       "Medium",
    "Large":        "Large",
    "Extra large":  "Large",   # fallback to Large
}


def query_breeds_from_quiz(
    size=None,
    exercise=None,
    family_friendly=None,
    training_difficulty=None,
    limit=10,
):
    """
    Query dog_breeds.db and return a list of breed dicts.
    All params are optional — omit any to skip that filter.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row          # named column access — no more row[1]
    cursor = conn.cursor()

    query = "SELECT * FROM Breed WHERE 1=1"
    params = []

    if size:
        db_size = SIZE_MAP.get(size, size)
        query += " AND size = ?"
        params.append(db_size)

    if exercise:
        db_exercise = EXERCISE_MAP.get(exercise, exercise)
        query += " AND exercise = ?"
        params.append(db_exercise)

    if family_friendly is not None:
        query += " AND family_friendly = ?"
        params.append(int(family_friendly))

    if training_difficulty:
        query += " AND training_difficulty = ?"
        params.append(training_difficulty)

    query += " LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "name":        row["name"],
            "size":        row["size"],
            "exercise":    row["exercise"],
            "temperament": row["temperament"],
            "overview":    row["overview"],
            "rkc_url":     row["rkc_url"],
        }
        for row in rows
    ]


def build_rag_context_from_breeds(breeds):
    """
    Turn a list of breed dicts into a text block the RAG prompt can use.
    Includes temperament and overview so the LLM has richer context.
    """
    if not breeds:
        return ""

    lines = []
    for b in breeds:
        line = f"- {b['name']} (Size: {b['size']}, Exercise: {b['exercise']}"
        if b.get("temperament"):
            line += f", Temperament: {b['temperament'][:120]}"
        line += ")"
        lines.append(line)

    return "\n".join(lines)


def map_quiz_to_db_params(quiz_answers):
    """
    Convert raw quiz answer dict (keys match streamlit_app.py form fields)
    into kwargs accepted by query_breeds_from_quiz().
    """
    raw_size = quiz_answers.get("size")
    size = raw_size if raw_size and raw_size != "No preference" else None

    raw_exercise = quiz_answers.get("exercise")
    exercise = raw_exercise if raw_exercise else None

    family_val = quiz_answers.get("family_friendly")
    if isinstance(family_val, bool):
        family_friendly = family_val
    elif isinstance(family_val, str):
        family_friendly = family_val.lower() not in ("no", "false", "no preference", "")
    else:
        family_friendly = None

    training_difficulty = quiz_answers.get("training_difficulty") or None

    return {
        "size":               size,
        "exercise":           exercise,
        "family_friendly":    family_friendly,
        "training_difficulty": training_difficulty,
    }