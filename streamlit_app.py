import streamlit as st
import requests

# ---------------------------
# PAGE CONFIGURATION
# ---------------------------

st.set_page_config(page_title="Dog Breed Selector", layout="centered")

# ---------------------------
# CUSTOM STYLING
# ---------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600&family=DM+Serif+Display&display=swap');

/* --- App background --- */
.stApp {
    background-color: #f5f9f6;
    font-family: 'DM Sans', sans-serif;
}

/* --- Hide default Streamlit sidebar nav --- */
div[data-testid="stSidebarNav"] {
    display: none;
}

/* --- Sidebar background --- */
section[data-testid="stSidebar"] {
    background-color: #eaf4ee;
    border-right: 1px solid #d6eadd;
}

/* ============================================================
   SIDEBAR NAV BUTTONS
   Style all sidebar buttons as clean nav items.
   Active state uses a .nav-active marker div + CSS sibling selector
   to highlight the immediately following button.
   ============================================================ */

section[data-testid="stSidebar"] .stButton {
    margin-bottom: 0 !important;
}

/* Base nav button */
section[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: transparent !important;
    border: none !important;
    border-radius: 7px !important;
    color: #5a7268 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12.5px !important;
    font-weight: 500 !important;
    padding: 7px 12px !important;
    text-align: left !important;
    cursor: pointer !important;
    transition: background 0.15s, color 0.15s !important;
    margin-bottom: 2px !important;
    box-shadow: none !important;
    justify-content: flex-start !important;
    line-height: 1.4 !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: #d8eede !important;
    color: #2f5d50 !important;
    border: none !important;
    box-shadow: none !important;
}

section[data-testid="stSidebar"] .stButton > button:focus:not(:active) {
    box-shadow: none !important;
    outline: none !important;
}

/* Active nav button: the .nav-active div is injected immediately before
   the active button's container. We target the next sibling. */
section[data-testid="stSidebar"] .nav-active + div .stButton > button {
    background: #ffffff !important;
    color: #2f5d50 !important;
    font-weight: 600 !important;
    border: 0.5px solid #c0ddd0 !important;
    box-shadow: 0 1px 4px rgba(47,93,80,0.08) !important;
}

/* --- Sidebar logo block --- */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 12px 18px;
}

.sidebar-logo .dot {
    width: 26px;
    height: 26px;
    /* Lightened gradient vs original #2f5d50 / #4a8a76 */
    background: linear-gradient(135deg, #3f7a65, #5da58a);
    border-radius: 7px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.3px;
    box-shadow: 0 2px 6px rgba(47,93,80,0.25);
    flex-shrink: 0;
}

.sidebar-logo span {
    font-size: 13px;
    font-weight: 600;
    color: #2f5d50;
    letter-spacing: -0.2px;
}

/* --- Page topbar --- */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0 16px;
    border-bottom: 1px solid #ddeee5;
    margin-bottom: 22px;
}

.topbar h2 {
    margin: 0;
    font-family: 'DM Serif Display', serif;
    font-size: 20px;
    color: #1e3d33;
    letter-spacing: -0.3px;
}

.topbar .badge {
    font-size: 10px;
    padding: 3px 9px;
    border-radius: 99px;
    background: #d4f0e2;
    color: #1a6645;
    font-weight: 600;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}

/* --- Content card wrapper --- */
.card {
    background-color: white;
    padding: 22px 24px;
    border-radius: 14px;
    margin-bottom: 16px;
    border: 0.5px solid #ddeee5;
    box-shadow: 0 2px 8px rgba(47,93,80,0.06);
}

.card-welcome {
    background: linear-gradient(135deg, #ffffff 60%, #eaf6ef);
    border-left: 3px solid #2f5d50;
}

/* --- Quick action card --- */
.action-card {
    background-color: white;
    padding: 20px;
    border-radius: 14px;
    border: 0.5px solid #ddeee5;
    box-shadow: 0 2px 8px rgba(47,93,80,0.06);
    height: 100%;
}

.action-card h4 {
    margin: 0 0 6px;
    font-size: 14px;
    font-weight: 600;
    color: #1e3d33;
}

.action-card p {
    margin: 0 0 14px;
    font-size: 12px;
    color: #7a9088;
    line-height: 1.5;
}

/* --- Stat pills on home --- */
.stat-row {
    display: flex;
    gap: 10px;
    margin-top: 14px;
    flex-wrap: wrap;
}

.stat-pill {
    font-size: 11px;
    padding: 4px 10px;
    border-radius: 99px;
    background: #eaf4ee;
    color: #2f5d50;
    font-weight: 500;
    border: 0.5px solid #c0ddd0;
}

/* --- Primary button (main content area only) --- */
.stMain .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2f5d50, #3d7a68) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 0.45rem 1.1rem !important;
    box-shadow: 0 2px 6px rgba(47,93,80,0.2) !important;
}

