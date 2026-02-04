# app.py - Dog Breed Recommender

import os
import datetime
import streamlit as st
import openai

#html/CSS styling 
st.markdown(
    """
    <style>
    .stApp {
        background-color: #000000;
        color: #f9fafb;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6, p, li, div, span {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #f9fafb;
    }

    /* Container width */
    .block-container {
        max-width: 820px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    /* Buttons - minimal */
    .stButton > button,
    .stDownloadButton > button {
        background: #0b0b0b;
        color: #f9fafb;
        border: 1px solid #1f2937;
        border-radius: 8px;
        padding: 0.45rem 0.9rem;
        box-shadow: none;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        border-color: #374151;
        background: #111111;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stChatInput > div > div > textarea {
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 0.6rem 0.75rem;
        background: #0b0b0b;
        color: #f9fafb;
    }

    .stTextInput > div > div > input:focus,
    .stChatInput > div > div > textarea:focus {
        border-color: #374151;
        box-shadow: none;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #0b0b0b;
        border-right: 1px solid #1f2937;
    }

    /* Chat message spacing */
    .stChatMessage {
        padding: 0.4rem 0;
    }

    /* Hide Streamlit footer */
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.set_page_config(page_title="Dog Breed Recommender")

st.title("Dog Breed Recommender")
st.caption("Minimal, chat-first breed matching. Share your lifestyle to get recommendations.")

# OpenAI client will be created in the function with API key

warm_greeting = (
    "Hi! I can help you find dog breeds that match your lifestyle.\n\n"
    "To get started, share details like your home size, activity level, "
    "experience with dogs, time for grooming/training, and whether you have kids "
    "or other pets. I’ll suggest a few breeds and explain why they fit."
)

SYSTEM_PROMPT = """
You are a warm, friendly assistant that recommends dog breeds based on a user's lifestyle
and preferences. You are not a veterinarian.

Tone and style:
- Sound friendly, practical, and encouraging.
- Keep answers concise and easy to scan.
- Prefer bullet points and short paragraphs.

Behavior:
- Ask for missing details (home size, activity level, grooming tolerance, experience,
  time for training, kids/other pets, allergies, and budget).
- Recommend 1 best-fit breed with brief reasons that map to the user's needs,
  then offer 2 alternatives.
- If unsure, suggest broader categories and ask follow-up questions.
- Encourage users to research and meet breeds before deciding.
"""

def get_breed_reply(messages, use_rag=False, use_scraped_data=False):
    try:
        if use_rag:
            # Use RAG pipeline for grounded answers
            from rag_module import get_rag_pipeline
            rag = get_rag_pipeline(use_scraped_data=use_scraped_data)
            user_question = messages[-1]["content"]  # Get the latest user message
            return rag.answer_question(user_question)
        else:
            # Use standard OpenAI API
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                temperature=0.3,
            )
            return completion.choices[0].message.content
    except Exception as e:
        return f"Sorry, I'm having trouble connecting to the AI service. Error: {str(e)}"

if "conversation" not in st.session_state:
    st.session_state.conversation = [{"role": "assistant", "content": warm_greeting}]

with st.sidebar:
    st.header("Settings")
    use_rag = st.checkbox(
        "Use Knowledge Base (RAG)",
        value=True,
        help="Uses a breed knowledge base for grounded suggestions. May be slower on first run."
    )

    if use_rag:
        use_scraped = st.checkbox(
            "Use Royal Kennel Club Breed Data",
            value=True,
            help="Uses data scraped from Royal Kennel Club. Run scrapper.py first to generate dog_breeds_rkc.json"
        )
        if not os.path.exists("dog_breeds_rkc.json"):
            st.warning("dog_breeds_rkc.json not found. Suggestions will use a small built-in dataset.")
    else:
        use_scraped = False

    st.markdown("---")
    conv = st.session_state.conversation
    export_lines = [f"{'You:' if msg['role']=='user' else 'Assistant:'} {msg['content']}" for msg in conv]
    export_str = "\n\n".join(export_lines)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"breed_chat_{timestamp}.txt"
    st.download_button("Download", export_str, filename, "text/plain")

    if st.button("Clear conversation"):
        st.session_state.conversation = [{"role": "assistant", "content": warm_greeting}]
        st.rerun()

messages = st.session_state.conversation

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Tell me about your lifestyle and what you want in a dog.")

if user_input:
    messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Finding good breed matches..."):
            reply = get_breed_reply(messages, use_rag=use_rag, use_scraped_data=use_scraped)
        st.markdown(reply)

    messages.append({"role": "assistant", "content": reply})
    st.session_state.conversation = messages
