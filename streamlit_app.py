import streamlit as st
import requests

# ---------------------------
# PAGE CONFIGURATION
# ---------------------------
st.set_page_config(page_title="Dog Breed Selector", layout="centered")

# ---------------------------
# CUSTOM STYLING
# Injects CSS to style the app shell, sidebar nav items,
# cards, buttons, and topbar. The sidebar nav mimics the
# icon + label pattern used in modern chat UIs.
# ---------------------------
st.markdown("""
<style>

/* --- App background --- */
.stApp {
    background-color: #f6faf7;
}

/* --- Hide default Streamlit sidebar nav radio widget --- */
div[data-testid="stSidebarNav"] { display: none; }

/* --- Sidebar background --- */
section[data-testid="stSidebar"] {
    background-color: #eaf4ee;
}

/* --- Nav item base style --- */
.nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 12px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    color: #555;
    margin-bottom: 4px;
    transition: background 0.15s;
    text-decoration: none;
}

.nav-item:hover {
    background-color: #ffffff;
    color: #111;
}

/* --- Active nav item --- */
.nav-item.active {
    background-color: #ffffff;
    color: #2f5d50;
    font-weight: 600;
    border: 0.5px solid #d0e8dc;
}

/* --- Sidebar logo block --- */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 10px 20px;
}

.sidebar-logo .dot {
    width: 30px;
    height: 30px;
    background: #2f5d50;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 16px;
}

.sidebar-logo span {
    font-size: 14px;
    font-weight: 600;
    color: #2f5d50;
}

/* --- Page topbar --- */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 0 18px;
    border-bottom: 1px solid #ddeee5;
    margin-bottom: 20px;
}

.topbar h2 {
    margin: 0;
    font-size: 18px;
    color: #2f5d50;
}

.topbar .badge {
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 99px;
    background: #d4f0e2;
    color: #1a6645;
    font-weight: 600;
}

/* --- Content card wrapper --- */
.card {
    background-color: white;
    padding: 24px;
    border-radius: 14px;
    margin-bottom: 18px;
    border: 0.5px solid #ddeee5;
}

/* --- Form label style --- */
.form-label {
    font-size: 12px;
    font-weight: 600;
    color: #555;
    margin-bottom: 4px;
    display: block;
}

/* --- Primary button --- */
.stButton > button[kind="primary"] {
    background-color: #2f5d50 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #3d7a68 !important;
}

/* --- Secondary button --- */
.stButton > button[kind="secondary"] {
    background-color: transparent !important;
    color: #555 !important;
    border: 0.5px solid #aaa !important;
    border-radius: 8px !important;
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
}

.breed-card h3 {
    margin: 0 0 2px;
    font-size: 14px;
    color: #1a1a1a;
}

.breed-card p {
    margin: 0;
    font-size: 12px;
    color: #777;
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
}

</style>
""", unsafe_allow_html=True)


# ---------------------------
# SESSION STATE INITIALISATION
# Tracks which page the user is on and whether
# match results should be shown in the Match Me page.
# ---------------------------
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "show_results" not in st.session_state:
    st.session_state.show_results = False


# ---------------------------
# SIDEBAR NAVIGATION
# Renders a logo block and styled nav items.
# Each button updates st.session_state.page on click.
# ---------------------------
with st.sidebar:

    # Logo
    st.markdown("""
    <div class="sidebar-logo">
        <div class="dot">🐾</div>
        <span>Breed Finder</span>
    </div>
    """, unsafe_allow_html=True)

    # Nav buttons — one per page
    pages = {
        "Home":        "🏠",
        "Match Me":    "🔍",
        "Chat":        "💬",
        "Terminology": "📖",
    }

    for label, icon in pages.items():
        active_class = "active" if st.session_state.page == label else ""
        # Render the visual nav item
        st.markdown(f"""
        <div class="nav-item {active_class}">{icon}&nbsp;&nbsp;{label}</div>
        """, unsafe_allow_html=True)
        # Invisible Streamlit button overlaid to capture the click
        if st.button(label, key=f"nav_{label}", use_container_width=True):
            st.session_state.page = label
            st.session_state.show_results = False
            st.rerun()

    st.markdown("""
    <div style="position:absolute; bottom:20px; left:16px;
                font-size:11px; color:#aaa;">
        Powered by Claude API
    </div>
    """, unsafe_allow_html=True)