.stMain .stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #3d7a68, #4e9a85) !important;
    box-shadow: 0 4px 12px rgba(47,93,80,0.28) !important;
}

/* --- Secondary button --- */
.stButton > button[kind="secondary"] {
    background-color: transparent !important;
    color: #5a7268 !important;
    border: 0.5px solid #b0cdc2 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    box-shadow: none !important;
}

/* --- Result breed card --- */
.breed-card {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 16px;
    border: 0.5px solid #ddeee5;
    border-radius: 12px;
    margin-bottom: 10px;
    background: white;
    box-shadow: 0 1px 4px rgba(47,93,80,0.05);
}

.breed-card h3 {
    margin: 0 0 3px;
    font-size: 14px;
    font-weight: 600;
    color: #1a1a1a;
}

.breed-card p {
    margin: 0;
    font-size: 12px;
    color: #7a9088;
}

.breed-initial {
    width: 44px;
    height: 44px;
    background: #eaf4ee;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 15px;
    font-weight: 700;
    color: #2f5d50;
    flex-shrink: 0;
}

.breed-tag {
    display: inline-block;
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 99px;
    background: #eaf4ee;
    color: #2f5d50;
    border: 0.5px solid #c0ddd0;
    margin-left: 4px;
    font-weight: 500;
}

/* --- Chat bubbles --- */
.chat-bubble-user {
    text-align: right;
    margin: 8px 0;
}

