import streamlit as st
import os

st.set_page_config(page_title="My Perfect Pup", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600&family=DM+Serif+Display&display=swap');

[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

.stApp {
    background-color: #f5f9f6;
    font-family: 'DM Sans', sans-serif;
}

div[data-testid="stSidebarNav"] { display: none; }

section[data-testid="stSidebar"] {
    background-color: #eaf4ee;
    border-right: 1px solid #d6eadd;
}

section[data-testid="stSidebar"] .stButton {
    margin-bottom: 0 !important;
}

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

section[data-testid="stSidebar"] .nav-active + div .stButton > button {
    background: #ffffff !important;
    color: #2f5d50 !important;
    font-weight: 600 !important;
    border: 0.5px solid #c0ddd0 !important;
    box-shadow: 0 1px 4px rgba(47,93,80,0.08) !important;
}

.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 12px 18px;
}

.sidebar-logo .dot {
    width: 26px;
    height: 26px;
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

.stButton > button[kind="secondary"] {
    background-color: transparent !important;
    color: #5a7268 !important;
    border: 0.5px solid #b0cdc2 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    box-shadow: none !important;
}

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

.form-section {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #9ab0a8;
    margin: 14px 0 6px;
}

.stSelectbox label,
.stTextInput label {
    font-size: 12px !important;
    font-weight: 500 !important;
    color: #4a6a60 !important;
}

.rag-result-card {
    background: white;
    border: 0.5px solid #ddeee5;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(47,93,80,0.06);
    font-size: 13.5px;
    color: #1e3d33;
    line-height: 1.75;
    white-space: pre-wrap;
}
</style>
""", unsafe_allow_html=True)


def get_api_key() -> str:
    """Load API key from st.secrets, falling back to environment variable."""
    try:
        return st.secrets["OPENAI_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.getenv("OPENAI_API_KEY", "")


@st.cache_resource(show_spinner=False)
def load_rag_pipeline(api_key: str, use_scraped: bool = True):
    try:
        from rag_module import get_rag_pipeline
        return get_rag_pipeline(use_scraped_data=use_scraped, api_key=api_key), None
    except Exception as e:
        return None, str(e)


if "page" not in st.session_state:
    st.session_state.page = "Home"
if "show_results" not in st.session_state:
    st.session_state.show_results = False
if "messages" not in st.session_state:
    st.session_state.messages = []

OPENAI_API_KEY = get_api_key()


with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="dot">MPP</div>
        <span>My Perfect Pup</span>
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
    </div>
</div>
""", unsafe_allow_html=True)


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
            <span class="stat-pill">300+ breeds</span>
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


elif page == "Match Me":
    if not st.session_state.show_results:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Lifestyle questionnaire")
        st.caption("Answer as many or as few as you like — 'No preference' is always fine.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="form-section">Your home</div>', unsafe_allow_html=True)
            space    = st.selectbox("Living space", ["No preference", "Flat / apartment", "Small house", "Large house", "Other"])
            size     = st.selectbox("Preferred size", ["No preference", "Small", "Small-medium", "Medium", "Large", "Extra large"])
            animals  = st.selectbox("Other animals at home", ["No preference", "Yes — other dogs", "Yes — cats", "Yes — multiple animals", "Yes — other animals", "No other animals"])
            children = st.selectbox("Children around the dog", ["No preference", "Yes", "No", "Unsure"])
            st.markdown('<div class="form-section">Breed preferences</div>', unsafe_allow_html=True)
            dog_type = st.selectbox("Breed type", ["No preference", "Toy", "Hound", "Working", "Gundog", "Pastoral", "Utility", "Unsure"])
            age      = st.selectbox("Preferred age range", ["No preference", "Less than 10 years", "Over 10 years", "Over 12 years"])

        with col2:
            st.markdown('<div class="form-section">Care & activity</div>', unsafe_allow_html=True)
            exercise = st.selectbox("Daily exercise", ["No preference", "30 minutes", "1 hour", "2 hours", "More than 2 hours"])
            grooming = st.selectbox("Grooming frequency", ["No preference", "Daily", "More than once a week", "Once a week", "Less than once a week"])
            coat     = st.selectbox("Coat length", ["No preference", "Short", "Medium", "Long"])
            shedding = st.selectbox("Shedding tolerance", ["No preference", "No shedding preferred", "Shedding is fine"])
            st.markdown('<div class="form-section">Your experience</div>', unsafe_allow_html=True)
            experience = st.selectbox("Experience with dogs", ["No preference", "None", "Very little", "Average", "A lot", "Very well informed"])

        st.markdown("<br>", unsafe_allow_html=True)

        btn_col1, btn_col2, _ = st.columns([1.4, 0.8, 3])
        with btn_col1:
            find_clicked = st.button("Find matches", type="primary")
        with btn_col2:
            if st.button("Reset", type="secondary"):
                st.session_state.show_results = False
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        if find_clicked:
            if not OPENAI_API_KEY:
                st.error("OpenAI API key not found. Please add it to .streamlit/secrets.toml.")
            else:
                query_parts = []
                if space      != "No preference": query_parts.append(f"I live in a {space.lower()}")
                if size       != "No preference": query_parts.append(f"I want a {size.lower()} sized dog")
                if exercise   != "No preference": query_parts.append(f"I can provide {exercise} of exercise per day")
                if grooming   != "No preference": query_parts.append(f"I prefer {grooming.lower()} grooming")
                if coat       != "No preference": query_parts.append(f"I prefer a {coat.lower()} coat")
                if shedding   != "No preference": query_parts.append(shedding.lower())
                if animals    != "No preference": query_parts.append(f"I have {animals.lower()}")
                if children   != "No preference": query_parts.append(f"children present: {children.lower()}")
                if experience != "No preference": query_parts.append(f"my experience with dogs is {experience.lower()}")
                if dog_type   != "No preference": query_parts.append(f"I am interested in {dog_type.lower()} breeds")
                if age        != "No preference": query_parts.append(f"preferred dog lifespan: {age.lower()}")

                if not query_parts:
                    query = "Recommend a few popular, well-rounded dog breeds suitable for most households."
                else:
                    query = (
                        "Please recommend 3 dog breeds for someone with the following lifestyle: "
                        + "; ".join(query_parts)
                        + ". For each breed explain why it is a good match."
                    )

                with st.spinner("Finding matches..."):
                    rag, err = load_rag_pipeline(OPENAI_API_KEY, use_scraped=True)
                    if err:
                        st.error(f"Could not load AI pipeline: {err}")
                    else:
                        try:
                            answer = rag.answer_question(query)
                            st.session_state.match_results = answer
                            st.session_state.show_results = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error getting recommendations: {e}")

    else:
        header_col, edit_col = st.columns([3, 1])
        with header_col:
            st.subheader("Your breed matches")
        with edit_col:
            if st.button("Edit answers"):
                st.session_state.show_results = False
                st.rerun()

        results = st.session_state.get("match_results", "")
        if results:
            st.markdown(f'<div class="rag-result-card">{results}</div>', unsafe_allow_html=True)
        else:
            st.info("No matches found. Try adjusting your answers.")


elif page == "Chat":
    st.markdown("""
    <div class="card">
        <div style="font-size:13.5px;font-weight:600;color:#1e3d33;margin-bottom:3px;">Chat with AI</div>
        <div style="font-size:12px;color:#9ab0a8;">Ask anything about dog breeds, training, care, or behavior.</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center;padding:30px 0 10px;color:#9ab0a8;font-size:13px;">
            Ask me anything about dogs — breeds, training, care, or behavior.
        </div>
        """, unsafe_allow_html=True)
    else:
        for sender, msg in st.session_state.messages:
            safe_msg = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if sender == "You":
                st.markdown(f"""
                <div class="chat-bubble-user">
                    <div class="chat-sender-label">You</div>
                    <div class="bubble">{safe_msg}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-bubble-ai">
                    <div class="chat-avatar">AI</div>
                    <div>
                        <div class="chat-sender-label">My Perfect Pup AI</div>
                        <div class="bubble">{safe_msg}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    input_col, send_col = st.columns([5, 1])
    with input_col:
        user_input = st.text_input("Message", key="chat_input", label_visibility="collapsed", placeholder="e.g. What's a good breed for a flat?")
    with send_col:
        send = st.button("Send", type="primary", use_container_width=True)

    if send and user_input.strip():
        if not OPENAI_API_KEY:
            st.error("OpenAI API key not found. Please add it to .streamlit/secrets.toml.")
        else:
            st.session_state.messages.append(("You", user_input.strip()))
            with st.spinner("Thinking..."):
                rag, err = load_rag_pipeline(OPENAI_API_KEY, use_scraped=True)
                if err:
                    reply = f"Sorry, I couldn't load the AI pipeline: {err}"
                else:
                    try:
                        reply = rag.answer_question(user_input.strip())
                    except Exception as e:
                        reply = f"Sorry, something went wrong: {e}"
            st.session_state.messages.append(("AI", reply))
            st.rerun()

    if st.session_state.messages:
        if st.button("Clear conversation", type="secondary"):
            st.session_state.messages = []
            st.rerun()


elif page == "Terminology":
    groups = [
        ("#eaf4ee", "#2f5d50", "Pastoral", "Pastoral group",
         "Herding dogs bred to work cattle, sheep and reindeer — usually with a weatherproof double coat. Includes the Collie family, Old English Sheepdogs and Samoyeds."),
        ("#fdf3ea", "#b05e1a", "Hound", "Hound group",
         "Breeds originally used for hunting by scent or sight. Scent hounds include the Beagle and Bloodhound; sight hounds the Whippet and Greyhound. Dignified, aloof but trustworthy companions that enjoy significant exercise."),
        ("#eaedf9", "#3a44a0", "Utility", "Utility group",
         "A miscellaneous group of mainly non-sporting breeds including the Bulldog, Dalmatian, Akita and Poodle. 'Utility' means fitness for a purpose — most were bred for a function outside sport or work."),
        ("#f0f9ea", "#3d7a1a", "Gundog", "Gundog group",
         "Dogs trained to find and/or retrieve game. Divided into Retrievers, Spaniels, Hunt/Point/Retrieve, Pointers and Setters. Renowned for their friendly temperament as all-round family dogs."),
        ("#faeaf9", "#8a3a98", "Toy", "Toy group",
         "Small companion or lap dogs, many bred specifically as companions. Friendly personalities, love attention, and require modest exercise."),
        ("#fdf6ea", "#9a6a10", "Terrier", "Terrier group",
         "Bred to hunt vermin above and below ground — 'Terrier' derives from the Latin Terra (earth). Hardy and brave, with a history tracing back to the Middle Ages."),
        ("#eaf4f9", "#1a6a8a", "Working", "Working group",
         "Guards and search-and-rescue dogs bred over centuries. Includes the Boxer, Great Dane and St. Bernard — some of the most heroic and specialised canines in the world."),
        ("#f5f5f5", "#555555", "Breed", "Dog breed",
         "A standardised type of dog with consistent, heritable traits, selectively bred over generations for appearance or function."),
    ]

    for bg, color, badge, title, desc in groups:
        st.markdown(f"""
        <div class="term-group" style="border-left: 3px solid {color};">
            <div class="term-group-badge" style="background:{bg};color:{color};">{badge}</div>
            <div>
                <h4>{title}</h4>
                <p>{desc}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
