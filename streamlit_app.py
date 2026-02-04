import streamlit as st

# Initialize session state for quiz visibility
if "show_quiz" not in st.session_state:
    st.session_state.show_quiz = False

st.set_page_config(page_title="Dog Breed Selector")

st.title("Dog Breed Selector")
st.write("Use the tools below to explore dog breeds and find a great match for you.")

# Two main columns: left = search by characteristics, right = quiz
left_col, right_col = st.columns(2)

# ---------------------------
# LEFT: Search by characteristics
# ---------------------------
with left_col:
    st.subheader("Search by Characteristics")

    st.write("Type the dog characteristics you're looking for:")

    characteristics = st.text_input(
        "Enter characteristics",
        placeholder="e.g., high energy, good with kids, low shedding...",
        help="Separate multiple traits with commas"
    )

    if st.button("Search breeds"):
        if characteristics:
            st.info(
                f"Searching for breeds matching: **{characteristics}** "
                "In the future, this will query your RAG pipeline."
            )
        else:
            st.warning("Please enter some characteristics first.")

# ---------------------------
# RIGHT: 10-question quiz 
# ---------------------------
with right_col:
    st.subheader("Find Your Best-Fit Breed")

    st.write("Click the button below to take a short quiz and get a breed suggestion.")

    if st.button("Take quiz", type="primary", use_container_width=True):
        st.session_state.show_quiz = True

    if st.session_state.show_quiz:
        st.write("Answer these 10 quick questions to get a recommended breed.")

        with st.form("breed_quiz"):
            q1 = st.radio("What kind of space do you live in?", ["Small House", "Large House", "Flat/Apartment", "Other"])
            q2 = st.radio("What size dog do you prefer?", ["Small", "Small-Medium", "Medium", "Large", "Extra Large", "No preference"])
            q3 = st.radio("How often do you want to groom your dog?", ["Daily", "Once a week", "More than once a week", "Less often than once a week"])
            q4 = st.radio("Do you mind shedding?", ["Yes", "No", "No preference"])
            q5 = st.radio("Do you have a preference for coat length?", ["Short", "Medium", "Long", "No preference"])
            q6 = st.radio("How much exercise can you give the dog daily?", ["30 minutes", "1 hour", "2 hours", "More than 2 hours"])
            q7 = st.radio("Do you or will you have other animals around the dog?", [
                "Yes I have dogs", 
                "Yes I have cats", 
                "Yes I have multiple animals (dogs, cats, etc.)", 
                "Yes I have other animals", 
                "No I do not have other animals"
            ])
            q8 = st.radio("Do you or will you have children around the dog?", ["Yes", "No", "Unsure"])
            q9 = st.radio("How much experience do you have with dogs?", [
                "None",
                "Very little",
                "Average amount",
                "A lot of experience",
                "I am very well informed on how to take care of dogs and what they need to thrive"
            ])
            q10 = st.radio("What type of dog are you looking for?", [
                "Toy", 
                "Hound", 
                "Working", 
                "Gundog", 
                "Pastoral", 
                "Utility", 
                "Unsure/No preference"
            ])
            q11 = st.radio("What age range are you looking for in a dog?", [
                "Less than 10 years", 
                "Over 10 years", 
                "Over 12 years", 
                "No preference"
            ])

            submitted = st.form_submit_button("Get my breed suggestion")

        # Placeholder "result" logic: purely front-end, no real model yet
        if submitted:
            st.success(
                "Thanks for completing the quiz!"
            )
            st.write("Example: You might be a great match for a **Golden Retriever** or **Labrador Retriever** based on your answers.")