# ---------------------------
# TOPBAR
# Shows the current page title and a Beta badge.
# ---------------------------
page = st.session_state.page

st.markdown(f"""
<div class="topbar">
    <h2>{page}</h2>
    <span class="badge">Beta</span>
</div>
""", unsafe_allow_html=True)


# ---------------------------
# HOME PAGE
# Brief welcome message and quick-action cards
# that navigate to the main features.
# ---------------------------
if page == "Home":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Find your perfect dog")
    st.write(
        "Answer a few questions about your lifestyle and we'll match you "
        "with the right breed. Or chat with our AI for personalised advice."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**🔍 Match me**")
        st.caption("Lifestyle questionnaire to find your ideal breed.")
        if st.button("Go to Match Me", key="home_match"):
            st.session_state.page = "Match Me"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**💬 Ask the AI**")
        st.caption("Chat about any dog-related questions.")
        if st.button("Go to Chat", key="home_chat"):
            st.session_state.page = "Chat"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# MATCH ME PAGE
# Two states controlled by st.session_state.show_results:
#   False → show the 11-question form
#   True  → show breed result cards
# ---------------------------
elif page == "Match Me":

    # --- FORM STATE ---
    if not st.session_state.show_results:

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Lifestyle questionnaire")
        st.caption("Answer as many or as few questions as you like — 'No preference' is always fine.")

        # Questions laid out in a 2-column grid
        col1, col2 = st.columns(2)

        with col1:
            space = st.selectbox(
                "Living space",
                ["No preference", "Flat / apartment", "Small house", "Large house", "Other"]
            )
            grooming = st.selectbox(
                "Grooming frequency",
                ["No preference", "Daily", "More than once a week", "Once a week", "Less than once a week"]
            )
            coat = st.selectbox(
                "Coat length",
                ["No preference", "Short", "Medium", "Long"]
            )
            animals = st.selectbox(
                "Other animals at home",
                ["No preference", "Yes — other dogs", "Yes — cats",
                 "Yes — multiple animals", "Yes — other animals", "No other animals"]
            )
            experience = st.selectbox(
                "Experience with dogs",
                ["No preference", "None", "Very little", "Average", "A lot", "Very well informed"]
            )
            age = st.selectbox(
                "Preferred age range",
                ["No preference", "Less than 10 years", "Over 10 years", "Over 12 years"]
            )

        with col2:
            size = st.selectbox(
                "Preferred size",
                ["No preference", "Small", "Small-medium", "Medium", "Large", "Extra large"]
            )
            shedding = st.selectbox(
                "Shedding tolerance",
                ["No preference", "No shedding preferred", "Shedding is fine"]
            )
            exercise = st.selectbox(
                "Daily exercise",
                ["No preference", "30 minutes", "1 hour", "2 hours", "More than 2 hours"]
            )
            children = st.selectbox(
                "Children around the dog",
                ["No preference", "Yes", "No", "Unsure"]
            )
            dog_type = st.selectbox(
                "Breed type",
                ["No preference", "Toy", "Hound", "Working", "Gundog", "Pastoral", "Utility", "Unsure"]
            )

        st.markdown("<br>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns([1, 5])

        # Submit button — sends filters to the worker API
        with btn_col1:
            if st.button("Find matches", type="primary"):
                try:
                    with st.spinner("Finding best matches..."):
                        response = requests.post(
                            "https://your-worker-url.workers.dev",
                            json={"filters": {
                                "space":      space,
                                "size":       size,
                                "grooming":   grooming,
                                "shedding":   shedding,
                                "coat":       coat,
                                "exercise":   exercise,
                                "animals":    animals,
                                "children":   children,
                                "experience": experience,
                                "type":       dog_type,
                                "age":        age,
                            }}
                        )

                    if response.status_code == 200:
                        # Store results in session state and switch to results view
                        st.session_state.match_results = response.json()
                        st.session_state.show_results = True
                        st.rerun()
                    else:
                        st.error("Server error. Please try again.")

                except Exception as e:
                    st.error(f"Connection error: {e}")

        # Reset button — clears results and reruns
        with btn_col2:
            if st.button("Reset", type="secondary"):
                st.session_state.show_results = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # --- RESULTS STATE ---
    else:
        results = st.session_state.get("match_results", [])

        header_col, edit_col = st.columns([3, 1])
        with header_col:
            st.subheader(f"{len(results)} breed{'s' if len(results) != 1 else ''} matched your profile")
        with edit_col:
            if st.button("← Edit answers"):
                st.session_state.show_results = False
                st.rerun()

        if results:
            for breed in results:
                # Render each matched breed as a styled card
                st.markdown(f"""
                <div class="breed-card">
                    <div style="font-size:28px;">🐕</div>
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
# Simple chat interface with message history stored
# in session state. AI responses are fetched from
# the worker API with the full conversation history.
# ---------------------------
elif page == "Chat":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Chat with AI")

    # Initialise message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render existing messages
    for sender, msg in st.session_state.messages:
        align  = "right" if sender == "You" else "left"
        bg     = "#d4ede2" if sender == "You" else "#f1f1f1"
        color  = "#1a1a1a"

        st.markdown(f"""
        <div style="text-align:{align}; margin:10px 0;">
            <div style="display:inline-block; background:{bg}; color:{color};
                        padding:10px 15px; border-radius:12px; max-width:72%;
                        font-size:14px; line-height:1.5;">
                {msg}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Input bar
    user_input = st.text_input("Ask something about dogs:", key="chat_input",
                               placeholder="e.g. What's a good breed for a flat?")

    if st.button("Send", type="primary"):
        if user_input.strip():
            st.session_state.messages.append(("You", user_input))
            # TODO: replace stub with real API call to your worker
            st.session_state.messages.append(("AI", "AI response coming soon!"))
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------
# TERMINOLOGY PAGE
# Expandable sections for each Kennel Club breed group.
# Content is taken directly from the original app.
# ---------------------------
elif page == "Terminology":

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Dog terminology")

    with st.expander("Dog breed"):
        st.write("A standardised type of dog with consistent, heritable traits, "
                 "selectively bred over generations for appearance or function.")

    with st.expander("Pastoral group"):
        st.write(
            "The Pastoral Group consists of herding dogs associated with working cattle, sheep, "
            "reindeer and other cloven-footed animals. Usually this type of dog has a weatherproof "
            "double coat to protect it from the elements. Breeds such as the Collie family, Old "
            "English Sheepdogs and Samoyeds are but a few included in this group."
        )

    with st.expander("Hound group"):
        st.write(
            "Breeds originally used for hunting either by scent or by sight. Scent hounds include "
            "the Beagle and Bloodhound; sight hounds include the Whippet and Greyhound. Many enjoy "
            "significant exercise and can be described as dignified, aloof but trustworthy companions."
        )

    with st.expander("Utility group"):
        st.write(
            "A miscellaneous group of mainly non-sporting breeds including the Bulldog, Dalmatian, "
            "Akita and Poodle. 'Utility' means fitness for a purpose — most were selectively bred "
            "for a specific function not covered by sporting or working categories."
        )

    with st.expander("Gundog group"):
        st.write(
            "Dogs originally trained to find live game and/or retrieve wounded game. Divided into "
            "Retrievers, Spaniels, Hunt/Point/Retrieve, Pointers and Setters. Known for their "
            "temperament as all-round family dogs."
        )

    with st.expander("Toy group"):
        st.write(
            "Small companion or lap dogs. Many were bred specifically as companions; others are "
            "placed here due to their size. They should have friendly personalities, love attention, "
            "and require modest exercise."
        )

    with st.expander("Terrier group"):
        st.write(
            "Dogs bred to hunt vermin above and below ground. 'Terrier' comes from the Latin "
            "word Terra, meaning earth. Hardy and brave, they were bred to pursue fox, badger, "
            "rat and otter. Terrier-type dogs have been documented since the Middle Ages."
        )

    with st.expander("Working group"):
        st.write(
            "Selectively bred over centuries as guards and search-and-rescue dogs. Arguably "
            "some of the most heroic canines in the world — including the Boxer, Great Dane "
            "and St. Bernard — this group excels in specialised roles."
        )

    st.markdown("</div>", unsafe_allow_html=True)
