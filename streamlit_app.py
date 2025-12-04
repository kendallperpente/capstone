# app.py - Dog Medical Chatbot

import os
import datetime
import urllib.parse
import streamlit as st
import openai

st.markdown(
    """
    <style>
    .stApp {
        background-color: #e6f5e9;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.set_page_config(page_title="Dog Medical Chatbot", page_icon="🐾")

st.title("🐶 Dog Medical Assistant (Non‑Emergency)")
st.caption(
    "Friendly, educational help for dog health questions. "
    "This does NOT replace a licensed veterinarian or emergency care."
)

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are a warm, friendly assistant specialized in dog (canine) health and basic first aid.
You are NOT a veterinarian and cannot diagnose or prescribe treatment.

Tone and style:
- Sound kind, calm, and supportive.
- Acknowledge that people care deeply about their dogs and may be worried.
- Use clear, non-technical language first, then optionally add brief clinical details.
- Keep answers concise but practical, with simple next steps when possible.

Behavior:
- Ask for important missing details (age, breed, weight, symptoms, duration, current meds).
- Emphasize that advice is educational only and does not replace a real vet.
- For anything serious (e.g. trouble breathing, seizures, inability to stand, severe pain,
  poisoning, eye injuries, uncontrolled bleeding, collapse), clearly say it might be an
  emergency and that they should contact an emergency vet or poison control immediately.
- Never give definitive diagnoses or guarantee outcomes.
- Never claim to replace professional veterinary care.
"""

def get_dog_medical_reply(messages):
    completion = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        temperature=0.3,
    )
    return completion["choices"][0]["message"]["content"]

if "dog_conversations" not in st.session_state:
    warm_greeting = (
        "Hi there! 🐶💚 Thanks for stopping by.\n\n"
        "I’m a friendly assistant focused on dog health and everyday care. "
        "You can tell me what's going on with your pup, and I'll help you think through "
        "possible causes, things to watch for, and questions you might want to ask a vet.\n\n"
        "**Important:** I'm not a veterinarian, so I can't give an official diagnosis or "
        "tell you exactly what treatment to use. If your dog seems very sick, is in a lot "
        "of pain, or you're worried it might be an emergency, please contact a veterinarian "
        "or an emergency clinic right away.\n\n"
        "When you're ready, tell me a bit about your dog (age, breed, weight) and what "
        "symptoms you're seeing, and we'll go through it together. 🐾"
    )
    st.session_state.dog_conversations = {
        "Dog 1": [{"role": "assistant", "content": warm_greeting}],
        "Dog 2": [{"role": "assistant", "content": warm_greeting}],
    }

with st.sidebar:
    current_dog = st.selectbox(
        "Which dog are we talking about?",
        ["Dog 1", "Dog 2"],
        help="Each dog has its own saved conversation history.",
    )

    st.markdown("---")
    st.header("⚠️ Safety Notice")
    st.write(
        "- This bot is for **educational purposes only**.\n"
        "- It does **not** provide diagnoses or prescriptions.\n"
        "- If your dog is vomiting repeatedly, has trouble breathing, collapses, has a seizure,\n"
        "  may have eaten something toxic, or seems in severe pain, contact an **emergency vet** immediately."
    )

    st.markdown("---")
    st.header("🏥 Find nearby vets")
    location_input = st.text_input(
        "Your city or postal code",
        placeholder="e.g. Brooklyn, NY or 94103",
    )
    
    search_type = st.radio(
        "What are you looking for?",
        ["General vets", "Emergency vets"],
        horizontal=False
    )
    
    if location_input:
        query = f"{'emergency ' if search_type == 'Emergency vets' else ''}veterinarian near {location_input}"
        encoded_query = urllib.parse.quote_plus(query)
        maps_url = f"https://www.google.com/maps/search/{encoded_query}"
        st.markdown(f"[🔍 Open in Maps]({maps_url})", unsafe_allow_html=True)

    st.markdown("---")
    conv = st.session_state.dog_conversations[current_dog]
    export_lines = [f"{'You:' if msg['role']=='user' else 'Assistant:'} {msg['content']}" for msg in conv]
    export_str = "\n\n".join(export_lines)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{current_dog.lower().replace(' ', '_')}_chat_{timestamp}.txt"
    st.download_button("Download", export_str, filename, "text/plain")

    if st.button("Clear this dog's conversation"):
        st.session_state.dog_conversations[current_dog] = [{"role": "assistant", "content": warm_greeting}]
        st.rerun()

messages = st.session_state.dog_conversations[current_dog]

for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input(f"What's going on with {current_dog}?")

if user_input:
    messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking about your dog's symptoms..."):
            reply = get_dog_medical_reply(messages)
        st.markdown(reply)

    messages.append({"role": "assistant", "content": reply})
    st.session_state.dog_conversations[current_dog] = messages
