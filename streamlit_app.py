"""
streamlit_app.py — Dog Breed Selector Streamlit App
====================================================
Pages: Home | Breed Finder | Match Me | Chat | Terminology

Chat page uses RAG pipeline (OpenAI/GPT) with SQLite fallback if RAG fails.
"""

import os
import sqlite3
from typing import List, Dict, Any

import streamlit as st
from rag_module import get_rag_pipeline

DB_PATH = "dog_breeds.db"


# ---------------------------
# DB HELPERS
# ---------------------------
def get_connection():
    return sqlite3.connect(DB_PATH)


def search_breeds(
    size: str | None = None,
    exercise: str | None = None,
    temperament_keywords: List[str] | None = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    where = []
    params: list[Any] = []

    if size and size != "Any":
        where.append("size = ?")
        params.append(size)

    if exercise and exercise != "Any":
        where.append("exercise = ?")
        params.append(exercise)

    if temperament_keywords:
        for kw in temperament_keywords:
            where.append("temperament LIKE ?")
            params.append(f"%{kw}%")

    where_clause = " WHERE " + " AND ".join(where) if where else ""
    query = (
        "SELECT title, size, exercise, temperament, overview, lifespan, breed_group "
        "FROM breeds"
        + where_clause
        + " LIMIT ?"
    )
    params.append(limit)

    rows = cur.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_breeds_by_text(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    like = f"%{query}%"
    rows = cur.execute(
        """
        SELECT
            title,
            size,
            exercise,
            temperament,
            overview,
            lifespan,
            breed_group,
            full_text
        FROM breeds
        WHERE
            title       LIKE ?
            OR temperament LIKE ?
            OR overview    LIKE ?
            OR full_text   LIKE ?
        LIMIT ?
        """,
        (like, like, like, like, limit),
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows]


def format_sqlite_results(matches: List[Dict[str, Any]]) -> str:
    """Format SQLite results into a readable string for the chat."""
    lines = ["Here are some breeds from the database that might fit:\n"]
    for b in matches:
        title = b.get("title", "Unknown breed")
        size = b.get("size", "N/A")
        exercise = b.get("exercise", "N/A")
        lifespan = b.get("lifespan", "") or "N/A"
        group = b.get("breed_group", "") or "N/A"
        overview = b.get("overview", "") or b.get("temperament", "") or ""
        snippet = overview[:280] + ("…" if len(overview) > 280 else "")
        lines.append(
            f"- **{title}** — Size: {size} | Exercise: {exercise} | "
            f"Lifespan: {lifespan} | Group: {group}\n  {snippet}"
        )
    return "\n\n".join(lines)


# ---------------------------
# PAGE CONFIG
# ---------------------------
# ---------------------------
import traceback
import streamlit as st

st.set_page_config(page_title="Dog Breed Selector", layout="wide")

# Define pages
PAGES = ["Home", "Breed Finder", "Match Me", "Chat", "Terminology"]

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None
if "rag_available" not in st.session_state:
    st.session_state.rag_available = False
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")
# Initialize RAG pipeline if API key is available
def initialize_rag_pipeline():
    """Initialize the RAG pipeline with the provided API key."""
    if st.session_state.openai_api_key and st.session_state.rag_pipeline is None:
        try:
            st.session_state.rag_pipeline = get_rag_pipeline(api_key=st.session_state.openai_api_key)
            st.session_state.rag_available = True
            st.session_state.rag_error = None
        except Exception as e:
            st.session_state.rag_available = False
            st.session_state.rag_error = str(e)

# Try to initialize RAG pipeline on first run
initialize_rag_pipeline()

# ---------------------------
# SIDEBAR
# ---------------------------
with st.sidebar:
    st.title("🐕 Menu")

    page = st.radio("Go to", PAGES, index=PAGES.index(st.session_state.page))
    st.session_state.page = page

    st.divider()

    # ── OpenAI API Key Configuration ──────────────────────────────────────
    st.subheader("🔑 OpenAI Configuration")
    
    with st.expander("Set API Key", expanded=not st.session_state.openai_api_key):
        api_key_input = st.text_input(
            "OpenAI API Key",
            value=st.session_state.openai_api_key,
            type="password",
            placeholder="sk-proj-...",
            help="Your OpenAI API key (keep this private)"
        )
        
        if api_key_input != st.session_state.openai_api_key:
            st.session_state.openai_api_key = api_key_input
            # Reset RAG pipeline so it gets reinitialized with the new key
            st.session_state.rag_pipeline = None
            st.session_state.rag_available = False
            st.rerun()
        
        if st.button("🔄 Reinitialize Pipeline", key="reinit_btn"):
            st.session_state.rag_pipeline = None
            st.session_state.rag_available = False
            initialize_rag_pipeline()
            st.rerun()

    st.divider()

    if st.session_state.get("rag_available"):
        st.success("✅ AI pipeline ready")
    else:
        st.warning("⚠️ AI pipeline unavailable — Chat will use DB search only")
        if "rag_error" in st.session_state and st.session_state.rag_error:
            with st.expander("Error details"):
                st.code(st.session_state.rag_error)
        elif not st.session_state.openai_api_key:
            st.caption("💡 Add your OpenAI API key above to enable AI features")

    st.divider()

    st.markdown("**Tips**")
    st.write("- Use *Breed Finder* to filter breeds from your scraped DB.")
    st.write("- Use *Match Me* for a lifestyle‑based quiz.")
    st.write("- Use *Chat* to ask free‑form questions.")


# ---------------------------
# HOME
# ---------------------------
def show_home():
    st.title("🐶 Dog Breed Selector (RKC Scraper Edition)")
    st.write(
        """
        This app uses data scraped from the Royal Kennel Club, stored in
        `dog_breeds_rkc.json` and loaded into `dog_breeds.db`.

        - **Breed Finder**: filter breeds directly from the database.
        - **Match Me**: lifestyle quiz → suggested breeds.
        """
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Data pipeline")
        st.markdown(
            """
            1. `scrapper.py` → `dog_breeds_rkc.json`
            2. `create_db.py` → `dog_breeds.db`
            3. This app reads from `dog_breeds.db` and `dog_breeds_rkc.json`
            """
        )
    with col2:
        st.subheader("Before running")
        st.markdown(
            """
            - Set `OPENAI_API_KEY` environment variable
            - Run `python scrapper.py`
            - Then `python create_db.py`
            - Confirm `dog_breeds.db` is in the project root
            """
        )


# ---------------------------
# BREED FINDER
# ---------------------------
def show_breed_finder():
    st.title("🔎 Breed Finder")
    st.write("Filter scraped RKC breeds by high‑level traits.")

    size = st.selectbox(
        "Preferred size",
        ["Any", "Small", "Medium", "Large", "Giant"],
    )
    exercise = st.selectbox(
        "Exercise requirement",
        ["Any", "Low", "Moderate", "High"],
    )
    temp_keywords_str = st.text_input(
        "Temperament keywords (optional, comma‑separated)",
        placeholder="e.g., friendly, calm, confident",
    )

    if st.button("Find breeds"):
        temperament_keywords = (
            [t.strip() for t in temp_keywords_str.split(",") if t.strip()]
            if temp_keywords_str
            else []
        )
        try:
            results = search_breeds(
                size=size if size != "Any" else None,
                exercise=exercise if exercise != "Any" else None,
                temperament_keywords=temperament_keywords,
                limit=20,
            )
        except Exception as e:
            st.error(f"Error querying database: {e}")
            return

        if not results:
            st.info("No breeds found that match those filters.")
            return

        st.subheader(f"Found {len(results)} breeds")
        for b in results:
            with st.expander(b["title"], expanded=False):
                st.write(f"**Size:** {b.get('size') or 'N/A'}")
                st.write(f"**Exercise:** {b.get('exercise') or 'N/A'}")
                st.write(f"**Lifespan:** {b.get('lifespan') or 'N/A'}")
                st.write(f"**Breed group:** {b.get('breed_group') or 'N/A'}")
                st.write(f"**Temperament:** {b.get('temperament') or 'N/A'}")
                overview = b.get("overview") or ""
                if overview:
                    st.markdown("---")
                    st.write("**Overview (from RKC):**")
                    st.write(overview)


# ---------------------------
# MATCH ME
# ---------------------------
def show_match_me():
    st.title("🎯 Match Me")
    st.write("Answer a few questions and we'll suggest breeds from your scraped DB.")

    with st.form("match_me_quiz"):
        st.subheader("Your living situation")
        home_type = st.selectbox(
            "What type of home do you live in?",
            ["Apartment", "Small house", "Large house", "Farm or rural property"],
        )
        outdoor_space = st.selectbox(
            "Outdoor space available",
            [
                "No yard",
                "Small shared yard",
                "Private small yard",
                "Large yard or land",
            ],
        )

        st.subheader("Time and activity")
        exercise_time = st.selectbox(
            "How much time per day can you dedicate to exercise?",
            ["< 30 minutes", "30–60 minutes", "1–2 hours", "2+ hours"],
        )
        activity_level = st.selectbox(
            "How active are you generally?",
            ["Prefer calm walks", "Moderately active", "Very active (running/hiking)"],
        )

        st.subheader("Experience & family")
        dog_experience = st.selectbox(
            "Your dog experience",
            ["First‑time owner", "Some experience", "Very experienced"],
        )
        kids = st.radio(
            "Children in the household?",
            ["No children", "Young children", "Older children/teens"],
        )

        allergies = st.checkbox("Someone in the household has dog allergies")

        submitted = st.form_submit_button("Get my matches")

    if not submitted:
        return

    st.subheader("Suggested breeds (using DB filters)")

    # Map quiz answers to DB filters
    if home_type == "Apartment":
        size_pref = "Small"
    elif home_type == "Small house":
        size_pref = "Medium"
    else:
        size_pref = None

    if exercise_time in ["< 30 minutes", "30–60 minutes"] and activity_level == "Prefer calm walks":
        exercise_pref = "Low"
    elif exercise_time in ["30–60 minutes", "1–2 hours"] and activity_level != "Very active (running/hiking)":
        exercise_pref = "Moderate"
    else:
        exercise_pref = "High"

    temperament_keywords: List[str] = []
    if kids != "No children":
        temperament_keywords += ["good with children", "gentle", "friendly", "family"]
    if dog_experience == "First‑time owner":
        temperament_keywords += ["easy to train", "trainable", "eager"]
    if allergies:
        temperament_keywords += ["low shedding", "hypoallergenic", "non-shedding"]

    try:
        matches = search_breeds(
            size=size_pref,
            exercise=exercise_pref,
            temperament_keywords=temperament_keywords,
            limit=10,
        )
    except Exception as e:
        st.error(f"Error querying database: {e}")
        return

    if not matches:
        st.info(
            "No clear matches from the quiz mapping. "
            "Try relaxing constraints or using Breed Finder."
        )
        return

    for b in matches:
        with st.expander(b["title"], expanded=False):
            st.write(f"**Size:** {b.get('size') or 'N/A'}")
            st.write(f"**Exercise:** {b.get('exercise') or 'N/A'}")
            st.write(f"**Lifespan:** {b.get('lifespan') or 'N/A'}")
            st.write(f"**Breed group:** {b.get('breed_group') or 'N/A'}")
            st.write(f"**Temperament:** {b.get('temperament') or 'N/A'}")
            overview = b.get("overview") or ""
            if overview:
                st.markdown("---")
                st.write("**Overview (from RKC):**")
                st.write(overview)


# ---------------------------
# CHAT
# ---------------------------
def show_chat():
    st.title("💬 Chat — Ask anything about dog breeds")

    rag_available = st.session_state.get("rag_available", False)

    if rag_available:
        st.info("")
    else:
        st.warning("⚠️ AI unavailable — using database search only.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input(
        "Ask a question",
        placeholder="e.g., give me a big dog that is friendly",
        key="chat_input",
    )

    col_send, col_clear = st.columns([1, 1])
    with col_send:
        send = st.button("Send")
    with col_clear:
        clear = st.button("Clear chat")

    if clear:
        st.session_state.chat_history = []
        st.rerun()

    if send and user_input:
        answer = None

        # ── Try RAG pipeline first ────────────────────────────────────────
        if rag_available and st.session_state.rag_pipeline is not None:
            try:
                with st.spinner("Thinking..."):
                    answer = st.session_state.rag_pipeline.answer_question(user_input)
            except Exception as e:
                st.warning(f"AI pipeline error: {e} — falling back to database search.")
                answer = None

        # ── Fallback: SQLite text search ──────────────────────────────────
        if answer is None:
            try:
                matches = search_breeds_by_text(user_input, limit=5)
                if matches:
                    answer = format_sqlite_results(matches)
                else:
                    answer = (
                        "I couldn't find any strong matches in the database for that description. "
                        "Try different words (e.g., 'large friendly family dog')."
                    )
            except Exception as e:
                answer = f"Sorry, both the AI pipeline and database search failed. Error: {e}"

        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Assistant", answer))

    # ── Render conversation ───────────────────────────────────────────────
    if st.session_state.chat_history:
        st.subheader("Conversation")
        for speaker, msg in st.session_state.chat_history:
            if speaker == "You":
                st.markdown(f"**You:** {msg}")
            else:
                st.markdown(msg)
                st.markdown("---")


# ---------------------------
# TERMINOLOGY
# ---------------------------
def show_terminology():
    st.title("📚 Dog Terminology")
    st.write("Expand the sections to learn key dog‑related terms.")

    with st.expander("Breed Groups"):
        st.write("Groups of breeds with similar historical roles or traits.")
        st.write("- **Hound Group** – traditionally used for hunting by scent or sight.")
        st.write("- **Working Group** – strong breeds used for guarding and labor.")
        st.write("- **Toy Group** – small companion dogs.")
        st.write("- **Gundog / Sporting Group** – dogs bred to work closely with hunters.")

    with st.expander("Exercise Requirement"):
        st.write("How much activity a dog needs daily.")
        st.write("- **Low** – short walks and light play.")
        st.write("- **Moderate** – one or two substantial walks per day.")
        st.write("- **High** – several hours of vigorous activity daily.")

    with st.expander("Temperament Descriptors"):
        st.write("- **Family‑friendly** – often patient and tolerant with children.")
        st.write("- **Independent** – may be less eager to please, more self‑directed.")
        st.write("- **High‑drive** – very motivated to work, may need jobs or sports.")

    with st.expander("Grooming Terms"):
        st.write("- **Double‑coated** – dense undercoat with longer outer coat; sheds seasonally.")
        st.write(
            "- **Hypoallergenic (informal)** – often used for breeds that shed less "
            "and may be better tolerated by some allergy sufferers."
        )

    with st.expander("Size Categories"):
        st.write("- **Toy** – typically under 5 kg.")
        st.write("- **Small** – roughly 5–10 kg.")
        st.write("- **Medium** – roughly 10–25 kg.")
        st.write("- **Large** – roughly 25–45 kg.")
        st.write("- **Giant** – over 45 kg.")


# ---------------------------
# MAIN ROUTER
# ---------------------------
def main():
    page = st.session_state.page
    if page == "Home":
        show_home()
    elif page == "Breed Finder":
        show_breed_finder()
    elif page == "Match Me":
        show_match_me()
    elif page == "Chat":
        show_chat()
    elif page == "Terminology":
        show_terminology()
    else:
        show_home()


if __name__ == "__main__":
    main()