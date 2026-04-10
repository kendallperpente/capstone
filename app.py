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
.stApp {
    background-color: #f6faf7;
}

.card {
    background-color: white;
    padding: 25px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

h1, h2, h3 {
    color: #2f5d50;
}

.stButton > button {
    background-color: #4CAF7A;
    color: white;
    border-radius: 10px;
    padding: 8px 16px;
    border: none;
}

.stButton > button:hover {
    background-color: #3d9c65;
}

section[data-testid="stSidebar"] {
    background-color: #eaf4ee;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# HEADER
# ---------------------------
st.markdown("""
<div style="background-color:#2f5d50; padding:15px 25px; border-radius:10px; margin-bottom:20px;">
    <h2 style="color:white; margin:0;">Dog Breed Selector</h2>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# PAGES
# ---------------------------
pages = ["Home", "Match Me", "Chat", "Terminology"]

if "page" not in st.session_state:
    st.session_state.page = "Home"

# ---------------------------
# SIDEBAR
# ---------------------------
with st.sidebar:
    st.title("Menu")
    page = st.radio("Navigate", pages, index=pages.index(st.session_state.page))
    st.session_state.page = page

# ---------------------------
# HOME
# ---------------------------
if page == "Home":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Find Your Perfect Dog")

    st.write("""
    Use this app to:
    - Get matched with a dog breed based on your lifestyle  
    - Chat about dogs  
    - Learn dog terminology  
    """)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# MATCH ME (QUESTIONNAIRE)
# ---------------------------
elif page == "Match Me":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Lifestyle Questionnaire")

    # QUESTIONS
    space = st.selectbox("What kind of space do you live in?",
        ["Other", "Small House", "Large House", "Flat/Apartment"])

    size = st.selectbox("What size dog do you prefer?",
        ["No preference", "Small", "Small-Medium", "Medium", "Large", "Extra Large"])

    grooming = st.selectbox("How often do you want to groom your dog?",
        ["No preference", "Daily", "Once a week", "More than once a week", "Less often than once a week"])

    shedding = st.selectbox("Do you mind shedding?",
        ["No preference", "Yes", "No"])

    coat = st.selectbox("Do you mind coat length?",
        ["No preference", "Short", "Medium", "Long"])

    exercise = st.selectbox("How much exercise can you give daily?",
        ["No preference", "30 minutes", "1 hour", "2 hours", "More than 2 hours"])

    animals = st.selectbox("Do you have other animals?",
        ["No preference", "Yes I have dogs", "Yes I have cats",
         "Yes I have multiple animals", "Yes I have other animals",
         "No I do not have other animals"])

    children = st.selectbox("Will there be children around the dog?",
        ["No preference", "Yes", "No", "Unsure"])

    experience = st.selectbox("How much experience do you have with dogs?",
        ["No preference", "None", "Very little", "Average amount",
         "A lot of experience",
         "Very well informed"])

    dog_type = st.selectbox("What type of dog are you looking for?",
        ["No preference", "Toy", "Hound", "Working", "Gundog", "Pastoral", "Utility", "Unsure"])

    age = st.selectbox("What age range are you looking for?",
        ["No preference", "Less than 10 years", "Over 10 years", "Over 12 years"])

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # SUBMIT
    with col1:
        if st.button("Get Matches"):
            try:
                with st.spinner("Finding best matches..."):
                    response = requests.post(
                        "https://your-worker-url.workers.dev",
                        json={"filters": {
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
                        }}
                    )

                if response.status_code == 200:
                    data = response.json()

                    st.subheader("Best Matches")

                    if data:
                        for breed in data:
                            st.markdown(f"""
                            <div class="card">
                                <h3>{breed['name']}</h3>
                                <p><b>Size:</b> {breed['size']}</p>
                                <p><b>Energy:</b> {breed['energy']}</p>
                                <p><b>Grooming:</b> {breed['grooming']}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No matches found. Try adjusting your answers.")

                else:
                    st.error("Server error.")

            except Exception as e:
                st.error(f"Error: {e}")

    # RESET
    with col2:
        if st.button("Reset"):
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# CHAT
# ---------------------------
elif page == "Chat":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Chat with AI")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    user_input = st.text_input("Ask something about dogs:")

    if st.button("Send"):
        if user_input:
            st.session_state.messages.append(("You", user_input))
            st.session_state.messages.append(("AI", "AI coming soon!"))

    for sender, msg in st.session_state.messages:
        align = "right" if sender == "You" else "left"
        color = "#d1e7dd" if sender == "You" else "#f1f1f1"

        st.markdown(f"""
        <div style="text-align:{align}; margin:10px 0;">
            <div style="
                display:inline-block;
                background:{color};
                padding:10px 15px;
                border-radius:12px;
                max-width:70%;
            ">
                {msg}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# TERMINOLOGY
# ---------------------------
elif page == "Terminology":
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Dog Terminology")

    with st.expander("Dog Breed"):
        st.write("A standardized type of dog with consistent traits.")

    with st.expander("Pastoral Group"):
        st.write("The Pastoral Group consists of herding dogs that are associated with working cattle, sheep, reindeer and other cloven footed animals. Usually this type of dog has a weatherproof double coat to protect it from the elements when working in severe conditions. Breeds such as the Collie family, Old English Sheepdogs and Samoyeds who have been herding reindeer for centuries are but a few included in this group.")

    with st.expander("Hound Group"):
        st.write("Breeds originally used for hunting either by scent or by sight. The scent hounds include the Beagle and Bloodhound and the sight hounds such breeds as the Whippet and Greyhound. Many of them enjoy a significant amount of exercise and can be described as dignified, aloof but trustworthy companions.")

    with st.expander("Utility Group"):
        st.write("This group consists of miscellaneous breeds of dog mainly of a non-sporting origin, including the Bulldog, Dalmatian, Akita and Poodle. The name ‘Utility’ essentially means fitness for a purpose and this group consists of an extremely mixed and varied bunch, most breeds having been selectively bred to perform a specific function not included in the sporting and working categories. Some of the breeds listed in the group are the oldest documented breeds of dog in the world.")

    with st.expander("Gundog Group"):
        st.write("Dogs that were originally trained to find live game and/or to retrieve game that had been shot and wounded. This group is divided into four categories - Retrievers, Spaniels, Hunt/Point/Retrieve, Pointers and Setters - although many of the breeds are capable of doing the same work as the other sub-groups. They make good companions, their temperament making them ideal all-round family dogs.")

    with st.expander("Toy Group"):
        st.write("The Toy breeds are small companion or lap dogs. Many of the Toy breeds were bred for this capacity although some have been placed into this category simply due to their size. They should have friendly personalities and love attention. They do not need a large amount of exercise and some can be finicky eaters.")

    with st.expander("Terrier Group"):
        st.write("Dogs originally bred and used for hunting vermin. 'Terrier' comes from the Latin word Terra, meaning earth. This hardy collection of dogs were selectively bred to be extremely brave and tough, and to pursue fox, badger, rat and otter (to name but a few) above and below ground. Dogs of terrier type have been known here since ancient times, and as early as the Middle Ages, these game breeds were portrayed by writers and painters.")

    with st.expander("Working Group"):
        st.write("Over the centuries these dogs were selectively bred to become guards and search and rescue dogs. Arguably, the working group consists of some of the most heroic canines in the world, aiding humans in many walks of life, including the Boxer, Great Dane and St. Bernard. This group consists of the real specialists in their field who excel in their line of work.")

    st.markdown("</div>", unsafe_allow_html=True)
