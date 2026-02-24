import streamlit as st
import os
import json
from scrapper import scrape_dog_breeds_rkc, save_documents_to_json
from rag_module import get_rag_pipeline

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Dog Breed Selector",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# CUSTOM CSS — warm, nature-inspired design with earthy tones
# ============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Root Variables ─────────────────────────────────────── */
:root {
    --cream:    #FAF6EF;
    --warm-tan: #E8D9C0;
    --bark:     #8B6343;
    --deep-bark:#5C3D1E;
    --moss:     #6B7C5C;
    --rust:     #C4622D;
    --text:     #2E1F0F;
    --muted:    #7A6552;
    --card-bg:  #FFFFFF;
    --shadow:   0 4px 24px rgba(92,61,30,0.10);
    --radius:   14px;
}

/* ── Global Reset ───────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--cream) !important;
    color: var(--text);
}

/* ── Header ─────────────────────────────────────────────── */
.app-header {
    text-align: center;
    padding: 2.5rem 1rem 1rem;
    margin-bottom: 1rem;
}
.app-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    font-weight: 700;
    color: var(--deep-bark);
    margin: 0;
    line-height: 1.15;
    letter-spacing: -0.5px;
}
.app-header p {
    color: var(--muted);
    font-size: 1.05rem;
    font-weight: 300;
    margin-top: 0.5rem;
}
.paw-divider {
    font-size: 1.4rem;
    letter-spacing: 0.5rem;
    color: var(--warm-tan);
    margin: 0.5rem 0 1.5rem;
}

/* ── Cards ──────────────────────────────────────────────── */
.card {
    background: var(--card-bg);
    border-radius: var(--radius);
    padding: 1.8rem 2rem;
    box-shadow: var(--shadow);
    border: 1px solid var(--warm-tan);
    height: 100%;
}
.card h3 {
    font-family: 'Playfair Display', serif;
    font-size: 1.4rem;
    color: var(--deep-bark);
    margin-bottom: 0.3rem;
}
.card .card-sub {
    color: var(--muted);
    font-size: 0.88rem;
    margin-bottom: 1.2rem;
}

/* ── Result Box ─────────────────────────────────────────── */
.result-box {
    background: linear-gradient(135deg, #FFF8F0 0%, #FDF3E7 100%);
    border: 1.5px solid var(--warm-tan);
    border-left: 4px solid var(--bark);
    border-radius: var(--radius);
    padding: 1.4rem 1.6rem;
    margin-top: 1.2rem;
    font-size: 0.97rem;
    line-height: 1.7;
    color: var(--text);
}
.result-box strong {
    color: var(--deep-bark);
}

/* ── Status Badge ───────────────────────────────────────── */
.status-badge {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 1rem;
}
.status-ok   { background: #EAF2E8; color: #3A6B35; border: 1px solid #B5D5B0; }
.status-warn { background: #FEF3E2; color: #855700; border: 1px solid #F5D08A; }

/* ── Streamlit Widget Overrides ─────────────────────────── */
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] select {
    background: #FFFDF9 !important;
    border: 1.5px solid var(--warm-tan) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--bark) !important;
    box-shadow: 0 0 0 3px rgba(139,99,67,0.12) !important;
}

/* Primary buttons */
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stFormSubmitButton"] > button {
    background: var(--bark) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.4rem !important;
    transition: background 0.2s, transform 0.1s !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--deep-bark) !important;
    transform: translateY(-1px) !important;
}

/* Secondary buttons */
div[data-testid="stButton"] > button[kind="secondary"] {
    background: transparent !important;
    color: var(--bark) !important;
    border: 1.5px solid var(--bark) !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] > button[kind="secondary"]:hover {
    background: var(--warm-tan) !important;
}

/* Radio buttons */
div[data-testid="stRadio"] label {
    font-size: 0.93rem !important;
    color: var(--text) !important;
}

/* Expander */
div[data-testid="stExpander"] {
    background: var(--card-bg) !important;
    border: 1px solid var(--warm-tan) !important;
    border-radius: var(--radius) !important;
}

/* Spinner */
div[data-testid="stSpinner"] {
    color: var(--bark) !important;
}

/* Divider */
hr {
    border-color: var(--warm-tan) !important;
    margin: 1.5rem 0 !important;
}

/* Caption */
div[data-testid="stCaptionContainer"] {
    color: var(--muted) !important;
    font-size: 0.8rem !important;
}