.chat-bubble-user .bubble {
    display: inline-block;
    background: linear-gradient(135deg, #2f5d50, #3d7a68);
    color: white;
    padding: 10px 15px;
    border-radius: 16px 16px 4px 16px;
    max-width: 72%;
    font-size: 13.5px;
    line-height: 1.5;
    box-shadow: 0 2px 6px rgba(47,93,80,0.2);
}

.chat-bubble-ai {
    text-align: left;
    margin: 8px 0;
    display: flex;
    align-items: flex-start;
    gap: 8px;
}

.chat-avatar {
    width: 26px;
    height: 26px;
    background: #eaf4ee;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: 700;
    color: #2f5d50;
    flex-shrink: 0;
    border: 1px solid #c0ddd0;
    margin-top: 2px;
}

.chat-bubble-ai .bubble {
    display: inline-block;
    background: #f1f6f3;
    color: #1e3d33;
    padding: 10px 15px;
    border-radius: 4px 16px 16px 16px;
    max-width: 72%;
    font-size: 13.5px;
    line-height: 1.5;
    border: 0.5px solid #ddeee5;
}

.chat-sender-label {
    font-size: 10px;
    font-weight: 600;
    color: #9ab0a8;
    margin-bottom: 3px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}

/* --- Terminology group cards --- */
.term-group {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 16px;
    border-radius: 10px;
    background: white;
    border: 0.5px solid #ddeee5;
    margin-bottom: 10px;
    box-shadow: 0 1px 4px rgba(47,93,80,0.04);
}

.term-group-badge {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 4px;
    flex-shrink: 0;
    margin-top: 2px;
    white-space: nowrap;
}

.term-group h4 {
    margin: 0 0 4px;
    font-size: 13px;
    font-weight: 600;
    color: #1e3d33;
}

.term-group p {
    margin: 0;
    font-size: 12px;
    color: #667e75;
    line-height: 1.55;
}

/* --- Form section label --- */
.form-section {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #9ab0a8;
    margin: 14px 0 6px;
}

/* --- Streamlit select/input label override --- */
.stSelectbox label,
.stTextInput label {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #4a6a60 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# SESSION STATE
# ---------------------------

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "show_results" not in st.session_state:
    st.session_state.show_results = False

# ---------------------------
# SIDEBAR NAVIGATION
# ---------------------------

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="dot">BF</div>
        <span>Breed Finder</span>
    </div>
    """, unsafe_allow_html=True)

    pages = ["Home", "Match Me", "Chat", "Terminology"]
    for label in pages:
        if st.session_state.page == label:
            st.markdown('<div class="nav-active"></div>', unsafe_allow_html=True)
        if st.button(label, key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.session_state.show_results = False
            st.rerun()


# ---------------------------
# TOPBAR
# ---------------------------

page = st.session_state.page

page_subtitles = {
    "Home": "Welcome",
    "Match Me": "Find your ideal breed",
    "Chat": "Ask the AI anything",
    "Terminology": "Breed group reference",
}

st.markdown(f"""
<div class="topbar">
    <h2>{page}</h2>
    <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:11px;color:#9ab0a8;">{page_subtitles.get(page,'')}</span>
        <span class="badge">Beta</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# HOME PAGE
# ---------------------------

if page == "Home":
    st.markdown("""
    <div class="card card-welcome">
        <div style="font-family:'DM Serif Display',serif;font-size:22px;color:#1e3d33;margin-bottom:8px;">
            Find your perfect dog
        </div>
        <p style="font-size:13.5px;color:#5a7268;line-height:1.6;margin:0 0 12px;">
            Answer a few questions about your lifestyle and we'll match you with the right breed.
            Or chat with our AI for personalised advice.
        </p>
        <div class="stat-row">
            <span class="stat-pill">200+ breeds</span>
            <span class="stat-pill">Instant match</span>
            <span class="stat-pill">AI-powered</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="action-card">
            <h4>Match Me</h4>
            <p>Answer 11 lifestyle questions and get a personalised breed shortlist.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start questionnaire", key="home_match", type="primary", use_container_width=True):
            st.session_state.page = "Match Me"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="action-card">
            <h4>Ask the AI</h4>
            <p>Chat freely about any dog-related questions — breeds, training, care and more.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open chat", key="home_chat", type="primary", use_container_width=True):
            st.session_state.page = "Chat"
            st.rerun()

# ---------------------------
# MATCH ME PAGE
# ---------------------------

elif page == "Match Me":
    if not st.session_state.show_results:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Lifestyle questionnaire")
        st.caption("Answer as many or as few as you like — 'No preference' is always fine.")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="form-section">Your home</div>', unsafe_allow_html=True)
            space = st.selectbox(
                "Living space",
                ["No preference", "Flat / apartment", "Small house", "Large house", "Other"],
            )
            size = st.selectbox(
                "Preferred size",
                ["No preference", "Small", "Small-medium", "Medium", "Large", "Extra large"],
            )
            animals = st.selectbox(
                "Other animals at home",
                ["No preference", "Yes — other dogs", "Yes — cats", "Yes — multiple animals",
                 "Yes — other animals", "No other animals"],
            )
            children = st.selectbox(
                "Children around the dog",
                ["No preference", "Yes", "No", "Unsure"],
            )

            st.markdown('<div class="form-section">Breed preferences</div>', unsafe_allow_html=True)
            dog_type = st.selectbox(
                "Breed type",
                ["No preference", "Toy", "Hound", "Working", "Gundog", "Pastoral", "Utility", "Unsure"],
            )
            age = st.selectbox(
                "Preferred age range",
                ["No preference", "Less than 10 years", "Over 10 years", "Over 12 years"],
            )

        with col2:
            st.markdown('<div class="form-section">Care & activity</div>', unsafe_allow_html=True)
            exercise = st.selectbox(
                "Daily exercise",
                ["No preference", "30 minutes", "1 hour", "2 hours", "More than 2 hours"],
            )
            grooming = st.selectbox(
                "Grooming frequency",
                ["No preference", "Daily", "More than once a week", "Once a week", "Less than once a week"],
            )
            coat = st.selectbox(
                "Coat length",
                ["No preference", "Short", "Medium", "Long"],
            )
            shedding = st.selectbox(
                "Shedding tolerance",
                ["No preference", "No shedding preferred", "Shedding is fine"],
            )

            st.markdown('<div class="form-section">Your experience</div>', unsafe_allow_html=True)
            experience = st.selectbox(
                "Experience with dogs",
                ["No preference", "None", "Very little", "Average", "A lot", "Very well informed"],
            )

        st.markdown("<br>", unsafe_allow_html=True)

        btn_col1, btn_col2, _ = st.columns([1.4, 0.8, 3])
        with btn_col1:
            if st.button("Find matches", type="primary"):
                try:
                    with st.spinner("Finding best matches..."):
                        response = requests.post(
                            "https://your-worker-url.workers.dev",
                            json={
                                "filters": {
                                    "space": space,
                                    "size": size,
                                    "grooming": grooming,
                                    "shedding": shedding,
                                    "coat": coat,
                                    "exercise": exercise,
                                    "animals": animals,
                                    "children": children,
                                    "experience": experience,
                                    "type": dog_type,
                                    "age": age,
                                }
                            },
                        )
                        if response.status_code == 200:
                            st.session_state.match_results = response.json()
                            st.session_state.show_results = True
                            st.rerun()
                        else:
                            st.error("Server error. Please try again.")
                except Exception as e:
                    st.error(f"Connection error: {e}")

        with btn_col2:
            if st.button("Reset", type="secondary"):
                st.session_state.show_results = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        results = st.session_state.get("match_results", [])
        header_col, edit_col = st.columns([3, 1])

        with header_col:
            st.subheader(f"{len(results)} breed{'s' if len(results) != 1 else ''} matched your profile")

        with edit_col:
            if st.button("Edit answers"):
                st.session_state.show_results = False
                st.rerun()

        if results:
            for breed in results:
                initial = breed['name'][0].upper() if breed.get('name') else "?"
                st.markdown(f"""
                <div class="breed-card">
                    <div class="breed-initial">{initial}</div>
                    <div style="flex:1;">
                        <h3>{breed['name']}</h3>
                        <p>{breed.get('size','—')} · {breed.get('type','—')} · {breed.get('lifespan','—')}</p>
                    </div>
                    <div>
                        <span class="breed-tag">{breed.get('energy','—')}</span>
                        <span class="breed-tag">{breed.get('grooming','—')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No matches found. Try adjusting your answers.")

# ---------------------------
# CHAT PAGE
# ---------------------------

elif page == "Chat":
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.markdown("""
    <div class="card">
        <div style="font-size:13.5px;font-weight:600;color:#1e3d33;margin-bottom:3px;">
            Chat with AI
        </div>
        <div style="font-size:12px;color:#9ab0a8;">
            Ask anything about dog breeds, training, care, or behaviour.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center;padding:30px 0 10px;color:#9ab0a8;font-size:13px;">
            Ask me anything about dogs — breeds, training, care, or behaviour.
        </div>
        """, unsafe_allow_html=True)
    else:
        for sender, msg in st.session_state.messages:
            if sender == "You":
                st.markdown(f"""
                <div class="chat-bubble-user">
                    <div class="chat-sender-label">You</div>
                    <div class="bubble">{msg}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-bubble-ai">
                    <div class="chat-avatar">AI</div>
                    <div>
                        <div class="chat-sender-label">Breed Finder AI</div>
                        <div class="bubble">{msg}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    input_col, send_col = st.columns([5, 1])
    with input_col:
        user_input = st.text_input(
            "Message",
            key="chat_input",
            label_visibility="collapsed",
            placeholder="e.g. What's a good breed for a flat?",
        )
    with send_col:
        send = st.button("Send", type="primary", use_container_width=True)

    if send:
        if user_input.strip():
            st.session_state.messages.append(("You", user_input))
            st.session_state.messages.append(("AI", "AI response coming soon!"))
            st.rerun()

    if st.session_state.messages:
        if st.button("Clear conversation", type="secondary"):
            st.session_state.messages = []
            st.rerun()

# ---------------------------
# TERMINOLOGY PAGE
# ---------------------------

elif page == "Terminology":
  
    groups = [
        (
            "#eaf4ee",
            "#2f5d50",
            "Pastoral",
            "Pastoral group",
            "Herding dogs bred to work cattle, sheep and reindeer — usually with a weatherproof double coat. "
            "Includes the Collie family, Old English Sheepdogs and Samoyeds.",
        ),
        (
            "#fdf3ea",
            "#b05e1a",
            "Hound",
            "Hound group",
            "Breeds originally used for hunting by scent or sight. Scent hounds include the Beagle and Bloodhound; "
            "sight hounds the Whippet and Greyhound. Dignified, aloof but trustworthy companions that enjoy significant exercise.",
        ),
        (
            "#eaedf9",
            "#3a44a0",
            "Utility",
            "Utility group",
            "A miscellaneous group of mainly non-sporting breeds including the Bulldog, Dalmatian, Akita and Poodle. "
            "'Utility' means fitness for a purpose — most were bred for a function outside sport or work.",
        ),
        (
            "#f0f9ea",
            "#3d7a1a",
            "Gundog",
            "Gundog group",
            "Dogs trained to find and/or retrieve game. Divided into Retrievers, Spaniels, Hunt/Point/Retrieve, Pointers "
            "and Setters. Renowned for their friendly temperament as all-round family dogs.",
        ),
        (
            "#faeaf9",
            "#8a3a98",
            "Toy",
            "Toy group",
            "Small companion or lap dogs, many bred specifically as companions. Friendly personalities, love attention, "
            "and require modest exercise.",
        ),
        (
            "#fdf6ea",
            "#9a6a10",
            "Terrier",
            "Terrier group",
            "Bred to hunt vermin above and below ground — 'Terrier' derives from the Latin Terra (earth). Hardy and brave, "
            "with a history tracing back to the Middle Ages.",
        ),
        (
            "#eaf4f9",
            "#1a6a8a",
            "Working",
            "Working group",
            "Guards and search-and-rescue dogs bred over centuries. Includes the Boxer, Great Dane and St. Bernard — "
            "some of the most heroic and specialised canines in the world.",
        ),
        (
            "#f5f5f5",
            "#555555",
            "Breed",
            "Dog breed",
            "A standardised type of dog with consistent, heritable traits, selectively bred over generations "
            "for appearance or function.",
        ),
    ]

    for bg, color, badge, title, desc in groups:
        st.markdown(
            f"""
            <div class="term-group" style="border-left: 3px solid {color};">
                <div class="term-group-badge" style="background:{bg};color:{color};">{badge}</div>
                <div>
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