/* Warning / success / error messages */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.9rem !important;
}

/* Column gap */
div[data-testid="column"] { padding: 0 0.6rem !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "show_quiz" not in st.session_state:
    st.session_state.show_quiz = False
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None
if "scraped_data_loaded" not in st.session_state:
    st.session_state.scraped_data_loaded = False
if "search_result" not in st.session_state:
    st.session_state.search_result = None
if "quiz_result" not in st.session_state:
    st.session_state.quiz_result = None

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="app-header">
    <h1>🐾 Dog Breed Selector</h1>
    <div class="paw-divider">· · ·</div>
    <p>Discover your perfect four-legged companion with AI-powered recommendations</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# HELPER: Initialize RAG pipeline with clean error handling
# ============================================================================

def init_rag(has_scraped_data: bool) -> bool:
    """
    Initialize the RAG pipeline into session state.
    Returns True on success, False on failure (error already shown).
    """
    if st.session_state.rag_pipeline is not None:
        return True

    with st.spinner("🔄 Initialising AI recommendation system…"):
        try:
            st.session_state.rag_pipeline = get_rag_pipeline(use_scraped_data=has_scraped_data)
            st.session_state.scraped_data_loaded = has_scraped_data
            return True
        except ValueError as e:
            st.error(f"**API Key Error:** {e}")
            st.info(
                "**How to fix:**\n"
                "1. Get your key from https://platform.openai.com/account/api-keys\n"
                "2. Run in your terminal: `export OPENAI_API_KEY='sk-proj-your-key'`\n"
                "3. Restart Streamlit: `streamlit run streamlit_app.py`"
            )
            return False
        except Exception as e:
            st.error(f"**Unexpected error:** {e}")
            return False

# ============================================================================
# DATA SOURCE SETTINGS
# ============================================================================

data_file = "dog_breeds_rkc.json"
has_scraped_data = os.path.exists(data_file)

with st.expander("⚙️  Data source settings", expanded=False):
    if has_scraped_data:
        with open(data_file, "r") as f:
            data = json.load(f)
        st.markdown(
            f'<span class="status-badge status-ok">✓ Royal Kennel Club — {len(data)} breeds loaded</span>',
            unsafe_allow_html=True
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh scraped data", use_container_width=True):
                with st.spinner("Scraping fresh breed data from Royal Kennel Club…"):
                    try:
                        docs = scrape_dog_breeds_rkc()
                        if docs:
                            save_documents_to_json(docs, data_file)
                            st.session_state.scraped_data_loaded = False
                            st.session_state.rag_pipeline = None
                            st.success(f"✓ Scraped {len(docs)} breeds successfully!")
                            st.rerun()
                        else:
                            st.error("Scraping returned no results. Try again later.")
                    except Exception as e:
                        st.error(f"Scraping error: {e}")
        with col2:
            if st.button("♻️ Reload RAG pipeline", use_container_width=True):
                st.session_state.rag_pipeline = None
                st.session_state.scraped_data_loaded = False
                st.success("Pipeline will reload on your next search.")
    else:
        st.markdown(
            '<span class="status-badge status-warn">⚠ No scraped data — using 5-breed fallback</span>',
            unsafe_allow_html=True
        )
        if st.button("🌐 Scrape Royal Kennel Club data", type="primary"):
            with st.spinner("Scraping from Royal Kennel Club… this may take a minute."):
                try:
                    docs = scrape_dog_breeds_rkc()
                    if docs:
                        save_documents_to_json(docs, data_file)
                        st.session_state.rag_pipeline = None
                        st.session_state.scraped_data_loaded = False
                        st.success(f"✓ Scraped {len(docs)} breeds!")
                        st.rerun()
                    else:
                        st.error("Scraping returned no results. Please try again later.")
                except Exception as e:
                    st.error(f"Scraping error: {e}")

st.markdown("---")

# ============================================================================
# MAIN LAYOUT — two columns
# ============================================================================

left_col, right_col = st.columns(2, gap="large")

# ============================================================================
# LEFT COLUMN: Search by characteristics
# ============================================================================

with left_col:
    st.markdown("""
    <div class="card">
        <h3>🔍 Search by characteristics</h3>
        <p class="card-sub">Describe what you're looking for and we'll find your match</p>
    </div>
    """, unsafe_allow_html=True)

    # Small spacing trick — render the card as background then overlay widgets
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    characteristics = st.text_input(
        "What are you looking for?",
        placeholder="e.g. high energy, good with kids, low shedding, apartment-friendly…",
        label_visibility="collapsed",
    )

    search_clicked = st.button("Find my breeds →", type="primary", use_container_width=True)

    if search_clicked:
        if not characteristics.strip():
            st.warning("Please enter some characteristics first.")
        else:
            if init_rag(has_scraped_data):
                with st.spinner("🐾 Finding your best matches…"):
                    try:
                        question = (
                            f"I'm looking for a dog with these characteristics: {characteristics}. "
                            "What breeds would be the best match for me?"
                        )
                        st.session_state.search_result = st.session_state.rag_pipeline.answer_question(question)
                    except Exception as e:
                        st.error(f"Error getting recommendation: {e}")
                        st.session_state.search_result = None

    if st.session_state.search_result:
        st.markdown(
            f'<div class="result-box">{st.session_state.search_result}</div>',
            unsafe_allow_html=True
        )
        source_label = "Royal Kennel Club data" if st.session_state.scraped_data_loaded else "built-in dataset"
        st.caption(f"Based on {source_label}")

# ============================================================================
# RIGHT COLUMN: Quiz
# ============================================================================

with right_col:
    st.markdown("""
    <div class="card">
        <h3>📋 Lifestyle quiz</h3>
        <p class="card-sub">Answer a few questions for a personalised recommendation</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    if st.button(
        "Hide quiz ↑" if st.session_state.show_quiz else "Take the quiz ↓",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.show_quiz = not st.session_state.show_quiz
        st.rerun()

    if st.session_state.show_quiz:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        with st.form("breed_quiz", border=False):
            q1 = st.radio("1. Living space", ["Small house", "Large house", "Flat / apartment", "Other"])
            q2 = st.radio("2. Preferred size", ["Small", "Small-medium", "Medium", "Large", "Extra large", "No preference"])
            q3 = st.radio("3. Grooming commitment", ["Daily", "Once a week", "A few times a week", "Less than once a week"])
            q4 = st.radio("4. Shedding tolerance", ["I'd rather avoid shedding", "Shedding is fine", "No preference"])
            q5 = st.radio("5. Coat length preference", ["Short", "Medium", "Long", "No preference"])
            q6 = st.radio("6. Daily exercise available", ["30 min or less", "~1 hour", "~2 hours", "More than 2 hours"])
            q7 = st.radio("7. Other animals at home", ["None", "Other dogs", "Cats", "Multiple animals"])
            q8 = st.radio("8. Children at home", ["Yes", "No", "Unsure"])
            q9 = st.radio("9. Dog ownership experience", ["None", "Very little", "Some", "A lot", "Very experienced"])
            q10 = st.radio("10. Preferred dog type", ["Toy", "Hound", "Working", "Gundog", "Pastoral", "Utility", "No preference"])
            q11 = st.radio("11. Preferred lifespan", ["Shorter (under 8 yrs)", "Medium (8–12 yrs)", "Longer (12+ yrs)", "No preference"])

            submitted = st.form_submit_button("Get my recommendations →", use_container_width=True, type="primary")

        if submitted:
            if init_rag(has_scraped_data):
                with st.spinner("🐾 Analysing your profile…"):
                    try:
                        profile_question = f"""Based on this person's profile, what dog breeds would be the best match?

LIFESTYLE PROFILE:
- Living space: {q1}
- Preferred size: {q2}
- Grooming frequency: {q3}
- Shedding tolerance: {q4}
- Coat length preference: {q5}
- Daily exercise available: {q6}
- Other animals: {q7}
- Children: {q8}
- Dog experience: {q9}
- Dog type preference: {q10}
- Desired lifespan: {q11}

Please recommend the 2–3 best breed matches with explanations for why they suit this lifestyle."""

                        st.session_state.quiz_result = st.session_state.rag_pipeline.answer_question(profile_question)
                    except Exception as e:
                        st.error(f"Error getting recommendation: {e}")
                        st.session_state.quiz_result = None

    if st.session_state.quiz_result:
        st.markdown(
            f'<div class="result-box">{st.session_state.quiz_result}</div>',
            unsafe_allow_html=True
        )
        source_label = "Royal Kennel Club data" if st.session_state.scraped_data_loaded else "built-in dataset"
        st.caption(f"Based on {source_label}")
